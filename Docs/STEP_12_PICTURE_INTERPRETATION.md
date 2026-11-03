# Step 12: Automatic Picture Interpretation (Multimodal, Page-Level)

**Status:** Implemented as a page-level slice and disabled by default (`MULTIMODAL_ENABLED=false`).
Region-level detection, source previews, structured tables, visual embeddings, audio, and video
remain future work; see [STEP_13_MULTIMODAL_IMPLEMENTATION_PLAN.md](STEP_13_MULTIMODAL_IMPLEMENTATION_PLAN.md).

## Goal

Text extraction alone misses information that lives in charts, diagrams, screenshots, forms, stamps,
and signatures. This step adds an optional upload-time pass that asks a vision-capable model for a
short, factual description of each meaningful picture and stores that description alongside the
document text, so the existing chunking, embedding, and retrieval flow can find it.

## Design decisions

- **Page-level granularity.** Each physical PDF page (or each standalone image) is one unit and gets
  at most one description. Individual pictures are not cropped or given bounding boxes.
- **Ingestion-time, once per document.** Vision calls happen while the temporary upload still exists.
  Questions never trigger new vision calls, which keeps per-question cost and latency unchanged.
- **Descriptions are attached as text.** A description is appended to the matching `[PDF_PAGE:n]`
  block with a `[PICTURE_DESCRIPTION:<id>|AI_GENERATED]` marker. Chunking, embedding, and keyword
  retrieval then treat it like any other page text, and the page marker keeps it associated with the
  correct physical page.
- **Always labeled as AI-generated.** Answers that use a description are told to disclose it and
  must not present it as text printed in the document.
- **Never a hard failure.** Rendering, provider, and configuration problems are reported as a
  fallback reason. The text-only workflow continues with whatever was produced.
- **Opt-in.** The feature is off unless explicitly enabled, because it sends page images to the
  configured LLM provider.

## How the flow works

1. The user uploads a PDF, or a PNG, JPEG, or WebP image when the feature is enabled. The uploader
   only offers image types when `MULTIMODAL_ENABLED` is true.
2. The file is written to a temporary upload file in [src/upload_storage.py](../src/upload_storage.py).
   The file is removed when the context manager exits, whether or not processing succeeds.
3. `extract_text()` in [src/ingest.py](../src/ingest.py) runs as usual. Searchable PDFs use their text
   layer, scanned PDFs fall back to OCR, and images return Tesseract OCR text or an empty string when
   OCR is unavailable. Images are never decoded as UTF-8.
4. For PDFs, the page count is read first and at most `MEDIA_MAX_PAGES` pages are selected. The
   document is marked as truncated when it has more pages than that.
5. `describe_document_images()` in [src/visual_ingest.py](../src/visual_ingest.py) processes one page
   or image at a time. Each PDF page is rendered with `pdf2image` at `VISION_RENDER_DPI`, converted to
   RGB, downscaled to `VISION_MAX_IMAGE_EDGE`, and re-encoded as JPEG. The decoded bitmap is released
   before the provider call, so only the encoded image is held. Standalone images are validated first.
6. Each image is sent once to the vision model through `generate_answer_with_meta()` in
   [src/ai_query.py](../src/ai_query.py), using the prompt in
   [prompts/picture_description_prompt.txt](../prompts/picture_description_prompt.txt) at temperature 0.2.
7. Replies equal to, or starting with, `NO_MEANINGFUL_PICTURE` are skipped. Other replies become
   `PictureDescription` objects. Model output first has any literal `[PDF_PAGE:n]` or
   `[PICTURE_DESCRIPTION:...]` markers neutralized, so the model cannot forge structure.
8. `attach_picture_descriptions()` in [src/visual_content.py](../src/visual_content.py) inserts each
   description under its page marker. Descriptions for pages that are not in the text raise an error,
   and the Streamlit app catches it and logs it without failing the upload.
9. The combined text goes through the normal pipeline in [src/pipeline.py](../src/pipeline.py)
   (`build_pipeline_from_text()`), so chunking and indexing stay unchanged.
10. At question time, `answer_question()` extracts the descriptions present in the selected chunks.
    When any are present, the context is prefixed with a notice telling the LLM to add a
    "Picture description (AI-generated)" section and identify the region. The result reports
    `picture_description_used` and `picture_descriptions`.
11. The Streamlit app in [app_pages/home.py](../app_pages/home.py) charges vision tokens to the session
    budget, shows warnings for incomplete interpretation or page truncation, reports the number of
    descriptions in the success message, and adds a caption to answers that used a description.

## Components

- **[src/visual_content.py](../src/visual_content.py):** the `PictureDescription` data type, which
  validates region IDs, page numbers, and confidence; marker patterns; marker neutralization;
  attachment of descriptions to pages; and extraction of descriptions from retrieved chunks.
- **[src/visual_ingest.py](../src/visual_ingest.py):** environment parsing, image validation and
  normalization, PDF page rendering, the per-page vision loop, and the `VisualIngestResult` summary
  (counts, token usage, timing, and fallback reason).
- **[src/ai_query.py](../src/ai_query.py):** accepts image data URLs, sends them as content parts, and
  selects `VISION_MODEL` when images are present. Text-only requests are unchanged.
