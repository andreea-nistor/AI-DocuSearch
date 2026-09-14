"""Tests for automatic picture interpretation at ingestion time."""

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from PIL import Image

from src.ai_query import generate_answer_with_meta
from src.ingest import extract_text
from src.pipeline import answer_question, build_pipeline_from_text
from src.visual_content import attach_picture_descriptions
from src.visual_ingest import (
    VisualIngestResult,
    describe_document_images,
    image_to_data_url,
    load_validated_image,
)

PROVIDER_CONFIG = {
    "LLM_API_KEY": "test-key",
    "LLM_API_BASE": "https://provider.invalid/v1",
    "LLM_MODEL": "text-model",
    "VISION_MODEL": "vision-model",
}


def _success_meta(answer: str, prompt_tokens: int = 100, completion_tokens: int = 20) -> dict[str, Any]:
    return {
        "answer": answer,
        "elapsed_seconds": 0.1,
        "response_status": "success",
        "error_type": None,
        "error_message": None,
        "used_live_api": True,
        "langsmith_run_id": None,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_tokens": False,
        "temperature": 0.2,
    }


def _status_meta(status: str, error_type: str | None) -> dict[str, Any]:
    meta = _success_meta("", 0, 0)
    meta.update({"response_status": status, "error_type": error_type, "used_live_api": False})
    return meta


def _blank_image(width: int = 40, height: int = 30) -> Image.Image:
    return Image.new("RGB", (width, height), "white")


