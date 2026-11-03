# Step 13: Multimodal Document Intelligence (Plan)

**Status:** Planned. Phase 0 is partly done, and Phase 4 is partly implemented as a page-level slice
([Step 12](STEP_12_PICTURE_INTERPRETATION.md)). All other phases have not started.

## Goal

Extend the text-only Hybrid workflow so answers can use document tables, pictures, diagrams, charts,
forms, and layout, with every claim traceable to a page, region, or table cell. Audio and video come
later, once document-image retrieval is stable and measurable.

## Design principles

- **Keep text as a supported path.** Text extraction and text retrieval stay in place. They are not
  treated as legacy code to remove.
- **Add structure first.** Introduce typed document data (pages, regions, tables, citations) before
  adding model-specific behavior.
- **Keep source location.** Every transformation preserves the document, physical page, region, table
  cell, and, later, media timestamp.
- **Separate extraction, retrieval, and generation.** Each provider can be replaced independently.
- **Send the minimum private media.** Only the pages or pictures a question needs go to external
  providers.
- **Ship one vertical slice at a time, behind configuration.** Each slice has measurable exit criteria.
- **Decide with benchmarks.** A new model is adopted only when it improves quality enough to justify
  its latency, memory, licence, and cost.

## Implementation status

| Phase | Topic | Status | Notes |
|---|---|---|---|
| 0 | Baseline, fixtures, feature flags | Partial | Feature flags and vision settings exist. No fixture manifest or baseline evaluation yet. |
| 1 | Structured document model | Not started | No `src/document_model.py`. |
| 2 | Session-scoped derived media | Not started | Page renders are discarded after ingestion. |
| 3 | Layout-aware tables | Not started | DOCX and PDF tables are still flattened to text. |
| 4 | Automatic picture and page interpretation | Partial | Page-level descriptions for PDF pages and standalone images. No region detection. |
| 5 | Visual regions and cross-modal retrieval | Not started | No visual embeddings or bounding boxes. |
| 6 | Source preview and verification UI | Not started | No citation controls or previews. |
| 7 | Multi-document and advanced analysis | Not started | Candidate increments only. |
| 8 | Audio | Not started | Depends on Phases 2 and 6. |
| 9 | Video | Not started | Depends on Phase 8. |

## Current baseline

The text-only data path is:

upload, then a temporary file, then text extraction, then chunks, then MiniLM embeddings or keyword
search, then the text prompt, then the chat completion.

Several constraints shape the plan:

- Text extraction returns plain text only. OCR page images are discarded after conversion.
- Chunking and the embedding index accept strings only.
- The answer client sends text, or text plus images when vision is used.
- The uploaded temporary file is deleted after extraction. The app keeps only text and the built
  pipeline in session state.
- History and feedback depend on the current result shape.

## Architecture

### Implemented modules (Step 12)

- `visual_content` holds the picture-description data type, the AI-generated markers, and the
  attachment of descriptions to pages.
- `visual_ingest` renders PDF pages, validates standalone images, and runs one vision call per page or
  image. It never raises.
- `ai_query` accepts optional image inputs and switches to the vision model when they are present.
- `pipeline` adds the picture-description result fields and the disclosure notice.
- A dedicated prompt file guides the ingestion-time description.
- The Streamlit home page handles image uploads when enabled, tracks vision cost, and shows a
  disclosure caption.

### Planned modules

- `document_model` for typed artifact, region, table, and citation contracts.
- `media_storage` for session workspaces, opaque media references, cleanup, and resource limits.
- `table_extraction` for DOCX, native PDF, and scanned table normalization.
- `multimodal_index` for visual embeddings and visual search.
- `retrieval` for result normalization, score fusion, deduplication, and reranking.

Extraction, image encoding, score fusion, and provider payload construction stay out of the pipeline.
The pipeline coordinates these components and keeps the result contract.

## Planned data model

The model uses standard-library data classes, so no database or model framework is needed for the
first migration.

- A **document artifact** holds the document ID, file name, media type, a list of pages, and any
  regions that are not tied to a page.
