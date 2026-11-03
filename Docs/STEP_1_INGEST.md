# Step 1: Document Ingestion & Text Extraction

This step turns an uploaded or local document into plain text. Every later step (preprocessing, embeddings, retrieval, and the LLM answer) works on the string this step produces. The code lives in [src/ingest.py](../src/ingest.py).

## Goal

- Accept the common document formats used in DocuSearch: PDF, DOCX, plain text, and standalone images.
- Return one UTF-8 string per document, with enough structure left in it for later steps to know which page each piece of text came from.
- Recover text from scanned PDFs and images when no text layer exists, using OCR.
- Fail with clear messages for files that cannot be read, and degrade quietly where a partial result is still useful.

## Design Decisions

- **Dispatch by extension.** `extract_text()` is the single entry point. It lowercases the file extension and routes to a format-specific reader. Unknown extensions are read as text, so the step never rejects a file just because its extension is unfamiliar.
- **Page markers.** Every physical PDF page is written as a `[PDF_PAGE:n]` block, including empty pages. Page numbers survive into the chunks, which is what allows page-specific questions to be answered later.
- **Searchable text first, OCR second.** PDFs are read from their text layer with `pypdf`. OCR (`pdf2image` plus `pytesseract`) runs only when that layer yields no text, because OCR is much slower.
- **Forged marker neutralization.** Uploaded text can contain strings that look like internal markers (`[PDF_PAGE:n]` or `[PICTURE_DESCRIPTION:...]`). All readers pass their output through `neutralize_forged_markers()` from [src/visual_content.py](../src/visual_content.py), so only the extractor can create real page and AI-description markers.
- **Optional heavy dependencies.** `pypdf`, `python-docx`, `pdf2image`, and `pytesseract` are imported inside the functions that use them. A missing package produces a `RuntimeError` with install hints instead of breaking module import.

## Supported Formats

| Extension | Reader | Notes |
|-----------|--------|-------|
| `.pdf` | `extract_text_from_pdf()`, then OCR if empty | Searchable PDFs use `pypdf`; scanned PDFs fall back to OCR |
| `.docx` | `extract_text_from_docx()` | Paragraphs and tables are both extracted |
| `.png`, `.jpg`, `.jpeg`, `.webp` | `extract_text_from_image()` | OCR text, or an empty string when OCR is unavailable |
| `.doc` | none | Rejected with a `RuntimeError`; convert to `.docx` or plain text first |
| Anything else | `extract_text_from_text_file()` | Read as UTF-8 text, ignoring undecodable bytes |

Image text is only one part of the picture handling. When `MULTIMODAL_ENABLED=true`, a vision model also describes the image, as covered in [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md).

## How the Flow Works

1. `extract_text()` checks that the path exists and raises `FileNotFoundError` otherwise.
2. The extension is lowercased and matched against the supported formats above.
3. **PDF:** `pypdf` reads each page in order. Each page's text is stripped and wrapped in a `[PDF_PAGE:n]` block, and the blocks are joined with blank lines.
4. **PDF OCR fallback:** if the result contains no text beyond the page markers, the file is rendered to images at 300 DPI and each page is OCR'd. The `POPPLER_PATH` environment variable is passed to `pdf2image` when set. OCR failures do not raise; the original (possibly empty) text is returned.
5. **DOCX:** non-empty paragraphs are kept, stripped, and joined with newlines. Each table row is then appended as one line, with its non-empty cells joined by ` | `.
6. **Images:** the image is opened with Pillow and passed to Tesseract. If OCR fails for any reason, the function returns an empty string so that a vision-only description can still be produced.
7. **Plain text:** the file is read as UTF-8 with undecodable bytes dropped.
8. Every reader applies `neutralize_forged_markers()` to the text it returns, including each PDF page before it is wrapped in its marker.

Helper functions also used by the rest of the app are `get_pdf_page_count()`, which returns the page count or `0` on failure, and the `PdfExtractionError` exception class.

## Error Handling and Fallbacks

- **Missing file:** `FileNotFoundError` from `extract_text()`.
- **Unreadable PDF:** if `pypdf` cannot parse the file (corrupted, password-protected, or unusual internal structure), `extract_text_from_pdf()` raises `PdfExtractionError` with a user-facing message. The OCR fallback is not attempted in this case, because OCR would fail on the same file.
- **Missing pypdf, python-docx, pdf2image, or pytesseract:** a `RuntimeError` with an install command.
- **Legacy `.doc`:** a `RuntimeError` asking the user to convert the file.
- **Per-page OCR failure:** that page becomes empty text, and the remaining pages are still processed.
- **OCR fallback failure for a PDF:** the empty or partial searchable text is returned without raising.
- **Image OCR failure:** the function returns `""` rather than raising.

## Configuration

| Variable | Required | Purpose |
|----------|----------|---------|
| `TESSERACT_CMD` | No | Full path to the Tesseract executable, when it is not on `PATH`. Read by both PDF OCR and image OCR. |
| `POPPLER_PATH` | No | Path to the Poppler `bin` directory, when it is not on `PATH`. Used by `pdf2image` for PDF OCR. An explicit `poppler_path` argument takes precedence. |

On Streamlit Cloud, Tesseract and Poppler are installed from [packages.txt](../packages.txt) (`tesseract-ocr`, `poppler-utils`, `libtesseract-dev`), so these variables are not needed there. Python packages are listed in [requirements.txt](../requirements.txt): `pypdf`, `python-docx`, `pdf2image`, `pytesseract`, and `pillow`.

## Tests

The tests are plain Python functions run by a custom script, not a test runner. Run the full set from the repository root:

```
python -m test_src.test_ingest
```

Coverage in [test_src/test_ingest.py](../test_src/test_ingest.py) includes:

- Plain text round-trip and `FileNotFoundError` for a missing path.
- DOCX extraction (skipped with a message if `python-docx` is not installed) and rejection of `.doc`.
- Corrupted PDFs raising `PdfExtractionError`, and not being swallowed by the OCR fallback.
- Page numbers preserved for searchable PDFs, including empty pages, and for OCR output where one page fails.
- The OCR fallback triggering only when the searchable text is empty.
- Forged `[PDF_PAGE:n]` and `[PICTURE_DESCRIPTION:...]` markers in TXT, DOCX, and PDF text being neutralized.
- Temporary upload cleanup after success and after failure, and the pipeline still working afterwards.

PDF and OCR tests use mocks (`patch("pypdf.PdfReader")` and fake `pdf2image`/`pytesseract` modules), so they run without sample files or system binaries.

For a quick manual check of one file, run the module with a path:

```
python -m src.ingest examples/sample.txt
```

This prints the extracted text, or `No text was extracted from the file.` when the result is empty.

## Limitations

- The whole document is read into memory. Very large PDFs take time and memory, and there is no streaming.
- OCR is slow on large or high-resolution scans, and quality drops on low-quality scans or non-Latin scripts. OCR language selection is not configurable in this step; Tesseract's default language is used.
- Plain-text decoding assumes UTF-8. Other encodings can lose characters because undecodable bytes are dropped rather than reported.
- Legacy `.doc` files are not supported.
- Text extraction does not preserve layout, fonts, or tables in PDFs. Only the text layer, or OCR output, is kept.

## Related

- [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md): consumes this step's output, cleans it, and splits it into page-aware chunks.
- [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md): explains how `packages.txt` provides the OCR system binaries on Streamlit Cloud.
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md): adds vision-model descriptions for pages and images.