- **[src/ingest.py](../src/ingest.py):** routes image uploads to OCR and never reads them as text.
- **[src/pipeline.py](../src/pipeline.py):** detects description markers in selected chunks and adds the
  disclosure notice and result fields.
- **[prompts/picture_description_prompt.txt](../prompts/picture_description_prompt.txt):** asks for chart
  type, axes, units, legend, trend, and approximate values for charts; components and connections for
  diagrams; "appears to" for uncertain content; and the `NO_MEANINGFUL_PICTURE` sentinel for pages
  without pictures. It also tells the model not to follow instructions found inside images.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MULTIMODAL_ENABLED` | `false` | Master switch for uploads and picture interpretation. |
| `VISION_MODEL` | empty | Vision-capable model on `LLM_API_BASE`. Falls back to `LLM_MODEL` when empty. |
| `MEDIA_MAX_PAGES` | `25` | Maximum PDF pages rendered and interpreted per document. |
| `MEDIA_MAX_IMAGE_PIXELS` | `20000000` | Maximum decoded pixel count for standalone images. |
| `VISION_RENDER_DPI` | `110` | Resolution used when rendering PDF pages. |
| `VISION_MAX_IMAGE_EDGE` | `1568` | Longest edge, in pixels, of an image sent to the provider. |

Invalid or non-positive numeric values fall back to these defaults. PDF rendering needs Poppler:
set `POPPLER_PATH` locally, while Streamlit Cloud installs `poppler-utils` from `packages.txt`.
Choose a model that accepts `image_url` content on your provider; `.env.example` lists the same
variables. Vision calls are billed like other provider requests.

## Error handling and fallbacks

`describe_document_images()` never raises. Each failure is recorded in `fallback_reason`:

- **Cannot prepare the document** (for example, Poppler is missing or the PDF cannot be read): no
  descriptions, and the text-only workflow continues.
- **Page or image cannot be rendered, validated, or encoded:** processing stops at that point, and
  descriptions produced earlier are kept.
- **Vision model not configured:** the provider returns a simulated status. Processing stops and the
  reason says pictures were not interpreted.
- **Provider error or timeout:** processing stops, and the reason names the error type. Earlier
  descriptions are kept.
- **Prompt template cannot be loaded:** processing stops with the exception type as the reason.
- **Unsupported standalone format, animated image, or image over the pixel limit:** the image is
  rejected before any provider request.

Pages where the model finds nothing meaningful are counted as skipped, not as failures. In the app,
an incomplete interpretation shows a warning with the reason, and a truncated PDF shows a warning
with the number of pages that were interpreted.

## Privacy and safety

- Images are re-encoded as JPEG before transmission, which drops EXIF and other metadata.
- Pixel, page-count, and edge-length limits bound memory use and provider cost.
- Model replies are treated as untrusted content. Forged markers are neutralized, and the system
  message tells the answering model that document content, picture descriptions, and images are data,
  not instructions.
- Raw image bytes and base64 payloads are not sent to LangSmith. The trace records only the number of
  images (`image_count`).
- The temporary upload is removed after extraction and interpretation.
- Enabling the feature sends page images to the configured LLM provider. Update the
  [privacy policy](../Policies/PRIVACY_POLICY.md) and
  [third-party services](../Policies/THIRD_PARTY_SERVICES.md) disclosures before enabling it for
  external users.

## Tests

Run these from the repository root:

- `python -m test_src.test_visual_ingest` covers the vision request payload and model selection, one
  call per page, skipping of picture-less pages, provider, configuration, and render fallbacks,
  image validation limits, downscaling, one-page-at-a-time processing, and a standalone image flowing
  through to a disclosed answer. It uses a mocked provider and writes small temporary images to the
  working directory, then removes them.
- `python -m test_src.test_ingest` includes tests that attach descriptions to their PDF page and that
  forged markers in uploaded text or DOCX content are neutralized.
- `python -m test_src.test_ai_query` includes a test that answers disclose the selected
  AI-generated description.

## Limitations

- One description per PDF page. Individual pictures on a page are not separated.
- Only the first `MEDIA_MAX_PAGES` pages of a PDF are interpreted.
- The original page image is not kept after upload, so the UI cannot show a source preview.
- Standalone images with no OCR-readable text depend entirely on the model's description.
- Description quality depends on the configured vision model and the render resolution.
- Vision calls are not tested against a live provider in the automated suite.

## Related

- [STEP_1_INGEST.md](STEP_1_INGEST.md): text extraction, OCR fallback, and image routing.
- [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md): page-aware chunking that keeps description blocks with their page.
- [STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md): indexing of the enriched document text.
- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md): the chat-completions client that gains image content parts.
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): retrieval, the answer result contract, and the disclosure notice.
- [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md): `packages.txt` and Poppler on Streamlit Cloud.
- [STEP_10_COST_TRACKING.md](STEP_10_COST_TRACKING.md): how vision tokens count against the session budget.
- [STEP_11_GDPR_COMPLIANCE.md](STEP_11_GDPR_COMPLIANCE.md): privacy disclosures that cover sending page images to a provider.
- [STEP_13_MULTIMODAL_IMPLEMENTATION_PLAN.md](STEP_13_MULTIMODAL_IMPLEMENTATION_PLAN.md): planned future work.
- [FUTURE_ADD_INS.md](FUTURE_ADD_INS.md): other planned extensions.
