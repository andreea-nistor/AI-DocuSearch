# Step 2: Preprocessing & Text Cleaning

**Status:** Implemented in `src/preprocess.py`, used by `src/pipeline.py`.

## Goal

Turn the raw text produced by Step 1 (see [STEP_1_INGEST.md](STEP_1_INGEST.md)) into clean, bounded segments that can be embedded and searched. The step has two jobs:

- Normalize the text so that extraction noise (mixed line endings, runs of blank lines, irregular spacing) does not affect later steps.
- Split the text into overlapping chunks of a fixed maximum size, while keeping PDF page boundaries intact so that page-based questions can be answered reliably.

## Design Decisions

- **Simple, deterministic cleaning.** Cleaning uses three regular expressions and a `strip()`. It does not try to understand language, so it is fast and predictable.
- **Character-based chunking.** Chunks are measured in characters, not tokens. This avoids a tokenizer dependency and keeps the step independent of the embedding model.
- **Sliding window with overlap.** Consecutive chunks share a fixed number of characters, so a sentence that straddles a boundary is still present in full in at least one chunk.
- **Page-aware chunking.** Text from a PDF carries `[PDF_PAGE:n]` markers. Each physical page is chunked on its own, so no chunk mixes two pages and every chunk records the page it came from.
- **Defaults only in the pipeline.** The pipeline calls `chunk_text` with its default size and overlap. Callers can pass other values, but the app does not expose them as configuration.

## How the Flow Works

The pipeline calls the two functions in order from `build_pipeline_from_text()` in [src/pipeline.py](../src/pipeline.py).

### 1. Size guard (before this step)

Before cleaning, the pipeline rejects text larger than `MAX_DOCUMENT_MB` so that chunking and embedding never start on an oversized document. This check is part of the pipeline, not of this module.

### 2. Cleaning (`clean_text`)

The text goes through four ordered operations:

1. Convert Windows line endings (`\r\n`) to `\n`.
2. Collapse two or more consecutive newlines into a single blank line (`\n\n`).
3. Collapse runs of spaces and tabs into a single space.
4. Strip leading and trailing whitespace.

Cleaning keeps line structure (single newlines and paragraph breaks) and does not touch the `[PDF_PAGE:n]` markers, which stay on their own lines.

### 3. Chunking (`chunk_text`)

1. **Validation.** If `chunk_size` is not greater than `overlap`, a `ValueError` is raised. Empty input returns an empty list.
2. **Marker detection.** The function looks for `[PDF_PAGE:n]` markers that sit alone on a line.
3. **Unmarked text.** If there are no markers, the whole text is chunked with the sliding window. Text that appears before the first marker is chunked the same way, without a page prefix.
4. **Per-page chunking.** For each marked page, the page content is stripped and chunked with the sliding window. Each resulting chunk is prefixed with its own `[PDF_PAGE:n]` marker and a newline.
5. **Empty pages.** A page with no text still produces one chunk that contains only its marker, so page numbers remain complete and page-based lookups still find the page.

The sliding window works as follows. Each chunk takes up to `chunk_size` characters starting at the current position. If the chunk reaches the end of the text, the loop stops. Otherwise, the next window starts `overlap` characters before the end of the current one. Because `chunk_size` is greater than `overlap`, the window always moves forward.

Defaults are `chunk_size=500` and `overlap=100`. For a 1,200-character string, this produces three chunks: characters 0 to 500, 400 to 900, and 800 to 1,200.

### 4. Output

The result is a list of strings. Each string is either plain text (for DOCX, TXT, and images) or a page-prefixed chunk (for PDFs). The list goes to Step 3 ([STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md)) for embedding, or to keyword search when embeddings are not used.

## Configuration

This step has no environment variables of its own. The values below are fixed in code or are set by the pipeline.

| Setting | Where | Default | Effect |
|---------|-------|---------|--------|
| `chunk_size` | `chunk_text()` argument | 500 | Maximum characters per chunk. |
| `overlap` | `chunk_text()` argument | 100 | Characters shared by consecutive chunks. Must be less than `chunk_size`. |
| `MAX_DOCUMENT_MB` | Environment variable, read in `src/pipeline.py` | 50 | Documents with more extracted text than this are rejected before cleaning. |

## Error Handling and Fallbacks

- **Invalid parameters.** `chunk_text()` raises `ValueError` when `chunk_size` is not greater than `overlap`. The pipeline lets this error propagate after logging it to stderr.
- **Empty input.** An empty string produces an empty list. The caller decides what to do with it.
- **Memory errors.** `chunk_text()` catches `MemoryError`, writes a short message with the input length to stderr, and re-raises it. It does not try to recover.
- **Oversized input.** The size guard in the pipeline raises a `DocumentTooLargeError` with a readable message, so the app can show it to the user.

## Tests

There is no separate preprocessing test module. The chunking behavior is covered by tests in `test_src/test_ingest.py`:

- `test_pdf_chunking_never_crosses_page_boundaries` checks that every chunk starts with a page marker and that no chunk contains text from two pages.
- `test_picture_descriptions_are_labeled_and_attached_to_their_pdf_page` checks that chunking keeps picture descriptions with their own page.
- `test_oversized_document_is_rejected_before_chunking_or_embedding` checks the size guard.

Run them from the repository root:

```powershell
python -m test_src.test_ingest
```

The file `src/preprocess.py` also contains a small demo under `if __name__ == "__main__"` that cleans and chunks 200 generated lines and prints the chunk count. It is a manual check, not a test.

## Limitations

- Chunk size is measured in characters, so a chunk does not always match a token budget for a given embedding model.
- The sliding window can split a sentence or a table row across two chunks. Overlap reduces this but does not remove it.
- Cleaning collapses every run of spaces or tabs, including indentation, into one space, so content whose layout matters (for example, aligned columns) loses that layout.
- The whole document is held in memory. There is no streaming mode; the `MAX_DOCUMENT_MB` guard is the only protection against very large inputs.
- Chunk size and overlap are not configurable from the app or from environment variables.

## Related

- [STEP_1_INGEST.md](STEP_1_INGEST.md): produces the text this step cleans.
- [STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md): embeds and indexes the chunks.
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): orchestrates cleaning, chunking, and indexing, and applies the size guard.
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md): adds picture descriptions that are attached to page chunks.
