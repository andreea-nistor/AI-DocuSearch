# Step 8: User Feedback Collection & Analytics

Status: implemented for answer ratings (Helpful / Not helpful). Feature request and bug report types exist in the storage layer but are not exposed in the UI.

## Goal

Let users rate each Hybrid answer as helpful or not helpful, keep those ratings in a local per-session file, and optionally forward them to LangSmith so they can be reviewed next to the traced run that produced the answer.

## Design decisions

- **Local JSON storage.** Each browser session writes to its own file, `feedback/user_{session_id}.json`, relative to the working directory. The file is written with `write_json_atomic` in [src/json_io.py](../src/json_io.py), which writes a temporary file, calls `fsync`, and then replaces the target, so a crash cannot leave a truncated file behind.
- **Session identity.** `app_pages/home.py` creates a random `uuid4().hex` session ID the first time a session needs a `FeedbackManager`. The same ID is used by history storage and by GDPR export and deletion.
- **LangSmith is optional.** The local file is always written. LangSmith delivery is best effort and is skipped when tracing or the API key is not configured.
- **Retention by file age.** Old feedback files are removed by a cleanup function, not by per-entry expiry.

## How it works

1. The user clicks **Helpful** or **Not helpful** under an answer in the chat history. Each button has a key of the form `feedback_positive_{answer_id}` or `feedback_negative_{answer_id}`.
2. For chat history entries, `answer_id` is `ans_{timestamp}`, where the timestamp is the history entry's timestamp.
3. The handler calls `FeedbackManager.add_feedback()` with the question, the document name, the mode, the answer length, the chunk count, and the retrieval time from the stored metrics.
4. If the answer has a `langsmith_run_id`, the handler calls `submit_langsmith_feedback()` with `True` or `False`. The call is made in [src/langsmith_feedback.py](../src/langsmith_feedback.py).
5. The UI shows a thank-you message for a positive rating or a short "we will use this to improve" message for a negative rating.
6. The entry is appended to the session file. The file is loaded newest first when it is read.

A `render_result()` function also exists in `app_pages/home.py` for a per-answer view. The main flow does not call it, so the chat history buttons are the active path.

## Data stored per entry

| Field | Notes |
|-------|-------|
| `answer_id` | Identifier of the answer being rated |
| `rating` | `true` (helpful), `false` (not helpful), or `null` for non-rating feedback |
| `question` | The user's question, or `N/A` |
| `document_name` | Uploaded file name, or `N/A` |
| `comment` | Optional text, truncated to 500 characters |
| `feedback_type` | `answer_rating`, `feature_request`, `bug_report`, or `general_comment` |
| `mode` | For example `Hybrid (RAG)` or `Hybrid (fallback to DirectLLM)` |
| `answer_length` | Length of the answer in characters |
| `chunk_count` | Number of retrieved chunks |
| `retrieval_seconds` | Retrieval time, rounded to 2 decimals |
| `langsmith_run_id` | Run ID used for LangSmith delivery, when available |
| `timestamp` | Time the entry was recorded |

## Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `FEEDBACK_RETENTION_DAYS` | `90` | Feedback files older than this many days are deleted by the cleanup run |
| `LANGSMITH_FEEDBACK_ENABLED` | `true` | When set to a value other than `1`, `true`, `yes`, or `on`, ratings are not sent to LangSmith. The local file is still written |
| `LANGSMITH_API_KEY` | none | Required for LangSmith delivery |
| `LANGSMITH_TRACING` | none | Must be `true` for LangSmith delivery |

Set these in `.env` (see `.env.example`) or in the Streamlit Cloud secrets.

## Retention cleanup

The cleanup is `FeedbackManager.cleanup_old_feedback()`. It is called from `app_pages/home.py` through a function decorated with `st.cache_resource(ttl=3600)`, so it runs at most once per hour per server process, not on every rerun. It deletes files whose modification time is older than the retention period and prints a message for each deletion. Errors are ignored.

## Analytics and export

- `FeedbackManager.get_feedback_summary()` returns totals, positive and negative counts, the positive percentage, counts by feedback type, and the average answer length for ratings. The app does not render this summary.
- `python -m src.export_feedback` exports all feedback files to `feedback_export.json` and `feedback_export.csv`, and prints statistics and a per-mode breakdown.
- `python -m test_src.test_langsmith_feedback_report` tests the LangSmith feedback report CLI. That CLI reads ratings back from LangSmith and can filter by project, score, and date. Its exit codes are 2 for a missing key or client failure and 1 for a query failure.

## Privacy

- Feedback files are plain JSON and are not encrypted. The `question` and `document_name` fields can contain document-derived text.
- `feedback/*.json` is listed in `.gitignore`.
- The GDPR export and deletion functions in [src/gdpr_compliance.py](../src/gdpr_compliance.py) include the session's feedback file.
- When LangSmith delivery is enabled, the rating and optional comment are sent to LangSmith.
- The consent text in `src/i18n.py` states that feedback is kept for 90 days and then deleted.

## Error handling and fallbacks

- If the feedback file is missing, `load_feedback()` returns an empty list.
- If the file cannot be read or parsed, `load_feedback()` also returns an empty list and the error is printed.
- If LangSmith is not installed, not configured, or disabled, delivery returns `False` and the local rating is still saved.
- LangSmith errors are printed to stderr. They do not interrupt the UI.

## Tests

Run the feedback suite with:

`python -m test_src.test_feedback`

It covers adding, listing, summarizing, filtering, updating, exporting, comment truncation, persistence across manager instances, empty files, LangSmith delivery and the disabled case, and the two chat feedback buttons driven through Streamlit's `AppTest` (which runs `web_app.py` without a browser). The LangSmith client is mocked, so no network call is made.

## Limitations

- Clicking a feedback button again adds another entry. There is no de-duplication per answer.
- A corrupt feedback file is read as empty, and the next save overwrites it with the new entry.
- There is no locking. Concurrent writes to the same session file are last-writer-wins.
- Feedback is written to a relative `feedback/` directory, so its location depends on the working directory. On Streamlit Community Cloud the file system is ephemeral.
- Feature requests, bug reports, and general comments have a storage path (`add_feedback()` with those types) but no UI. The app's **Share feedback** button opens an external form instead.
- There is no switch that disables local feedback storage. Only LangSmith delivery can be turned off.
- `update_feedback_rating()` exists but the app does not call it.

## Related files

- [src/feedback_manager.py](../src/feedback_manager.py): `FeedbackManager` class, storage, summary, export, and cleanup
- [src/json_io.py](../src/json_io.py): atomic JSON writes
- [src/langsmith_feedback.py](../src/langsmith_feedback.py): LangSmith rating delivery
- [src/langsmith_feedback_report.py](../src/langsmith_feedback_report.py): LangSmith feedback report CLI
- [src/export_feedback.py](../src/export_feedback.py): local export and statistics CLI
- [src/gdpr_compliance.py](../src/gdpr_compliance.py): export and deletion of feedback data
- [app_pages/home.py](../app_pages/home.py): feedback buttons, session setup, and cleanup scheduling
- [test_src/test_feedback.py](../test_src/test_feedback.py): feedback tests

## Related

- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md): LangSmith run IDs and the `LANGSMITH_FEEDBACK_ENABLED` setting
- [STEP_6_HISTORY_TRACKING.md](STEP_6_HISTORY_TRACKING.md): the chat history entries that feedback is attached to
- [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md): deployment and secrets
- [STEP_11_GDPR_COMPLIANCE.md](STEP_11_GDPR_COMPLIANCE.md): export and deletion of user data