- A **page** holds its physical page number, text, regions, and an optional page image reference.
- A **region** holds an ID, page number, kind (text, table, picture, chart, formula, or form), text,
  optional normalized bounding box, optional media reference, extraction method, confidence, and
  metadata.

For visual regions, the text is a generated, searchable description. Its metadata records that it is
model-generated, along with the provider, model, time, prompt version, and whether the source was a
full page or an extracted picture. Generated descriptions are supporting evidence and are never shown
as native document text.

A compatibility adapter converts an artifact back to the current page-marked text. This lets structured
ingestion land before chunking, the index, or the answer pipeline change.

### Evidence citations

Every retrieved item uses one citation shape: a citation ID (for example, document, page, and region),
document ID, page number, region ID, kind, bounding box, media reference, extraction method, and
confidence. Coordinates are normalized to the range 0 to 1, so previews do not depend on the rendered
resolution.

## Phases

### Phase 0: Baseline, fixtures, and feature flags

**Goal:** make quality and compatibility measurable before structural changes.

- Build a small, redistributable fixture set: searchable PDF pages, scanned pages, DOCX tables, a
  multi-page table, a chart, a diagram, rotated content, and an unreadable region.
- Record the expected pages, regions, table values, and answers in a machine-readable manifest.
- Add the remaining feature flags, all disabled by default.
- Capture baseline extraction, retrieval, latency, and memory results in a repeatable script.
- Add a regression test that checks all required existing result fields.

**Exit criteria:** existing tests pass with every new flag off, fixtures have clear expected outputs and
usable licences, and baseline measurements are stored in a repeatable script.

### Phase 1: Structured document model and compatibility adapter

**Goal:** keep layout and source identity without changing user-visible answers.

- Add the typed contracts and validation helpers.
- Add a structured extraction function beside the current text extraction.
- Represent every physical PDF page, including empty pages.
- Convert the artifact back to page-marked text and compare it with the current output.
- Create stable region and citation IDs that contain no private text.
- Leave the pipeline builder unchanged in this phase.

**Exit criteria:** existing ingestion and page-request tests pass, page markers are unchanged, native text
does not drift after a round trip, and empty, malformed, and unsupported files behave as they do today.

### Phase 2: Session-scoped derived media

**Goal:** keep page renders and crops safely after the original upload is deleted.

- Create a random session workspace under an app-owned temporary root.
- Give the rest of the application opaque media references, never file paths.
- Enforce limits on extension, file signature, byte size, pixel count, page count, and output files.
- Delete the previous workspace when a new upload replaces it.
- Clean up stale workspaces at startup, touching only application-owned folders.
- Keep raw media and paths out of history, feedback, and tracing.

**Exit criteria:** derived files last for the active session, replacing an upload removes the old media,
partial artifacts are removed after a failure, and tests cover path traversal, malformed images, and
resource limits.

### Phase 3: Layout-aware tables

**Goal:** treat tables as structured, citable evidence before adding vision generation.

- Keep DOCX rows, columns, merged cells, and surrounding titles instead of joining cell text.
- Evaluate a permissively licensed native PDF table extractor against the fixtures.
- Use OCR table extraction only when native extraction is unavailable.
- Store each table with headers, rows, cells, spans, units, footnotes, page, and bounding box.
- Render the selected table as compact Markdown for the existing text model.
- Add deterministic operations (sum, difference, percentage, minimum, maximum, filter). Document-provided
  code is never executed.
- Retrieve at row or table-section level, keeping headers and footnotes.

**Exit criteria:** cell accuracy meets the Phase 0 target, multi-page headers and continuation rows are
kept, arithmetic answers match expected values, ambiguous cells are flagged rather than silently
normalized, and text-only providers can answer table questions without images.

### Phase 4: Automatic picture and page interpretation

**Goal:** describe meaningful pictures at ingestion, then use those descriptions when answering questions
about the same page. Users can also ask a vision model about a whole PDF page or a standalone image.

Supported sources:

- Complete rendered PDF pages, including scanned pages (implemented).
- Pictures embedded in PDF and DOCX files, with location when known (planned).
- Standalone PNG, JPEG, and WebP uploads (implemented).
- TIFF, BMP, GIF, and HEIC/HEIF are deferred until decoder, animation, orientation, and resource tests exist.

