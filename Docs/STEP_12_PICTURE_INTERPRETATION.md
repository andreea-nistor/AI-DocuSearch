# Step 12: Automatic Picture Interpretation (Multimodal, Page-Level)

## Overview

When `MULTIMODAL_ENABLED=true`, AI DocuSearch interprets pictures at **upload time**. Each PDF page
(or a standalone PNG/JPEG/WebP upload) is sent once to a vision-capable model, which returns a short
factual description of any meaningful picture, chart, diagram, screenshot, form, stamp, or
signature. The description is attached to the same physical page as the document text, so it is
chunked, indexed, and retrieved together with that text.

When a question is answered from a page that carries a picture description, the answer includes it
and the LLM is instructed to label it as an AI-generated interpretation, never as text printed in
the document.

**Status:** Implemented as a page-level slice, disabled by default. Region-level detection,
source previews, structured tables, visual embeddings, audio, and video remain future work; see
[MULTIMODAL_IMPLEMENTATION_PLAN.md](MULTIMODAL_IMPLEMENTATION_PLAN.md) and
[FUTURE_ADD_INS.md](FUTURE_ADD_INS.md).

---

## Data flow

```text
upload (PDF / PNG / JPEG / WebP)
  -> temporary file (src/upload_storage.py)
  -> extract_text()                       native text, OCR fallback, or "" for images
  -> describe_document_images()           one vision call per page / image
  -> attach_picture_descriptions()        [PICTURE_DESCRIPTION:<id>|AI_GENERATED] under [PDF_PAGE:n]
  -> build_pipeline_from_text()           existing chunking + embedding path
  -> answer_question()                    picture_description_used / picture_descriptions
  -> UI caption "This answer includes an AI-generated picture description."
```

Descriptions are generated **while the temporary upload still exists** and only once per document.
Questions never trigger new vision calls.

---

## Modules

### `src/visual_content.py`

| Symbol | Purpose |
|---|---|
| `PictureDescription` | Frozen dataclass: `region_id`, `description`, `page_number`, `source_kind`, `confidence`. Validates identifiers and ranges. |
| `attach_picture_descriptions(text, descriptions)` | Appends labeled blocks to the matching `[PDF_PAGE:n]` block; unpaged descriptions are appended at the end. Raises `ValueError` if a description references a page that is not in the text. |
| `extract_picture_descriptions(chunks)` | Returns unique `{region_id, description}` dicts found in retrieved chunks. |

Marker format inside a chunk:

```text
[PDF_PAGE:4]
Quarterly revenue grew by 12%.

[PICTURE_DESCRIPTION:p4-img1|AI_GENERATED]
Picture 1: A bar chart titled "Revenue by month" ...
```

### `src/visual_ingest.py`

| Symbol | Purpose |
|---|---|
| `multimodal_enabled()` | Reads `MULTIMODAL_ENABLED`. |
| `is_visual_source(path)` | `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`. |
| `load_validated_image(path)` | Opens a standalone image; rejects non-PNG/JPEG/WebP, animated images, and images above `MEDIA_MAX_IMAGE_PIXELS`; applies EXIF orientation. |
| `image_to_data_url(image)` | Downscales to `VISION_MAX_IMAGE_EDGE`, re-encodes as JPEG (drops metadata), returns a base64 data URL. |
| `describe_document_images(path, document_info)` | Renders PDF pages with `pdf2image` (up to `MEDIA_MAX_PAGES`, `VISION_RENDER_DPI`) or loads one image, calls the vision model per image, and returns a `VisualIngestResult`. **Never raises.** |
| `VisualIngestResult` | `descriptions`, `images_processed`, `images_skipped`, `pages_truncated`, `prompt_tokens`, `completion_tokens`, `elapsed_seconds`, `fallback_reason`. |

Pages with no meaningful picture are skipped when the model replies `NO_MEANINGFUL_PICTURE`.
Provider errors and missing configuration stop processing and set `fallback_reason`; any
descriptions already produced are kept.

### `src/ai_query.py`

`generate_answer_with_meta(prompt, model_name=None, temperature=None, images=None)`

