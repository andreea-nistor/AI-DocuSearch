import base64
import io
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from .ai_query import generate_answer_with_meta
from .prompt_loader import load_prompt_with_temperature
from .visual_content import PictureDescription

NO_PICTURE_SENTINEL = "NO_MEANINGFUL_PICTURE"
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
_ALLOWED_PIL_FORMATS = {"PNG", "JPEG", "WEBP"}
DEFAULT_MAX_PAGES = 25
DEFAULT_MAX_IMAGE_PIXELS = 20_000_000
DEFAULT_RENDER_DPI = 110
DEFAULT_MAX_EDGE = 1568
_TRUE_VALUES = {"1", "true", "yes", "on"}


def multimodal_enabled() -> bool:
    return os.getenv("MULTIMODAL_ENABLED", "false").strip().lower() in _TRUE_VALUES


def is_visual_source(path: str) -> bool:
    return path.lower().endswith((".pdf",) + SUPPORTED_IMAGE_EXTENSIONS)


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, "") or default)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass
class VisualIngestResult:
    descriptions: list[PictureDescription] = field(default_factory=list)
    images_processed: int = 0
    images_skipped: int = 0
    pages_truncated: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    elapsed_seconds: float = 0.0
    fallback_reason: str | None = None


def load_validated_image(path: str, max_pixels: int | None = None) -> Any:
    """Open a standalone image, enforcing format, animation, and decoded-size limits."""
    from PIL import Image, ImageOps

    limit = max_pixels or _int_env("MEDIA_MAX_IMAGE_PIXELS", DEFAULT_MAX_IMAGE_PIXELS)
    with Image.open(path) as img:
        if img.format not in _ALLOWED_PIL_FORMATS:
            raise ValueError(f"Unsupported image format: {img.format or 'unknown'}")
        if getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1:
            raise ValueError("Animated images are not supported")
        if img.width * img.height > limit:
            raise ValueError(f"Image exceeds the {limit:,} pixel limit")
        # exif_transpose returns a copy, so the data survives closing the file.
        return ImageOps.exif_transpose(img).convert("RGB")


def image_to_data_url(image: Any, max_edge: int | None = None) -> str:
    """Downscale, re-encode as JPEG (drops metadata), and return a base64 data URL."""
    edge = max_edge or _int_env("VISION_MAX_IMAGE_EDGE", DEFAULT_MAX_EDGE)
    image = image.convert("RGB")
    image.thumbnail((edge, edge))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _render_pdf_pages(path: str, max_pages: int) -> tuple[list[tuple[int, Any]], bool]:
    from pdf2image import convert_from_path
    from pdf2image.pdfinfo import pdfinfo_from_path

    poppler_path = os.environ.get("POPPLER_PATH") or None
    info = pdfinfo_from_path(path, poppler_path=poppler_path)
    total_pages = int(info.get("Pages", 0) or 0)
    dpi = _int_env("VISION_RENDER_DPI", DEFAULT_RENDER_DPI)
    images = convert_from_path(
        path,
        dpi=dpi,
        first_page=1,
        last_page=min(total_pages, max_pages) if total_pages else max_pages,
        poppler_path=poppler_path,
    )
    pages = [(page_number, image) for page_number, image in enumerate(images, start=1)]
    return pages, total_pages > max_pages


def describe_document_images(path: str, document_info: str = "Unknown") -> VisualIngestResult:
    """Interpret each PDF page or standalone image once and return labeled descriptions.

    Never raises: rendering or provider problems are reported in `fallback_reason` so the
    text-only workflow can continue.
    """
    start = time.perf_counter()
    result = VisualIngestResult()
    max_pages = _int_env("MEDIA_MAX_PAGES", DEFAULT_MAX_PAGES)
    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == ".pdf":
            sources, result.pages_truncated = _render_pdf_pages(path, max_pages)
        elif ext in SUPPORTED_IMAGE_EXTENSIONS:
            sources = [(None, load_validated_image(path))]
        else:
            result.fallback_reason = f"Unsupported visual source: {ext or 'no extension'}"
            return result
    except Exception as exc:
        result.fallback_reason = f"Could not prepare images: {type(exc).__name__}: {exc}"
        result.elapsed_seconds = time.perf_counter() - start
        return result

    for page_number, image in sources:
        page_label = f"Physical PDF page {page_number}" if page_number else "Uploaded image"
        try:
            data_url = image_to_data_url(image)
        except Exception as exc:
            result.fallback_reason = f"Could not encode {page_label}: {type(exc).__name__}"
            break

        prompt, temperature = load_prompt_with_temperature(
            "picture_description_prompt",
            document_info=document_info,
            page_label=page_label,
        )
        meta = generate_answer_with_meta(prompt, temperature=temperature, images=[data_url])
        status = meta.get("response_status")
        if status == "simulated":
            result.fallback_reason = "Vision model is not configured; pictures were not interpreted."
            break
        if status != "success":
            result.fallback_reason = (
                f"Vision provider failed on {page_label}: "
                f"{meta.get('error_type') or 'error'}"
            )
            break

        result.images_processed += 1
        result.prompt_tokens += int(meta.get("prompt_tokens") or 0)
        result.completion_tokens += int(meta.get("completion_tokens") or 0)

        answer = (meta.get("answer") or "").strip()
        if not answer or answer.upper().startswith(NO_PICTURE_SENTINEL):
            result.images_skipped += 1
            continue

        region_id = f"p{page_number}-img1" if page_number else "img1"
        result.descriptions.append(
            PictureDescription(
                region_id=region_id,
                description=answer,
                page_number=page_number,
                source_kind="page" if page_number else "image",
            )
        )

    result.elapsed_seconds = time.perf_counter() - start
    print(
        f"[VISUAL_INGEST] processed={result.images_processed} described={len(result.descriptions)} "
        f"skipped={result.images_skipped} fallback={result.fallback_reason!r}",
        file=sys.stderr,
    )
    return result