Implemented in Step 12:

- Each PDF page is rendered, one at a time, and sent to the vision model once. The description is stored
  as an AI-generated block under the page marker.
- Standalone images are validated first, covering orientation, decoded pixel limits, animation
  rejection, and metadata stripping on re-encode.
- Descriptions are indexed as ordinary page text, so a page can match on its visual content.
- When a selected page has a description, the answer is told to add a labeled section and to keep
  generated content separate from printed text.
- Any failure falls back to the extracted text and is reported as a reason.

Still planned in this phase:

- Detect meaningful pictures as regions, ignoring logos, icons, separators, and backgrounds.
- Extract embedded pictures from PDF and DOCX files and keep nearby captions with them.
- Store each description as a region with a bounding box, media reference, caption, and provenance.
- Add a provider-neutral message-part contract for text and images.
- Send only the requested pictures, according to each provider's capabilities.
- Add a separate multimodal answer prompt that requires page and region citations.
- Track images sent, encoded bytes, and vision time. Images are never logged.
- Return a clear message for a standalone image with no OCR text and no usable description.
- Show visual citations separately from native text citations.

**Answer rules:** descriptions are labeled "Picture description (AI-generated)". They use observational
wording such as "the image appears to show". Unreadable or ambiguous content is stated as such. A
description is never quoted as if it were printed in the document. When a page has several pictures,
only those relevant to the question are included, up to a limit.

**Exit criteria:** a question such as "describe the chart on page 4" sends only page 4 and its text; an
embedded picture is cited by document and location; each picture is interpreted once at ingestion, not
per question; repeated logos do not produce noisy descriptions; unsupported, animated, oversized, and
malformed images are rejected before any request; provider errors keep their current semantics; and
text-only configuration still passes the existing tests.

### Phase 5: Visual regions and cross-modal retrieval

**Goal:** find visual evidence when the user gives no page number.

- Detect picture, chart, diagram, formula, and form regions with bounding boxes.
- Reuse the ingestion-time descriptions and keep their captions and nearby paragraphs.
- Allow a deeper question-time look at an image only when its description is not enough and the source
  is still available.
- Compare a CLIP-style baseline with a document-focused visual retriever.
- Put visual search behind a common retriever interface.
- Normalize text, table, and visual scores before fusion. Raw scores are never compared directly.
- Deduplicate page and region results, and enforce image and context budgets.
- Rerank a small candidate set only where measured quality justifies the extra latency.

**Exit criteria:** recall meets the Phase 0 target on unseen questions, answers cite the region and page,
captions stay with their images, irrelevant images are not sent just because they share a page, and a
missing visual dependency falls back to text retrieval with a recorded reason.

### Phase 6: Source preview and verification UI

**Goal:** let users check the exact evidence behind an answer.

- Add compact citation controls below answers.
- Show the page thumbnail with the cited region highlighted.
- Show table evidence with the cited cells emphasized.
- Label each source as native text, OCR, table extraction, or visual interpretation.
- Show low-confidence warnings without exposing internal details.
- Make sure media references cannot open another session's content.
- Test desktop and mobile layouts with long answers, wide tables, and several citations.

**Exit criteria:** every multimodal claim traces to visible evidence, controls do not shift the chat layout,
citations are keyboard accessible, and expired media shows a clear unavailable state.

### Phase 7: Multi-document and advanced analysis

**Status:** candidate increments only. Each needs its own fixtures and acceptance target.

- Compare clauses, tables, figures, and revisions across documents.
- Extract forms, checkboxes, signatures, handwriting, formulas, and key-value fields.
- Let users correct OCR text and table cells, with targeted re-indexing.
- Detect and redact sensitive regions before any external vision call.
- Export grounded reports that include citation metadata.

### Phase 8: Audio

**Prerequisites:** a stable media lifecycle, evidence citations, a provider abstraction, and cost limits.

- Ingest audio with a duration limit and safe media probing.
- Transcribe with timestamps, detected language, and optional speaker labels.
- Store transcript segments as regions with start and end times, and search them through the text index.
- Add time-range playback in the UI.
- Treat voice data as sensitive. Speaker identification is off by default.

