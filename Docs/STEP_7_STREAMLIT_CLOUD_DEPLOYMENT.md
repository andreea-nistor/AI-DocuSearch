# Step 7: Streamlit Cloud Deployment

This document describes how the application is packaged and run on Streamlit Community Cloud, and how the code in the repository implements the deployment-specific behaviour: secrets bridging, startup order, memory and size guards, temporary upload handling, and the optional LangSmith tracing.

## Goal

Run AI DocuSearch as a public Streamlit web app without committing credentials, while keeping the same code path that runs locally. The repository needs only a small set of deployment files, and the app adapts at runtime to the memory and OCR resources available on the host.

## Design Decisions

| Concern | Decision | Where it lives |
|---|---|---|
| Entry point | `web_app.py` is the Streamlit main file and builds navigation with `st.navigation` | [web_app.py](../web_app.py) |
| Python dependencies | Pinned by name in `requirements.txt` (unpinned versions) | [requirements.txt](../requirements.txt) |
| OS-level OCR dependencies | apt packages listed in `packages.txt` (tesseract, poppler) | [packages.txt](../packages.txt) |
| Secrets | Entered in the Streamlit Cloud UI; copied into `os.environ` at startup | [app_pages/home.py](../app_pages/home.py) |
| Local configuration | `.env` loaded with `python-dotenv`; `.env` and `.streamlit/` are git-ignored | [.env.example](../.env.example), [.gitignore](../.gitignore) |
| Memory safety | Document size cap and available-memory check before embedding | [src/pipeline.py](../src/pipeline.py) |
| Uploads | Written to a temp directory and deleted after use; stale files swept at startup | [src/upload_storage.py](../src/upload_storage.py) |

## Implementation Flow

1. **Navigation entry.** `web_app.py` registers the home page as the default page. The privacy policy, terms of service, and third-party services pages are registered as hidden pages, so they are reachable through links but not listed in the sidebar.

2. **Secrets bridging.** `app_pages/home.py` sets the BLAS thread-limit environment variables first, then loads `.env` (for local runs) and copies every key in `st.secrets` into `os.environ`. Values are converted to strings. This runs inside a `st.cache_resource` function, so it executes once per server process. All later code reads configuration through `os.getenv`, which keeps local and cloud behaviour identical.

3. **LangSmith initialization.** Tracing is set up before the provider modules are imported. If `LANGSMITH_TRACING` is not set, it defaults to `false`. Tracing failures never block the app.

4. **Session setup.** Each browser session gets a random UUID hex identifier. History, feedback, and the cost tracker use this identifier. Old upload temp files are removed with `cleanup_stale_uploads()`, which deletes only files in the application's own temp directory that are older than one hour. Retention cleanup for history and feedback files also runs at startup, and the cleanup is cached so it does not run on every rerun.

5. **Start gates.** The language choice (English or Română) is shown first. The GDPR consent banner comes next. If consent is not given, the page stops with `st.stop()`. A budget gate then checks the per-session cost tracker and stops the page when the session is blocked.

6. **Upload.** The uploader accepts PDF, DOCX, and TXT files. PNG, JPEG, and WebP images are accepted only when `MULTIMODAL_ENABLED=true`. The file is written with `temporary_upload()`, which always removes it in a `finally` block. Extraction and pipeline building run on that path.

7. **Pipeline build and guards.** `src/pipeline.py` refuses extracted text larger than `MAX_DOCUMENT_MB` (default 50) with a `DocumentTooLargeError`. It checks available memory against `MIN_AVAILABLE_MEMORY_GB` (default 2.0). If memory is low or the embedding model cannot be used, the pipeline returns an index of `None`, and the app answers with keyword retrieval.

8. **Question answering (Hybrid mode).** Each question calls `run_hybrid()`. It tries RAG first. It falls back to Direct LLM when the pipeline is missing, the RAG answer is inconclusive (English or Romanian patterns), or RAG raises an exception. Requests for specific pages can be answered from the page-matched chunks.

9. **Response handling.** Only results with `response_status="success"` are charged to the session budget, written to history, and offered for feedback. A `simulated` result (no API configuration) is shown with a warning and is not charged or stored. Any other status shows a provider error message.

10. **Rendering.** `render_chat_history()` draws the conversation as HTML-escaped chat bubbles with feedback controls. A footer with the GDPR links is rendered on every page. The per-answer metrics helper and the aggregate metrics helper exist in `app_pages/home.py`, but the live chat flow does not call them, so the app does not show a metrics panel.

## Configuration

Set these in the Streamlit Cloud Secrets editor (as `KEY = "value"` lines) or in a local `.env` file. The table lists the variables read by the code, with defaults from the code when unset.

