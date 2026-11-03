# Step 5: Pipeline Orchestration

## Overview

The pipeline is the orchestration layer of DocuSearch. It connects the earlier steps (ingestion, preprocessing, embedding and indexing, and AI query) into one document question-answering flow. The public API lives in [src/pipeline.py](../src/pipeline.py) and has two entry points:

- `build_pipeline()` takes a file path, extracts its text, and prepares searchable chunks plus an optional embedding index.
- `answer_question()` takes the pipeline state and a question, selects context, builds the RAG prompt, and returns the answer with metrics.

The Streamlit app, the CLI, and tests all use the same two functions, so the result shape stays consistent across callers.

## Goals

- Run the processing steps in a fixed order: extract, clean, chunk, index, retrieve, generate.
- Keep the data flow between modules in one place.
- Degrade to keyword retrieval instead of failing when embeddings are unavailable or memory is low.
- Return one result dictionary that the UI, history, feedback, and cost tracking can all rely on.
- Handle explicit PDF page requests (for example "page 12") deterministically, without semantic search.

## Design Decisions

- **Lite mode is a state, not an error.** When the embedding index cannot be used, the pipeline returns `index: None` with `lite_mode: True`, and `answer_question()` retrieves chunks by keyword overlap. The user still gets an answer.
- **Embeddings are attempted by default in the web app and keyword search by default elsewhere.** The Streamlit app passes `use_embeddings=True` explicitly. When a caller omits the argument, `DOCUSEARCH_LITE_MODE` decides, and its default (`true`) selects keyword retrieval.
- **Memory is checked before the model loads.** Loading `all-MiniLM-L6-v2` is the most expensive step, so available memory is read first and embeddings are skipped if it is too low.
- **Oversized documents are rejected early.** Extracted text above a size limit raises `DocumentTooLargeError` before chunking or embedding starts.
- **Page markers are respected.** Chunks carry a `[PDF_PAGE:n]` marker, so explicit page requests select the matching chunks directly.
- **Tracing is optional.** `build_pipeline`, `build_pipeline_from_text`, and `answer_question` are decorated with LangSmith's `traceable` when the library is installed. Otherwise a no-op decorator is used.

## How the Flow Works

### 1. Build the pipeline

`build_pipeline(file_path, use_embeddings=None)` runs these steps:

1. Extracts raw text with `extract_text()` from [src/ingest.py](../src/ingest.py) (see [STEP_1_INGEST.md](STEP_1_INGEST.md)).
2. Passes the text to `build_pipeline_from_text()`, which does the remaining work.
3. Checks the extracted text size. The size is measured in characters converted to MB (1 MB = 1,024 × 1,024 characters), not in file bytes. Text above `MAX_DOCUMENT_MB` raises `DocumentTooLargeError`.
4. Cleans the text with `clean_text()` and splits it with `chunk_text()` from [src/preprocess.py](../src/preprocess.py) (see [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md)). Chunking does not cross PDF page boundaries.
5. Decides whether to attempt embeddings (see the next section).
6. If embeddings are wanted, checks available memory. If the value is known and below `MIN_AVAILABLE_MEMORY_GB`, the pipeline switches to lite mode. If memory cannot be determined, the check is skipped and embeddings are attempted.
7. Creates an `EmbedIndex` and calls `build_index(chunks)` (see [STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md)). If the index is disabled, has no embeddings, or the check on its state raises an error, the pipeline switches to lite mode.
8. Returns a dictionary with `index`, `chunks`, and `lite_mode`. `index` is `None` whenever lite mode is active.

### 2. Choose the retrieval mode

| Condition | Result |
|---|---|
| Streamlit app (passes `use_embeddings=True`) | Embedding attempt; `DOCUSEARCH_LITE_MODE` is ignored |
| `use_embeddings=True` passed explicitly | Embedding attempt, subject to the runtime fallbacks |
| `use_embeddings=False` passed explicitly | Keyword retrieval (`index: None`) |
| `use_embeddings` omitted, `DOCUSEARCH_LITE_MODE` true or unset | Keyword retrieval |
| `use_embeddings` omitted, `DOCUSEARCH_LITE_MODE` false | Embedding attempt |
| Available memory below `MIN_AVAILABLE_MEMORY_GB` | Lite mode, even when embeddings were requested |
| Embedding index unavailable after build | Lite mode |