**Exit criteria:** answers cite exact time ranges, unsupported codecs, long files, and transcription failures
degrade cleanly, and temporary audio follows the same cleanup policy as document images.

### Phase 9: Video

**Prerequisites:** Phase 8 complete and explicit operational limits approved.

- Extract audio, scene boundaries, keyframes, and visible text.
- Place transcript intervals, scenes, and keyframes on one timeline.
- Retrieve transcript and visual evidence without processing every frame.
- Add timestamped citations and playback.
- Enforce strict limits on duration, resolution, frame count, disk, memory, and provider cost.

**Exit criteria:** answers cite a scene or time range, processing stays within budget, and a partial failure
(for example, missing audio) still lets the other modalities be queried.

## Retrieval and generation policy

1. Honor explicit page requests before semantic retrieval.
2. Retrieve text, table, and picture-description candidates.
3. For each selected answer page, add its meaningful descriptions as companion evidence, ranked by
   relevance to the question.
4. Retrieve visual-embedding candidates only when that feature is enabled and the question is likely to
   need them.
5. Normalize scores per retriever.
6. Deduplicate parent pages and child regions.
7. Select evidence within text, description, image-count, byte, and provider limits.
8. Generate from evidence labeled as native text, OCR, structured table, or AI-generated description.
9. Add the labeled picture-description section whenever that evidence contributes to the answer.
10. Return citations, modalities used, confidence signals, and fallback reasons.

The model must not claim it inspected an image when it only received OCR text or a generated description.

## Result contract

New fields are added with neutral defaults and no existing field is renamed or removed:

- Modalities used, including text by default.
- Picture-description usage and the description list (implemented).
- Evidence citations, visual sources, and table sources.
- Images sent and media bytes sent.
- Multimodal retrieval and vision generation times.
- A media fallback reason.

Compact citations may be stored in history, but raw media and encoded payloads never are. Cost is
counted only for successful responses. The direct-LLM fallback returns the same fields with neutral
values. `picture_description_used` is true only when at least one generated description is part of the
answer context.

## Configuration

### Implemented (Step 12)

| Variable | Default | Purpose |
|---|---|---|
| `MULTIMODAL_ENABLED` | `false` | Master switch for image uploads and picture interpretation. |
| `VISION_MODEL` | empty | Vision-capable model on `LLM_API_BASE`. Uses `LLM_MODEL` when empty. |
| `MEDIA_MAX_PAGES` | `25` | Maximum PDF pages rendered and interpreted per document. |
| `MEDIA_MAX_IMAGE_PIXELS` | `20000000` | Decoded pixel limit for standalone images. |
| `VISION_RENDER_DPI` | `110` | Resolution used for PDF page renders. |
| `VISION_MAX_IMAGE_EDGE` | `1568` | Longest edge of an image sent to the provider. |

### Planned

- `DOCUMENT_LAYOUT_ENABLED`, `TABLE_EXTRACTION_ENABLED`, `VISION_GENERATION_ENABLED`,
  `VISUAL_INDEX_ENABLED`, and `MEDIA_MAX_IMAGES_PER_QUERY`.

Each planned flag is added with its phase, and every new variable is documented in `.env.example`.

## Dependencies

No dependency is adopted without a written evaluation. Each candidate is checked for licence, Python and
Streamlit Cloud compatibility, download size, peak memory, CPU needs, cold-start time, binary or model
downloads, offline behavior, failure modes, and supported languages and formats.

| Capability | Baseline | Main criteria |
|---|---|---|
| PDF rendering | `pdf2image` (existing) | Page fidelity, Poppler availability, memory, speed |
| OCR regions | Tesseract (existing) | Languages, coordinates, confidence, rotated text |
| DOCX tables | `python-docx` (existing) | Merged cells, nested tables, order |
| Native PDF tables | Candidate (`pdfplumber`) | Licence, ruled and unruled tables, accuracy |
| Visual embeddings | CLIP-style sentence model | Cross-modal recall, memory, model size, licence |
| Vision generation | Provider-neutral client (existing) | Payload compatibility, grounding, privacy, cost |
| Audio transcription | Provider or local Whisper-style adapter | Accuracy, timestamps, memory, licence |
| Video probing | FFmpeg / ffprobe (candidate) | Deployment availability, sandboxing, limits |