| Variable | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | none | API key for the OpenAI-compatible provider. Fallbacks: `OPENAI_API_KEY`, `XAI_API_KEY`, `GROK_API_KEY` |
| `LLM_API_BASE` | none | Chat completions base URL. Fallbacks: `OPENAI_API_BASE`, `XAI_API_BASE`, `GROK_API_BASE`. If only `OPENAI_API_KEY` is set, `https://api.openai.com/v1` is used |
| `LLM_MODEL` | none | Model name. Fallbacks: `OPENAI_MODEL`, `XAI_MODEL`, `GROK_MODEL` |
| `LLM_TEMPERATURE` | `0.2` | Sampling temperature. A `# temperature:` line in a prompt file takes precedence |
| `LANGSMITH_TRACING` | `false` | Enables LangSmith tracing when set to `true` |
| `LANGSMITH_API_KEY` | none | LangSmith API key |
| `LANGSMITH_PROJECT` | `default` in code, `ai-docusearch` in `.env.example` | LangSmith project name |
| `LANGSMITH_FEEDBACK_ENABLED` | `true` | Sends Helpful / Not helpful ratings to LangSmith |
| `HISTORY_ENABLED` | `true` | Enables per-session question history |
| `HISTORY_RETENTION_DAYS` | `30` | Age limit for history files |
| `HISTORY_LIMIT` | `10` | Number of history entries kept per session |
| `FEEDBACK_RETENTION_DAYS` | `90` | Age limit for feedback files |
| `MAX_DOCUMENT_MB` | `50` | Maximum size of extracted text before chunking |
| `MIN_AVAILABLE_MEMORY_GB` | `2.0` | Below this available memory, keyword retrieval is used |
| `DOCUSEARCH_LITE_MODE` | `true` | Default retrieval mode for callers that omit `use_embeddings` (for example, the CLI). The web app passes `use_embeddings=True` explicitly |
| `MULTIMODAL_ENABLED` | `false` | Enables picture interpretation and image uploads |
| `VISION_MODEL` | falls back to `LLM_MODEL` | Vision-capable model on the same API base |
| `MEDIA_MAX_PAGES` | `25` | Maximum PDF pages sent for picture interpretation |
| `MEDIA_MAX_IMAGE_PIXELS` | `20000000` | Pixel limit for images sent to the vision model |
| `VISION_RENDER_DPI` | `110` | Render resolution for PDF pages sent to the vision model |
| `VISION_MAX_IMAGE_EDGE` | `1568` | Longest edge, in pixels, for images sent to the vision model |
| `TESSERACT_CMD` | system `PATH` | Tesseract executable path (local Windows use) |
| `POPPLER_PATH` | system `PATH` | Poppler `bin` directory (local Windows use) |

On Streamlit Cloud, Tesseract and Poppler are installed from `packages.txt`, so `TESSERACT_CMD` and `POPPLER_PATH` are not needed there.

## Deployment Procedure

1. Push the repository to GitHub. Confirm that `.env` and `.streamlit/` are not committed.
2. In Streamlit Community Cloud, create an app from the repository and set the main file path to `web_app.py`.
3. Add the secrets listed above in the app's Secrets settings. At minimum, set `LLM_API_KEY`, `LLM_API_BASE`, and `LLM_MODEL`.
4. Deploy. Cloud installs `requirements.txt` and the apt packages in `packages.txt`.
5. Open the app, select a language, accept the consent notice, upload a small file, and ask a question. A successful answer confirms the provider configuration. A `[SIMULATED ANSWER]` warning means the API settings were not found.

## Error Handling and Fallbacks

- **Missing provider configuration** returns a simulated answer that is labelled as such and is not charged or saved.
- **Provider failure** shows an error message and the answer is neither charged nor saved.
- **Document too large** (text over `MAX_DOCUMENT_MB`) is refused before chunking, and the user sees an error.
- **Low memory or unavailable embedding model** switches retrieval to keyword search.
- **Scanned PDFs** without a text layer go through OCR. If OCR is unavailable, a warning is shown.
- **Session budget** is $0.50 per session. The UI warns at 80% and blocks further questions at 100%. Costs are estimated from fixed per-token assumptions in `src/cost_tracker.py`.
- **Unexpected exceptions** in the question flow are shown in the UI with the exception type and a short troubleshooting hint, and are printed to the server logs.

## Tests

Run these from the repository root:

- `python -m test_src.test_legal_pages` uses Streamlit's `AppTest` to check the language gate and the legal page navigation. It does not need network access.
- `python -m test_src.test_langsmith` checks LangSmith configuration and sends one traced test call. It is a script, not a pytest test, and needs LangSmith credentials and network access.
- `python -m test_src.test_ingest` covers text, DOCX, and PDF extraction, including page markers.
- `python -m test_src.test_history` covers history isolation between sessions.

## Limitations

- Streamlit Community Cloud's file system is ephemeral. Files in `history/` and `feedback/` are lost when the app restarts or is redeployed.
- Session history and the cost budget are tied to a browser session. Refreshing the page starts a new session and a new budget.
- The cost budget is enforced in the UI only. It is an estimate, not billing data.
- Mobile detection reads a `_user_agent` query parameter or the `HTTP_USER_AGENT` environment variable. Standard Streamlit does not set either by default, so the mobile layout is not reliably applied. This was not tested in a browser.
- Memory limits on the Cloud host are not configurable from the app. `MAX_DOCUMENT_MB` and `MIN_AVAILABLE_MEMORY_GB` are the app's only controls.
- Romanian OCR accuracy depends on the Tesseract language data installed by `packages.txt`. The file does not list a Romanian language pack, so this was not verified.

## Related

- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md) describes the provider call and configuration precedence.
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md) describes the RAG and Direct LLM pipeline used by Hybrid mode.
- [STEP_6_HISTORY_TRACKING.md](STEP_6_HISTORY_TRACKING.md) describes per-session history and retention.
- [STEP_8_FEEDBACK_COLLECTION.md](STEP_8_FEEDBACK_COLLECTION.md) describes feedback capture and LangSmith feedback.
- [STEP_9_INTERNATIONALIZATION.md](STEP_9_INTERNATIONALIZATION.md) describes the English and Romanian UI.
- [STEP_10_COST_TRACKING.md](STEP_10_COST_TRACKING.md) describes the session budget.
- [STEP_11_GDPR_COMPLIANCE.md](STEP_11_GDPR_COMPLIANCE.md) describes the consent banner and data export.
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md) describes the optional vision feature.