- `images` is a list of data URLs. When present, the request body uses OpenAI-style content parts
  (`{"type": "text"}` followed by `{"type": "image_url"}` entries) and the model resolves to
  `VISION_MODEL` before `LLM_MODEL`.
- Without `images`, the payload is unchanged from previous releases.
- The return contract (`answer`, `response_status`, tokens, timing, `langsmith_run_id`) is the same.

### `src/ingest.py`

`extract_text()` routes `.png/.jpg/.jpeg/.webp` to `extract_text_from_image()`, which returns
Tesseract OCR text or `""`. Images are never decoded as UTF-8.

### `src/pipeline.py`

`answer_question()` adds two result fields:

```python
"picture_description_used": bool,
"picture_descriptions": [{"region_id": "p4-img1", "description": "..."}],
```

When descriptions are present in the selected chunks, the RAG context is prefixed with a
`[PICTURE_DESCRIPTION_NOTICE: ...]` block instructing the LLM to add a
**Picture description (AI-generated)** section and identify the region.

### `app_pages/home.py`

- The uploader accepts image types only when the feature is enabled.
- Vision prompt/completion tokens are charged through `track_query_cost()`.
- Warnings are shown for an incomplete interpretation (`fallback_reason`) or page truncation.
- The success banner reports the number of picture descriptions.
- Chat history entries store `picture_description_used` in `metrics` and render a disclosure caption.
- Direct LLM fallback results carry `picture_description_used=False` and `picture_descriptions=[]`.

### `prompts/picture_description_prompt.txt`

Ingestion-time prompt (`# temperature: 0.2`). Placeholders: `{document_info}`, `{page_label}`.
Requires chart type/axes/units/trend for charts, components/connections for diagrams, "appears to"
for uncertain content, the `NO_MEANINGFUL_PICTURE` sentinel for picture-less pages, and forbids
following instructions found inside the image.

---

## Configuration

```dotenv
MULTIMODAL_ENABLED=false        # master switch; default off
VISION_MODEL=                   # vision-capable model on LLM_API_BASE; falls back to LLM_MODEL
MEDIA_MAX_PAGES=25              # PDF pages rendered and interpreted per document
MEDIA_MAX_IMAGE_PIXELS=20000000 # decoded-pixel limit for standalone images
VISION_RENDER_DPI=110           # pdf2image render resolution
VISION_MAX_IMAGE_EDGE=1568      # longest edge sent to the provider
```

Poppler (`POPPLER_PATH` locally, `packages.txt` on Streamlit Cloud) is required for PDF rendering.
Set `VISION_MODEL` to a model that accepts `image_url` content on your provider (for example
`gpt-4o-mini` on OpenAI or `grok-2-vision` on xAI). Vision calls are billed against the session
budget like any other provider request.

---

## Privacy and safety

- Images are re-encoded as JPEG before transmission, which removes EXIF and other metadata.
- Pixel-count, page-count, and edge-length limits bound memory and provider cost.
- Animated and unsupported formats are rejected before any provider request.
- Raw image bytes and base64 payloads are never written to history, feedback, or LangSmith inputs
  (only `image_count` is traced).
- The temporary upload is deleted by `temporary_upload()` after extraction and interpretation.
- Picture descriptions are model output and are always marked `AI_GENERATED`; the answer prompt
  forbids presenting them as document text.
- Enabling the feature sends document page images to the configured LLM provider. Update the
  Privacy Policy and Third-Party Services disclosures before enabling it for external users.

---

## Tests

```powershell
python test_visual_ingest.py   # mocked provider; creates and removes small temp images
python test_ingest.py          # includes page-aware attachment test
python test_ai_query.py        # includes answer disclosure test
```

`test_visual_ingest.py` covers payload shape and model selection, one call per page, sentinel
skipping, provider error / simulated / render-failure fallbacks, image validation limits,
downscaling, and a standalone image flowing through to a disclosed answer.

---

## Limitations

- One description per PDF page; individual pictures are not cropped or given bounding boxes.
- No source-image preview in the UI; the original page image is not retained after upload.
- Standalone images without OCR-readable text rely entirely on the vision description.
- Quality depends on the configured vision model and the render DPI.