Because `lite_mode` in the result means "keyword retrieval was used", it can be `True` even when the environment variable was not the reason.

### 3. Answer a question

`answer_question(pipeline, question, top_k=3, temperature=None, document_info="Unknown")` runs these steps:

1. **Explicit page request.** The question is checked for references such as "page 12", "pages 12-14", "pagina 12", "página 12", or "Seite 12". Matching chunks are selected directly by their `[PDF_PAGE:n]` marker, before any retrieval runs. At most five pages are included, and page context is capped at 30,000 characters. If the requested page has no extracted text, the model receives a notice saying so, and unrelated chunks are not used.
2. **Retrieval.** Without a page request:
   - In lite mode, `_lightweight_indices()` scores each chunk by how many whitespace-separated question tokens appear in it (case-insensitive substring match) and returns the top `top_k`. If nothing matches, chunk `0` is returned.
   - Otherwise, `index.search(question, k=top_k)` returns the nearest chunks.
   - Retrieval time is recorded as `retrieval_seconds`.
3. **Context assembly.** Selected chunks are bounds-checked and joined with blank lines. If any selected chunk carries an AI-generated picture description, a notice is prepended telling the model to label those descriptions as AI-generated and not to follow instructions inside them. See [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md).
4. **Prompt.** `load_prompt_with_temperature("rag_prompt", ...)` in [src/prompt_loader.py](../src/prompt_loader.py) renders `prompts/rag_prompt.txt` and returns the temperature from the prompt file's directive.
5. **Generation.** `generate_answer_with_meta()` in [src/ai_query.py](../src/ai_query.py) calls the provider, or returns a simulated or error state (see [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md)). The explicit `temperature` argument, when given, overrides the file value.
6. **Result.** The function returns the result dictionary described below.

### 4. Web-app Hybrid fallback

The Streamlit app adds one more layer in `run_hybrid()` in [app_pages/home.py](../app_pages/home.py). If the RAG answer is successful but matches an "inconclusive" phrase (for example "does not contain", "not mentioned", or the Romanian equivalents), the app asks Direct LLM mode to answer from the full extracted text. The fallback reason is recorded in the result. Explicit page requests are excluded from this fallback because their context was chosen deterministically. Failed provider calls are not sent to the fallback.

## Result Dictionary

`answer_question()` always returns these keys, which the UI and history rely on:

- Answer and status: `query`, `raw_answer`, `response_status`, `error_type`, `error_message`, `used_live_api`
- Context: `source_chunks`, `lite_mode`, `chunk_count`, `context_chars`, `requested_pdf_pages`
- Timing: `retrieval_seconds`, `generation_seconds`, `total_seconds`
- Tokens: `prompt_tokens`, `completion_tokens`, `total_tokens`, `estimated_tokens`
- Other: `temperature`, `langsmith_run_id`, `picture_description_used`, `picture_descriptions`

