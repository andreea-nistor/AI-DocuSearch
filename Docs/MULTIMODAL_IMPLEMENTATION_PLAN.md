# Multimodal Document Intelligence Implementation Plan

**Created:** 2026-09-02  
**Status:** In progress  
**Target:** Incremental delivery without breaking the current text-only Hybrid workflow

## Implementation Status (2026-09-14)

Implemented, gated by `MULTIMODAL_ENABLED=false` by default:

- `src/visual_content.py`: `PictureDescription` contract, `[PICTURE_DESCRIPTION:<id>|AI_GENERATED]`
  markers, page-aware attachment, and extraction of selected descriptions from chunks.
- `src/ai_query.py`: optional `images=[data_url, ...]` parameter that switches the request to
  OpenAI-style content parts and prefers `VISION_MODEL`; text-only calls are unchanged.
- `src/visual_ingest.py`: full-page PDF rendering (`pdf2image`), standalone PNG/JPEG/WebP
  validation (format, animation, pixel limit, EXIF orientation), JPEG re-encoding to a data URL,
  one vision call per image, `NO_MEANINGFUL_PICTURE` sentinel to skip picture-less pages, and
  never-raising `VisualIngestResult` with a `fallback_reason`.
- `prompts/picture_description_prompt.txt`: ingestion-time description prompt.
- `src/ingest.py`: image uploads OCR-or-empty instead of being decoded as UTF-8 text.
- `src/pipeline.py`: `picture_description_used` / `picture_descriptions` result fields and a
  disclosure notice in the RAG context.
- `app_pages/home.py`: uploader accepts images only when enabled; descriptions are generated while
  the temporary upload exists, vision tokens are charged, and chat history shows a disclosure
  caption.
- Tests: `test_visual_ingest.py`, plus additions to `test_ingest.py` and `test_ai_query.py`.

Not yet implemented: region-level detection and bounding boxes, session-scoped media storage and
source previews, structured tables, visual embeddings, deeper question-time inspection, audio,
and video. The current slice is page-level: one description per PDF page or uploaded image.

## 1. Objective

Add grounded question answering over document text, tables, pictures, diagrams, charts, forms, and
layout. Add audio and video only after document-image retrieval is stable and measurable.

The implementation must preserve:

- The existing PDF, DOCX, and TXT text workflow.
- Keyword and Direct LLM fallbacks when embeddings or multimodal services are unavailable.
- The current result dictionary fields used by the pipeline, UI, history, feedback, and metrics.
- Physical PDF page selection and its five-page request limit.
- Temporary-upload cleanup and private-content handling.
- Provider-neutral OpenAI-compatible configuration where the provider supports vision payloads.

## 2. Current Baseline

The current data path is:

```text
upload -> temporary file -> extract_text() -> list[str] chunks
       -> MiniLM text embeddings or keyword search -> text prompt -> chat completion
```

Important constraints:

- `src.ingest.extract_text()` returns only `str`.
- OCR page images are discarded after conversion to text.
- `src.preprocess.chunk_text()` and `src.embed_index.EmbedIndex` accept strings.
- `src.ai_query.generate_answer_with_meta()` sends one text content value.
- `app_pages/home.py` deletes the uploaded temporary file after extraction and retains text and the
  built pipeline in `st.session_state`.
- History and feedback rely on the current result metadata shape.

## 3. Delivery Principles

1. Introduce structured document data before adding model-specific behavior.
2. Keep text extraction and text retrieval as a supported path, not a legacy path to remove.
3. Preserve source location at every transformation: document, physical page, region, table cells,
   and eventually media timestamps.
4. Separate extraction, retrieval, and generation so each provider can be replaced independently.
5. Send the minimum necessary private media to external providers.
6. Add one end-to-end vertical slice at a time and gate it behind configuration.
7. Use benchmark evidence to decide whether a new model improves quality enough to justify its
   latency, memory, licensing, and cost.

## 4. Proposed Core Contracts

Start with typed standard-library dataclasses. Avoid requiring a database or a model framework for
the first migration.

```python
@dataclass(frozen=True)
class BoundingBox:
    left: float
    top: float
    right: float
    bottom: float


@dataclass
class DocumentRegion:
    region_id: str
    page_number: int | None
    kind: Literal["text", "table", "picture", "chart", "formula", "form"]
    text: str
    bounding_box: BoundingBox | None = None
    media_ref: str | None = None
    extraction_method: str = "native"
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentPage:
    page_number: int
    text: str
    regions: list[DocumentRegion]
    page_image_ref: str | None = None


@dataclass
class DocumentArtifact:
    document_id: str
    filename: str
    media_type: str
    pages: list[DocumentPage]
    unpaged_regions: list[DocumentRegion] = field(default_factory=list)
```