## Tests

### Current

- `python -m test_src.test_visual_ingest` uses a mocked provider and creates and removes small temporary
  images. It covers payloads, model selection, one call per page, skipping of picture-less pages,
  fallbacks, image validation, downscaling, and disclosed answers.
- `python -m test_src.test_ingest` includes page-aware attachment and marker neutralization tests.
- `python -m test_src.test_ai_query` includes the answer disclosure test.

### Planned strategy

- **Unit:** data-model validation, artifact-to-text compatibility, region and citation IDs, session media
  lifecycle, table normalization, text and image message payloads, score fusion and budgets, and
  result-contract defaults on every path.
- **Integration:** searchable, scanned, and DOCX-table documents; charts and mixed content; explicit page
  image questions; text questions that hit a page with a picture; description failure keeping the text
  answer; deterministic table calculations; provider timeouts and malformed responses; upload
  replacement and expired media.
- **UI:** disabled-feature behavior unchanged, citation previews, wide and multi-page tables on desktop and
  mobile, and failed provider results neither saved, rated, nor charged.
- **Metrics:** retrieval recall at k for text and visual sources, table cell precision and recall, citation
  correctness, grounded answer accuracy, unsupported-claim rate, OCR error rate, latency, peak memory,
  provider request count, and cost per question.

## Privacy and threat review

Complete this review before enabling external vision or transcription in production:

- Document exactly which bytes and metadata leave the deployment.
- Require configuration and user disclosure for external media processing.
- Strip image metadata unless interpretation needs it.
- Check decoded dimensions and decompression limits, not only upload size.
- Treat OCR text, descriptions, transcripts, and codes inside images as untrusted prompt content.
- Block cross-session media access and path traversal.
- Avoid face, speaker, and biometric identification by default.
- Update the privacy policy, terms of service, third-party disclosures, and `.env.example`.

The behavior that is already live is described in [Step 12](STEP_12_PICTURE_INTERPRETATION.md#privacy-and-safety).

## Observability

Log structured events that contain no content: extraction method, page and region counts, retrieval
timings, candidate and selected counts per modality, images and bytes sent, provider and model identity,
response status, fallback reason, cleanup outcome, resource-limit rejections, and estimated and reported
cost. Raw images, encoded payloads, full OCR text, transcripts, and local media paths are never traced.

## Limitations

**Current (Step 12 slice):**

- One description per PDF page. Individual pictures are not cropped or located.
- No source preview, because page images are not kept after upload.
- Standalone images without OCR text depend entirely on the vision description.
- Quality depends on the vision model and the render resolution.

**Open decisions before Phase 2:**

- Maximum pages and rendered pixels per document.
- Whether page images may go to external providers by default, or only after explicit consent.
- Deployment target: Streamlit Cloud, local Windows, or both.
- Languages required for OCR and table extraction.
- Acceptable model download size and peak memory.
- Whether previews may persist across reruns but never in answer history.
- Quality, latency, and cost thresholds for turning on visual retrieval by default.

## Next iteration

The next iteration covers Phases 0 and 1 only:

1. Create the fixture manifest and the result-contract regression test.
2. Add the document model and a structured extraction function for searchable PDFs, DOCX, and TXT,
   without page rendering.
3. Add the artifact-to-text adapter.
4. Route the current text extraction through the adapter, where compatibility tests show the same output.
5. Leave the pipeline builder, embeddings, prompts, UI, and provider calls unchanged.
6. Run the ingestion, AI query, and legal-page tests.

## Related

- [STEP_1_INGEST.md](STEP_1_INGEST.md): current text extraction and OCR.
- [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md): page-aware chunking that the structured model would extend.
- [STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md): the text index that visual retrieval would sit beside.
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): the result contract that new fields extend.
- [STEP_11_GDPR_COMPLIANCE.md](STEP_11_GDPR_COMPLIANCE.md): privacy obligations for external media processing.
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md): the implemented page-level slice.
- [FUTURE_ADD_INS.md](FUTURE_ADD_INS.md): other planned extensions.