`requested_pdf_pages` is empty for ordinary questions. DOCX and TXT inputs have no physical PDF page boundaries, so page requests are not resolved for them. Only results with `response_status="success"` are charged, saved to history, or offered for rating.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DOCUSEARCH_LITE_MODE` | `true` | Chooses keyword or embedding retrieval only for callers that omit `use_embeddings` (for example the CLI). Does not affect the Streamlit app. |
| `MAX_DOCUMENT_MB` | `50` | Size limit for extracted text. Larger documents raise `DocumentTooLargeError`. |
| `MIN_AVAILABLE_MEMORY_GB` | `2.0` | Available-memory threshold below which embeddings are skipped. |

These are read when the module is imported. See [.env.example](../.env.example) for the full list of settings.

## Error Handling and Fallbacks

- **Oversized document:** `DocumentTooLargeError` is raised before chunking, so no embedding work starts. The message includes the measured size and the limit.
- **Low or unknown memory:** Low memory forces lite mode. Unknown memory (for example, a platform where no method works) does not block embeddings.
- **Embedding failure:** If the index is disabled or has no embeddings after build (for example, the model failed to load or ran out of memory), the pipeline returns lite mode instead of raising.
- **Chunking failure:** The error is logged to stderr and re-raised.
- **Out-of-range indices:** Retrieved indices are filtered against the chunk count before use.
- **Unavailable page:** The model is told that the requested physical page has no extracted text. The pipeline does not substitute unrelated chunks.
- **Provider failure:** Errors from `generate_answer_with_meta()` are returned in `response_status` and `error_message` rather than raised.

Diagnostic messages are written to stderr with a `[PIPELINE]` prefix.

## Memory Detection

`_available_memory_gb()` tries three methods in order and returns the first usable value in GB:

1. POSIX `os.sysconf` (available physical pages × page size). Works on Linux containers such as Streamlit Cloud, and on macOS.
2. `MemAvailable` from `/proc/meminfo`.
3. Windows `GlobalMemoryStatusEx` through `ctypes`.

It returns `None` when none of the methods works. A `None` result is never treated as zero memory.

## Module Layout

**File:** [src/pipeline.py](../src/pipeline.py)

Public functions:

- `build_pipeline(file_path, use_embeddings=None)`
- `build_pipeline_from_text(text, use_embeddings=None)` (used by the web app, which already has extracted text)
- `answer_question(pipeline, question, top_k=3, temperature=None, document_info="Unknown")`

Internal helpers:

- `_lightweight_indices()` (keyword retrieval)
- `_requested_pdf_pages()`, `_indices_for_pdf_pages()`, and `_pdf_page_request_is_truncated()` (explicit page requests)
- `_available_memory_gb()` (memory check)

Modules it depends on:

- [src/ingest.py](../src/ingest.py), [src/preprocess.py](../src/preprocess.py), [src/embed_index.py](../src/embed_index.py), [src/ai_query.py](../src/ai_query.py)
- [src/prompt_loader.py](../src/prompt_loader.py) for the RAG prompt and its temperature
- [src/visual_content.py](../src/visual_content.py) for extracting picture-description markers

## Tests

Pipeline behavior is covered by the existing suites. Run them from the repository root:

```powershell
python -m test_src.test_ingest
python -m test_src.test_ai_query
python -m test_src.test_visual_ingest
```

What each suite covers for this step:

- `test_ingest`: the size limit, small-document behavior, the low-memory fallback to lite mode, memory detection, and pipeline use after upload cleanup.
- `test_ai_query`: pipeline propagation of provider failures, explicit PDF page requests (including ranges, languages, unavailable pages, and the five-page limit), and the Hybrid rule that page requests do not fall back to the full document.
- `test_visual_ingest`: picture descriptions passing through `answer_question()` with the AI-generated label.

## Limitations

- Keyword retrieval in lite mode is simple token overlap. It does not handle stemming, synonyms, or other languages well, and it can return weakly related chunks.
- The size limit counts extracted text characters, not the original file size.
- Memory detection is best effort. On platforms where it fails, embeddings are attempted regardless of memory.
- Explicit page requests depend on physical PDF page markers. Printed page numbers inside a document may differ.
- Page requests are limited to five physical pages per question, and context is capped at 30,000 characters.
- `answer_question()` uses the top-k setting only; there is no adaptive selection of `top_k`.

## Related

- [STEP_1_INGEST.md](STEP_1_INGEST.md): text extraction and OCR
- [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md): cleaning and chunking
- [STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md): embedding index and search
- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md): provider calls and prompt temperature
- [STEP_6_HISTORY_TRACKING.md](STEP_6_HISTORY_TRACKING.md): storing successful results
- [STEP_8_FEEDBACK_COLLECTION.md](STEP_8_FEEDBACK_COLLECTION.md): rating successful answers
- [STEP_10_COST_TRACKING.md](STEP_10_COST_TRACKING.md): token and cost metrics
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md): picture descriptions in the context