For visual regions, `text` contains an automatically generated searchable description and
`metadata` records that it is model-generated, including the vision provider/model, generation
time, prompt version, and whether the source was a full page or an extracted picture. Generated
descriptions are supporting evidence and must never be presented as native document text.

Add a compatibility function:

```python
def artifact_to_marked_text(artifact: DocumentArtifact) -> str:
    """Produce the current [PDF_PAGE:n] text representation."""
```

This adapter allows structured ingestion to land before changing `chunk_text()`, `EmbedIndex`, or
the answer pipeline.

### Evidence Contract

Every retrieved item should use one citation shape:

```python
{
    "citation_id": "D1:P4:R2",
    "document_id": "...",
    "page_number": 4,
    "region_id": "p4-r2",
    "kind": "table",
    "bounding_box": [0.10, 0.15, 0.85, 0.60],
    "media_ref": None,
    "extraction_method": "native_docx_table",
    "confidence": 1.0,
}
```

Coordinates should be normalized to $[0,1]$ so previews are independent of rendered resolution.

## 5. Component Boundaries

```text
src/
|-- document_model.py      # Typed artifact, region, table, and citation contracts
|-- media_storage.py       # Session workspace, references, cleanup, and resource limits
|-- ingest.py              # Existing compatibility API and format dispatch
|-- visual_ingest.py       # PDF rendering, embedded images, OCR regions
|-- table_extraction.py    # DOCX/native PDF/scanned table normalization
|-- preprocess.py          # Text adapter plus modality-aware region chunking
|-- embed_index.py         # Existing text index
|-- multimodal_index.py    # Visual embeddings and visual search
|-- retrieval.py           # Result normalization, fusion, deduplication, reranking
|-- ai_query.py            # Text-only and multimodal provider payloads
`-- pipeline.py            # Orchestration and fallback policy
```

Do not place extraction, image encoding, score fusion, and provider payload construction in
`pipeline.py`; it should coordinate those components and preserve the result contract.

## 6. Phased Implementation

### Phase 0: Baseline, Fixtures, and Feature Flags

**Goal:** Make quality and compatibility measurable before structural changes.

Tasks:

- Add a small, redistributable fixture set containing searchable PDF pages, scanned pages, DOCX
  tables, a multi-page table, a chart, a diagram, rotated content, and an unreadable region.
- Record expected pages, regions, table values, and answers in a machine-readable manifest.
- Add feature flags with disabled defaults:

```dotenv
MULTIMODAL_ENABLED=false
DOCUMENT_LAYOUT_ENABLED=false
TABLE_EXTRACTION_ENABLED=false
VISION_GENERATION_ENABLED=false
VISUAL_INDEX_ENABLED=false
MEDIA_MAX_PAGES=25
MEDIA_MAX_IMAGE_PIXELS=20000000
MEDIA_MAX_IMAGES_PER_QUERY=3
```

- Capture baseline text extraction, retrieval, latency, and memory results.
- Add a result-contract regression test that asserts all required existing fields.

Exit criteria:

- Existing tests pass with every new flag disabled.
- Fixtures have clear expected outputs and acceptable usage rights.
- Baseline measurements are stored in a repeatable test or evaluation script.

### Phase 1: Structured Document Model and Compatibility Adapter

**Goal:** Preserve layout and source identity without changing user-visible answers.

Tasks:

- Add `src/document_model.py` with typed contracts and validation helpers.
- Add `extract_document()` beside `extract_text()` in `src/ingest.py`.
- Represent every physical PDF page, including empty pages.
- Convert the artifact back to the current marked text and compare it with `extract_text()`.
- Add stable region and citation identifiers that do not contain private text.
- Keep `build_pipeline_from_text()` unchanged during this phase.

Exit criteria:

- Existing ingestion and page-request tests continue to pass.
- Artifact-to-text output preserves all current physical page markers.
- Native text does not change unexpectedly after a structured round trip.
- Empty, malformed, and unsupported documents fail or fall back as they do today.

### Phase 2: Session-Scoped Derived Media

**Goal:** Safely preserve page renders and crops after the original upload is deleted.

Tasks:

- Add `src/media_storage.py` with a random session workspace under the app-owned temporary root.
- Return opaque media references, not arbitrary filesystem paths, to the rest of the application.
- Enforce extension, signature, byte-size, pixel-count, page-count, and generated-file limits.
- Delete a prior workspace when a new upload replaces it.
- Run stale-workspace cleanup at startup as a fallback for sessions that close unexpectedly.
- Exclude raw media and paths from history, feedback, and LangSmith traces.

Exit criteria:

- Derived files survive long enough for questions in the active session.
- Replacing an upload removes the previous derived media.
- Failure during extraction removes partial artifacts.
- Stale cleanup only removes application-owned workspaces.
- Tests cover traversal attempts, malformed images, and resource limits.

### Phase 3: Layout-Aware Tables

**Goal:** Make tables first-class structured and citable evidence before adding vision generation.

Tasks:

- Preserve DOCX rows, columns, merged cells, and surrounding titles instead of only joining cells.
- Evaluate a permissively licensed native PDF table extractor against the fixture corpus.
- Use OCR table extraction only when native extraction is unavailable.
- Add a `TableData` structure containing headers, rows, cells, spans, units, footnotes, page, and
  bounding box.
- Render selected table content as compact Markdown for the existing text LLM.
- Add deterministic table operations for filtering, sums, differences, percentages, minima, and
  maxima; never execute document-provided code.
- Retrieve at row or logical table-section level while preserving headers and footnotes.

Exit criteria:

- Expected table cells meet the accuracy target defined in Phase 0.
- Multi-page headers and continuation rows are preserved in supported fixtures.
- Arithmetic answers match deterministic expected values.
- Low-confidence or ambiguous cells are identified instead of silently normalized.
- Text-only providers can answer table questions without receiving images.

### Phase 4: Automatic Picture and Page Interpretation

**Goal:** Automatically interpret meaningful pictures while reading and chunking a document, then
use those descriptions when answering questions about evidence found on the same page. Also let
users directly ask a vision-capable LLM about a complete PDF page or standalone image upload.

This is the first genuine multimodal slice. Start with explicit page requests because the current
pipeline already selects physical PDF pages deterministically. Then enable the same provider path
for extracted PDF/DOCX pictures and standalone images.

Initial supported visual sources:

- Complete rendered PDF pages, including scanned pages.
- Pictures embedded in PDF and DOCX documents, with their page or document location when known.
- Standalone `.png`, `.jpg`, `.jpeg`, and `.webp` uploads.
- `.tif`, `.tiff`, `.bmp`, `.gif`, and HEIC/HEIF only in a later compatibility increment after
  decoder, animation, orientation, deployment, and resource-limit tests are defined.

Example questions:

- "Describe the picture on page 3."
- "What objects and people are visible in this image?"
- "Read and explain the text in this screenshot."
- "What does the diagram show, and how are its components connected?"
- "Summarize the trend in this chart and identify its axes and units."
- "Does this picture support the statement in the surrounding paragraph?"

Tasks:

- Render configured PDF pages during ingestion and retain session-scoped references.
- Extract embedded PDF and DOCX pictures and associate them with nearby captions and text.
- Add validated standalone image ingestion for PNG, JPEG, and WebP, including EXIF orientation,
  decoded pixel limits, and metadata stripping where appropriate.
- During ingestion, detect meaningful pictures, charts, diagrams, screenshots, forms, and other
  visual regions; ignore repeated logos, tiny icons, separators, and decorative backgrounds where
  practical.
- Automatically send each accepted visual region to the configured vision-capable model once and
  generate a concise factual description suitable for retrieval.
- Store the description in its `DocumentRegion` with page number, bounding box, media reference,
  nearby caption, generation provenance, and confidence or warning metadata.
- During chunking, attach visual descriptions to text chunks from the same page using an explicit
  marker such as `[PICTURE_DESCRIPTION:p4-r2|AI_GENERATED]`; do not merge them into native document
  prose without a label.
- Index generated picture descriptions as searchable text so questions can retrieve a page through
  either its written content or its visual content.
- When text retrieval selects an answer page, collect meaningful picture descriptions from that
  page as companion evidence, subject to relevance and context limits.
- Add a provider-neutral `MessagePart` contract for text and images.
- Extend `generate_answer_with_meta()` through a new compatible entry point that accepts message
  parts while preserving text-only calls.
- Encode or upload only the requested pictures or page images according to provider capability.
- Add a separate multimodal prompt requiring page/region grounding and uncertainty disclosure.
- Instruct the LLM to describe only visible evidence, distinguish observation from inference, and
  state when content is unreadable, cropped, ambiguous, or too low resolution.
- Track images sent, encoded bytes, vision latency, and fallback reason without logging images.
- Fall back to extracted page text if vision is disabled, unsupported, oversized, or unavailable.
- For a standalone image with no useful OCR text, return a clear vision-unavailable message instead
  of pretending that the image was inspected.

Automatic processing flow:

```text
document upload
  -> extract native text and page structure
  -> detect and crop meaningful visual regions
  -> generate picture descriptions with a vision-capable model
  -> create page chunks containing labeled text and picture descriptions
  -> index both native text and generated descriptions
  -> retrieve answer chunks and companion pictures from the selected pages
  -> answer with citations and an explicit picture-description disclosure