def test_images_switch_payload_to_content_parts_and_vision_model() -> None:
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": "A chart."}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
    }

    with (
        patch.dict(os.environ, PROVIDER_CONFIG, clear=True),
        patch("src.ai_query._get_langsmith_client", return_value=None),
        patch("requests.post", return_value=response) as post,
    ):
        result = generate_answer_with_meta("Describe", images=["data:image/jpeg;base64,QUJD"])

    payload = post.call_args.kwargs["json"]
    content = payload["messages"][0]["content"]
    assert payload["model"] == "vision-model"
    assert content[0] == {"type": "text", "text": "Describe"}
    assert content[1] == {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,QUJD"}}
    assert result["response_status"] == "success"


def test_text_only_payload_is_unchanged_without_images() -> None:
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    with (
        patch.dict(os.environ, PROVIDER_CONFIG, clear=True),
        patch("src.ai_query._get_langsmith_client", return_value=None),
        patch("requests.post", return_value=response) as post,
    ):
        generate_answer_with_meta("Plain question")

    payload = post.call_args.kwargs["json"]
    assert payload["model"] == "text-model"
    assert payload["messages"][0]["content"] == "Plain question"


def test_pdf_pages_are_described_once_and_picture_less_pages_are_skipped() -> None:
    pages = [(1, _blank_image()), (2, _blank_image())]
    metas = [_success_meta("NO_MEANINGFUL_PICTURE"), _success_meta("Picture 1: a rising line chart.")]

    with (
        patch("src.visual_ingest._render_pdf_pages", return_value=(pages, False)),
        patch("src.visual_ingest.generate_answer_with_meta", side_effect=metas) as generate,
    ):
        result = describe_document_images("report.pdf", document_info="Document: report.pdf")

    assert generate.call_count == 2
    for call in generate.call_args_list:
        images = call.kwargs["images"]
        assert len(images) == 1 and images[0].startswith("data:image/jpeg;base64,")
    assert result.images_processed == 2
    assert result.images_skipped == 1
    assert result.prompt_tokens == 200 and result.completion_tokens == 40
    assert result.fallback_reason is None
    assert [d.region_id for d in result.descriptions] == ["p2-img1"]
    assert result.descriptions[0].page_number == 2
    assert result.descriptions[0].description == "Picture 1: a rising line chart."


def test_provider_error_keeps_partial_descriptions_and_stops() -> None:
    pages = [(1, _blank_image()), (2, _blank_image()), (3, _blank_image())]
    metas = [_success_meta("A diagram."), _status_meta("error", "Timeout")]

    with (
        patch("src.visual_ingest._render_pdf_pages", return_value=(pages, True)),
        patch("src.visual_ingest.generate_answer_with_meta", side_effect=metas) as generate,
    ):
        result = describe_document_images("report.pdf")

    assert generate.call_count == 2
    assert len(result.descriptions) == 1
    assert result.pages_truncated is True
    assert "Timeout" in (result.fallback_reason or "")


def test_missing_vision_configuration_is_reported_without_descriptions() -> None:
    pages = [(1, _blank_image()), (2, _blank_image())]

    with (
        patch("src.visual_ingest._render_pdf_pages", return_value=(pages, False)),
        patch(
            "src.visual_ingest.generate_answer_with_meta",
            return_value=_status_meta("simulated", "configuration_missing"),
        ) as generate,
    ):
        result = describe_document_images("report.pdf")

    assert generate.call_count == 1
    assert result.descriptions == []
    assert "not configured" in (result.fallback_reason or "")


def test_render_failure_returns_fallback_reason_without_raising() -> None:
    with patch("src.visual_ingest._render_pdf_pages", side_effect=RuntimeError("poppler missing")):
        result = describe_document_images("report.pdf")

    assert isinstance(result, VisualIngestResult)
    assert result.descriptions == []
    assert "poppler missing" in (result.fallback_reason or "")


def test_standalone_image_validation_limits() -> None:
    png_path = Path("temp_visual_test.png")
    gif_path = Path("temp_visual_test.gif")
    _blank_image(40, 30).save(png_path)
    _blank_image(40, 30).save(gif_path)
    try:
        image = load_validated_image(str(png_path))
        assert image.mode == "RGB" and image.size == (40, 30)

        try:
            load_validated_image(str(png_path), max_pixels=100)
            assert False, "Expected pixel-limit ValueError"
        except ValueError as exc:
            assert "pixel limit" in str(exc)

        try:
            load_validated_image(str(gif_path))
            assert False, "Expected unsupported-format ValueError"
        except ValueError as exc:
            assert "Unsupported image format" in str(exc)
    finally:
        png_path.unlink(missing_ok=True)
        gif_path.unlink(missing_ok=True)


def test_data_url_downscales_and_reencodes_as_jpeg() -> None:
    url = image_to_data_url(_blank_image(4000, 2000), max_edge=800)
    assert url.startswith("data:image/jpeg;base64,")
    assert len(url) < 50_000


def test_standalone_image_upload_is_described_and_never_read_as_text() -> None:
    png_path = Path("temp_visual_upload.png")
    _blank_image().save(png_path)
    try:
        with patch.dict(sys.modules, {"pytesseract": None}):
            text = extract_text(str(png_path))
        assert text == ""

        with patch(
            "src.visual_ingest.generate_answer_with_meta",
            return_value=_success_meta("A photo of a red car."),
        ):
            result = describe_document_images(str(png_path))
    finally:
        png_path.unlink(missing_ok=True)

    assert [d.region_id for d in result.descriptions] == ["img1"]
    assert result.descriptions[0].page_number is None

    document_text = attach_picture_descriptions(text, result.descriptions)
    pipeline = build_pipeline_from_text(document_text, use_embeddings=False)
    with patch("src.pipeline.generate_answer_with_meta", return_value=_success_meta("A red car.")) as generate:
        answer = answer_question(pipeline, "What is in the picture?")

    assert "[PICTURE_DESCRIPTION:img1|AI_GENERATED]" in generate.call_args.args[0]
    assert answer["picture_description_used"] is True
    assert answer["picture_descriptions"][0]["description"] == "A photo of a red car."


if __name__ == "__main__":
    test_images_switch_payload_to_content_parts_and_vision_model()
    test_text_only_payload_is_unchanged_without_images()
    test_pdf_pages_are_described_once_and_picture_less_pages_are_skipped()
    test_provider_error_keeps_partial_descriptions_and_stops()
    test_missing_vision_configuration_is_reported_without_descriptions()
    test_render_failure_returns_fallback_reason_without_raising()
    test_standalone_image_validation_limits()
    test_data_url_downscales_and_reencodes_as_jpeg()
    test_standalone_image_upload_is_described_and_never_read_as_text()
    print("All visual ingest tests passed.")