```

Answer presentation rules:

- If a selected evidence page contains a meaningful picture description, include the relevant
  description under a clearly labeled section such as **Picture description (AI-generated)**.
- State that the answer includes an automatically generated picture interpretation and cite its
  page and region separately from native text evidence.
- Keep observations and uncertain interpretation separate. For example, use "The image appears to
  show" when the visual evidence is ambiguous.
- Never quote a generated picture description as if it were printed in the document.
- If several pictures exist on a selected page, include only descriptions relevant to the question
  or answer, up to a configurable limit. If relevance cannot be determined, include a compact list
  of the meaningful pictures on that evidence page rather than silently omitting them.
- If automatic interpretation failed, disclose that the page contains an image that could not be
  described; continue answering from available text and table evidence.

Exit criteria:

- A question such as "Describe the chart on page 4" sends only page 4 and relevant text.
- A standalone PNG, JPEG, or WebP can be uploaded and described by a configured vision-capable LLM.
- An embedded document picture can be described with its document and location citation.
- Every accepted picture is interpreted once during ingestion, not repeatedly for each question,
  unless the user explicitly requests deeper inspection.
- Picture descriptions are present in page chunks with an `AI_GENERATED` marker and are searchable.
- A text question whose answer is retrieved from a page containing a relevant picture returns the
  answer plus a labeled picture-description section and separate visual citation.
- Repeated logos and decorative graphics do not produce noisy descriptions in normal fixtures.
- Provider payload tests verify valid text-plus-image content and no unrelated page images.
- Unsupported formats, animated images, oversized decoded images, and malformed files are rejected
  with clear messages before a provider request is made.
- Provider errors retain the current explicit error semantics and do not create billable history.
- Text-only configuration still uses the current payload and passes existing tests.

### Phase 5: Visual Regions and Cross-Modal Retrieval

**Goal:** Find relevant visual evidence when the user does not provide a page number.

Tasks:

- Detect picture, chart, diagram, formula, and form regions with bounding boxes.
- Reuse the automatic ingestion-time descriptions and preserve nearby captions and paragraphs.
- Support optional deeper question-time visual inspection only when the stored description is not
  sufficient and the selected source image is still available.
- Evaluate a CLIP-compatible baseline against a document-focused visual retriever.
- Add `src/multimodal_index.py` behind a common retriever interface.
- Normalize text, table, and visual scores before fusion; do not compare raw scores directly.
- Deduplicate page and child-region results and enforce image/context budgets.
- Rerank a small candidate set where measured quality justifies the latency.

Exit criteria:

- Visual retrieval recall meets the Phase 0 target on unseen evaluation questions.
- Answers cite the retrieved region and page.
- Nearby captions remain associated with their images.
- Irrelevant images are not sent merely because they share a page with relevant text.
- Missing visual dependencies degrade to text retrieval with a recorded reason.

### Phase 6: Source Preview and Verification UI

**Goal:** Let users inspect the exact evidence supporting an answer.

Tasks:

- Add compact citation controls below answers.
- Show the page thumbnail with the cited bounding box highlighted.
- Render structured table evidence with cited cells emphasized.
- Label native text, OCR, table extraction, and visual interpretation.
- Display low-confidence warnings without exposing internal implementation instructions.
- Ensure media references cannot retrieve content from another session.
- Test desktop and mobile layouts with long answers, wide tables, and multiple citations.

Exit criteria:

- Every multimodal claim can be traced to visible evidence.
- Preview dimensions are stable and controls do not shift the chat layout.
- Keyboard navigation and accessible labels work for citations and previews.
- Expired or removed media produces a clear unavailable state.

### Phase 7: Multi-Document and Advanced Analysis

**Goal:** Use the structured evidence model for comparisons and specialized extraction.

Candidate increments:

- Compare clauses, tables, figures, and revisions across documents.
- Extract forms, checkboxes, signatures, handwriting, formulas, and key-value fields.
- Add user corrections for OCR and table cells, with targeted reindexing.
- Add sensitive-region detection and redaction before external vision calls.
- Export grounded reports with citation metadata.

Each increment requires a separate fixture set and acceptance target.

### Phase 8: Audio

**Prerequisite:** Stable media lifecycle, evidence citations, provider abstraction, and cost limits.

Tasks:

- Add duration-limited audio ingestion and safe media probing.
- Transcribe with timestamps, detected language, and optional speaker labels.
- Represent transcript segments as regions with start and end times.
- Retrieve transcript segments using the existing text index.
- Add time-range citation playback in the UI.
- Treat speaker identity and voice data as sensitive; disable identity inference by default.

Exit criteria:

- Answers cite exact transcript time ranges.
- Unsupported codecs, long files, and transcription failures degrade cleanly.
- Temporary audio and derived files follow the same cleanup policy as document images.

### Phase 9: Video

**Prerequisite:** Audio phase complete and explicit operational limits approved.

Tasks:

- Extract audio, scene boundaries, representative keyframes, and visible text.
- Associate transcript intervals, scenes, and keyframes on one timeline.
- Retrieve transcript and visual evidence without processing every frame.
- Add timestamped video citations and playback.
- Enforce strict duration, resolution, frame-count, disk, memory, and provider-cost limits.

Exit criteria:

- Answers cite a scene or time range and expose supporting keyframes or transcript text.
- Processing remains within configured resource budgets.
- Partial failures, such as missing audio, still allow supported modalities to be queried.

## 7. Provider and Dependency Evaluation

Select dependencies with a written evaluation rather than committing to them in advance.

| Capability | Baseline candidate | Evaluation criteria |
|---|---|---|
| PDF rendering | Existing `pdf2image` | Page fidelity, Poppler availability, memory, speed |
| OCR regions | Existing Tesseract `image_to_data` | Languages, coordinates, confidence, rotated text |
| DOCX tables | Existing `python-docx` | Merged cells, nested tables, order, images |
| Native PDF tables | `pdfplumber` candidate | License, ruled/unruled tables, coordinates, accuracy |
| Visual embeddings | CLIP-compatible Sentence Transformer | Cross-modal recall, memory, model size, license |
| Vision generation | Existing provider-neutral adapter | Payload compatibility, grounding, privacy, cost |
| Audio transcription | Provider or local Whisper-compatible adapter | Accuracy, language, timestamps, memory, license |
| Video probing | FFmpeg/ffprobe candidate | Deployment availability, sandboxing, resource limits |

Before adding a dependency, record:

- License and redistribution implications.
- Python and Streamlit Cloud compatibility.
- Download size, peak memory, CPU needs, and cold-start time.
- Whether external binaries or model downloads are required.
- Offline behavior and failure mode.
- Supported languages and file formats.

## 8. Retrieval and Generation Policy

The initial fusion policy should be explicit and testable:

1. Honor explicit physical page requests before semantic retrieval.
2. Retrieve text, table, and ingestion-time picture-description candidates.
3. For every selected answer page, collect its meaningful picture descriptions as companion
  evidence and rank them for relevance to the question and answer context.
4. Retrieve visual-embedding candidates only when enabled and potentially relevant.
5. Normalize scores per retriever.
6. Deduplicate parent pages and child regions.
7. Select evidence within text, picture-description, image-count, encoded-byte, and provider limits.
8. Generate from evidence labeled as native text, OCR, structured table, or AI-generated picture
  description.
9. Add a labeled picture-description section whenever that evidence contributes to the response.
10. Return citations, modality usage, confidence signals, and fallback reasons.

The model must not claim to have inspected an image when only OCR or a generated caption was sent.

## 9. Result Contract Migration

Add optional fields with neutral defaults:

```python
{
    "modalities_used": ["text"],
  "picture_description_used": False,
  "picture_descriptions": [],
    "evidence_citations": [],
    "visual_sources": [],
    "table_sources": [],
    "images_sent": 0,
    "media_bytes_sent": 0,
    "multimodal_retrieval_seconds": 0.0,
    "vision_generation_seconds": 0.0,
    "media_fallback_reason": None,
}
```

Rules:

- Do not rename or remove existing result fields.
- Store compact citations in history, not raw media or base64 payloads.
- Count cost only for `response_status="success"`, consistent with current behavior.
- Ensure Direct LLM fallback supplies the same new fields with neutral defaults.
- Set `picture_description_used=true` only when at least one generated description is included in
  the answer context and expose those descriptions with separate visual citations.

## 10. Test Strategy

### Unit Tests

- Structured model validation and artifact-to-text compatibility.
- Region identifiers, normalized coordinates, and citation serialization.
- Session media creation, replacement, stale cleanup, and failure cleanup.
- Native and scanned table normalization.
- Provider message construction for text-only and text-plus-image calls.
- Automatic picture-description generation, chunk markers, provenance, and decorative-image
  filtering.
- Score normalization, fusion, deduplication, and media-budget selection.
- Result-contract defaults across RAG, Direct LLM, Hybrid, and error paths.

### Integration Tests

- Searchable PDF, scanned PDF, DOCX table, chart, and mixed-content ingestion.
- Explicit page image question through retrieval and mocked vision generation.
- Text question that retrieves a page with a picture and returns a labeled picture description.
- Automatic description failure that preserves the text answer and records a fallback reason.
- Table question through deterministic calculation and cited answer.
- Vision-provider timeout, unsupported model, malformed response, and fallback.
- Upload replacement and expired media references.

### UI Tests

- Feature disabled behavior remains unchanged.
- Citation preview and highlighted region.
- Wide and multi-page tables on desktop and mobile.
- Low-confidence and media-unavailable states.
- No failed provider result is saved, rated, or charged.

### Evaluation Metrics

- Text and visual retrieval recall at $k$.
- Table cell precision and recall.
- Citation correctness and source-region overlap.
- Grounded answer accuracy and unsupported-claim rate.
- OCR character or word error rate on representative languages.
- Median and tail latency, peak memory, provider requests, and cost per question.

## 11. Privacy and Threat Review

Complete before enabling external vision or transcription in production:

- Document exactly which bytes and metadata leave the deployment.
- Require configuration and disclosure for external media processing.
- Strip image metadata unless required for interpretation.
- Validate decoded dimensions and decompression limits, not only upload byte size.
- Treat OCR text, captions, transcripts, and QR codes as untrusted prompt content.
- Prevent cross-session media access and path traversal.
- Avoid face identification, speaker identification, and biometric persistence by default.
- Update the Privacy Policy, Terms of Service, third-party disclosures, and `.env.example`.

## 12. Observability and Operations

Add structured, content-minimizing events for:

- Extraction method and page/region counts.
- Table and visual retrieval timings.
- Candidate and selected evidence counts by modality.
- Images and bytes sent to providers.
- Model/provider identity and response status.
- Fallback reason, cleanup outcome, and resource-limit rejection.
- Estimated and provider-reported token or media cost.

Do not trace raw images, base64 values, full OCR text, transcripts, or local media paths.

## 13. First Development Iteration

The first implementation iteration should include only Phases 0 and 1:

1. Create the fixture manifest and result-contract regression test.
2. Add `document_model.py`.
3. Add `extract_document()` for searchable PDFs, DOCX, and TXT without page rendering.
4. Add `artifact_to_marked_text()`.
5. Make `extract_text()` delegate through the adapter where compatibility tests prove equivalent.
6. Keep `build_pipeline_from_text()`, embeddings, prompts, UI, and provider calls unchanged.
7. Run ingestion tests, AI-query tests, and the Streamlit legal-page tests.

This iteration creates the required foundation while keeping its behavioral blast radius small.

## 14. Decisions Required Before Phase 2

- Maximum supported pages and rendered pixels per document.
- Whether page images may be sent to external providers by default or only after explicit consent.
- Required deployment target: Streamlit Cloud only, local Windows, or both.
- Minimum supported languages for OCR and table extraction.
- Acceptable model download size and peak memory.
- Whether source previews may persist across browser reruns but never in answer history.
- Target quality, latency, and cost thresholds for enabling visual retrieval by default.

## 15. Overall Completion Criteria

- Images and tables remain traceable evidence from ingestion through answer citations.
- Text-only operation remains fully supported.
- Multimodal failures fall back without fabricating visual inspection.
- Users can inspect the exact page, region, table cells, or media time range behind an answer.
- Temporary private media is bounded, isolated, and deleted.
- Quality and cost meet explicit benchmark thresholds.
- Documentation and legal disclosures match the released data flow.
