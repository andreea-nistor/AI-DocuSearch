# Step 6: Question History Tracking & Multi-User Isolation

**Status:** Implemented. Per-session JSON history, in-session chat display, document-scoped restore, retention cleanup, and a command-line inspection tool are in place. The sidebar history panel is not implemented.

## Goal

Keep a record of each successful question and answer together with its metrics (timing, retrieval, tokens, temperature), so that:

- the user can see their conversation for the document they are working on,
- the conversation survives a page refresh within the same browser session and can be restored when the same document is uploaded again,
- an administrator can inspect and export history without running the web app,
- one browser session never sees another session's history.

## Design Decisions

| Decision | Rationale |
|---|---|
| One JSON file per browser session (`history/user_{session_id}.json`) | Isolation comes from separate files and from Streamlit's own per-session state. No authentication layer is needed. |
| Random session ID (`uuid4().hex`) created once per Streamlit session | A browser refresh or a new visit starts a new session and a new file. |
| Two layers: `st.session_state.chat_history` and the disk file | The in-memory list gives instant display and survives Streamlit reruns; the disk file gives persistence across reruns of the server process and feeds the CLI. |
| Store all questions, filter by document in the UI | No data is lost when the user switches documents; each view only shows the relevant subset. |
| Only successful provider answers are logged | Simulated and failed responses are not charged, stored, or shown as history. |
| Atomic writes via `write_json_atomic` | A crash during a write cannot leave a truncated history file. |
| File-based storage, no database | Files are easy to inspect, back up, and delete. A database is listed as a future option. |

## How It Works

1. **Session start.** On the first run of a Streamlit session, `app_pages/home.py` generates a session ID, stores it in `st.session_state.session_id`, and creates a `HistoryManager` for it. The `HistoryManager` constructor creates the `history/` directory if it does not exist.
2. **Retention cleanup.** On each run, the app calls a cached function that runs the retention cleanup at most once per hour per server process. It removes stale history and feedback files (see [Retention cleanup](#retention-cleanup)).
3. **Document upload.** When a document is uploaded, the app loads up to `HISTORY_LIMIT` past entries for that document name from disk and prepends them to `chat_history`. A set named `loaded_docs` makes sure this happens only once per document in a session.
4. **Question answered.** The chat handler runs the Hybrid query. If `response_status` is `"success"`, the cost tracker is charged and `log_to_history()` is called.
5. **Logging.** `log_to_history()` builds an entry with an ISO 8601 timestamp, the question, the raw answer, the mode, the document name, and a `metrics` object. It appends the entry to `chat_history` first and then calls `HistoryManager.add_question()`, which appends it to the session file. A failure while writing to disk is printed and does not stop the UI.
6. **Display.** `render_chat_history()` keeps only the entries whose `document_name` matches the current upload and renders them as chat bubbles. The per-document aggregate metrics block reads the same data from disk through `get_recent_questions()`.
7. **Reading.** `load_session_history()` reads the whole file and returns it sorted newest first. `get_recent_questions()` applies an optional document filter and a limit to that result.

### Stored entry format

Each entry in `history/user_{session_id}.json` has these keys:

- `timestamp`: local time in ISO 8601 format
- `question`, `answer`, `mode`, `document_name`
- `metrics`: `total_seconds`, `retrieval_seconds`, `generation_seconds`, `chunk_count`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `temperature`, `langsmith_run_id`, `picture_description_used`

The file is a JSON array in append order, so the oldest entry is first.

## Session Isolation

- Each browser session has its own `st.session_state`, its own `HistoryManager`, and its own file.
- A refresh or a new browser window creates a new session ID and therefore a new, empty history. Old files remain on disk until cleanup removes them.
- Concurrent sessions never write to the same file.
- Cleanup removes whole files, so it does not change any other session's data.

## Document Filtering

- Questions from all documents in a session are stored together.
- The chat view, the aggregate metrics, and the restore step all filter by `document_name`.
- The sidebar is not used for history. `render_history_sidebar()` is a placeholder that does nothing.

## Retention Cleanup

`HistoryManager.cleanup_old_sessions(retention_days)` scans `history/` and processes files whose names start with `user_`:

- Files that contain an empty list are deleted.
- Files that cannot be read or parsed as JSON are skipped.
- Files whose first entry has a timestamp older than the cutoff are deleted.

The web app runs this from a function decorated with `st.cache_resource(ttl=3600)`, so the directory scan happens at most once per hour per server process instead of on every rerun. The same function also runs feedback cleanup with `FEEDBACK_RETENTION_DAYS` (see [STEP_8_FEEDBACK_COLLECTION.md](STEP_8_FEEDBACK_COLLECTION.md)).

## Error Handling and Fallbacks

- **Corrupt or unreadable session file.** `_load_json()` returns an empty list, so the app keeps running. The next save then replaces the file with only the new entry. See Limitations.
- **Disk write failure.** `_save_json()` catches `IOError` and prints a message. The entry remains in `chat_history` for the current session.
- **Unexpected errors while logging.** `log_to_history()` catches all exceptions, prints the traceback to stderr, and returns, so the chat answer is still shown.
- **History disabled.** With `HISTORY_ENABLED=false`, logging, restore, aggregate metrics, and cleanup are all skipped. The `HistoryManager` object is still created, and the `history/` directory is still created.
- **Failed or simulated answers.** These are not logged, charged, or stored.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `HISTORY_ENABLED` | `true` | Enables logging, restore, aggregate metrics, and cleanup. Accepts `true`, `1`, or `yes` (case-insensitive). |
| `HISTORY_RETENTION_DAYS` | `30` | Age in days after which a session file is deleted during cleanup. |
| `HISTORY_LIMIT` | `10` | Maximum number of entries loaded from disk per document and used for aggregate metrics. |

These are listed in `.env.example`. On Streamlit Cloud, set them in the app secrets (see [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md)).

## Command-Line Tool

`src/history_cli.py` works on the same files. Run it from the repository root:

```powershell
python -m src.history_cli list --document contract.pdf
```

Subcommands:

- `list [--session ID] [--document NAME]` prints entries grouped by session, with their index in file order.
- `show --session ID --index N` prints the full question, answer, and metrics for one entry.
- `export [--output FILE] [--session ID] [--document NAME]` writes a CSV file (default `history_export.csv`) with the timestamp, session ID, document, mode, question, answer, and the metric fields listed above, except `langsmith_run_id` and `picture_description_used`.
- `cleanup [--days N]` runs the same cleanup as the web app, with a default of 30 days.

`--session` takes the bare session ID (the hexadecimal part of the file name), not the `user_` prefix. `show` uses the index in file order, which is the same order that `list` prints.

## Testing

Run the history tests from the repository root:

```powershell
python -m test_src.test_history
```

The script removes its own test files before and after the run. It covers:

- add and load of a single entry,
- ordering of several entries (newest first),
- document filtering and the limit on `get_recent_questions()`,
- isolation between two session IDs,
- a Streamlit `AppTest` check that two app sessions get different session IDs,
- the JSON structure and ISO 8601 timestamps,
- cleanup of old session files,
- atomic writes that leave the original file intact when serialization fails.

Browser behavior (restore on re-upload, switching documents, refresh) is checked by hand. Manual checks:

- ask a question, refresh the browser, and confirm a new session starts with no history,
- upload a second document and confirm the chat view shows only that document's questions,
- run `python -m src.history_cli list` and confirm the entries appear.

## Limitations

- **Sidebar panel not implemented.** The chat view is the only in-app display of history.
- **Display order.** `render_chat_history()` iterates `reversed(chat_history)`, so the most recent turn of the current session is shown first. Entries restored from disk are placed before the in-session entries and are shown oldest first after the session turns. The order is not strictly chronological after a restore.
- **Retention uses the first entry in the file.** Because the file is in append order, the first entry is the oldest. A session is deleted when its oldest entry is past the cutoff, even if later entries are recent.
- **Corrupt file is overwritten.** If a session file cannot be parsed, it is treated as empty and the next save replaces it.
- **No locking across processes.** Each session writes only its own file, but the CLI and the web app can read a file at the same time as it is replaced. The atomic write prevents partial files, not lost updates from parallel writers.
- **Deployment storage.** Files live on the server's local disk and are not durable across Streamlit Cloud instance replacement.
- **Scale.** Each save rewrites the full session file. This is fine for typical session sizes, but a database would be needed for high volume.

## Related Files

| File | Purpose |
|---|---|
| [src/history_manager.py](../src/history_manager.py) | `HistoryManager`: file I/O, filtering, cleanup |
| [src/history_cli.py](../src/history_cli.py) | Command-line list, show, export, and cleanup |
| [src/json_io.py](../src/json_io.py) | `write_json_atomic()` used for every save |
| [app_pages/home.py](../app_pages/home.py) | Session setup, logging, restore, chat display, cleanup scheduling |
| [src/gdpr_compliance.py](../src/gdpr_compliance.py) | Export and deletion of a session's history on request |
| [test_src/test_history.py](../test_src/test_history.py) | History tests |
| [.env.example](../.env.example) | Example values for the history variables |

## Related

- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md): source of `response_status` and the answer fields that are logged
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): source of the timing, retrieval, and token metrics
- [STEP_8_FEEDBACK_COLLECTION.md](STEP_8_FEEDBACK_COLLECTION.md): feedback is stored per session and shares the cleanup schedule
- [STEP_10_COST_TRACKING.md](STEP_10_COST_TRACKING.md): cost is charged only for logged successful answers
- [STEP_11_GDPR_COMPLIANCE.md](STEP_11_GDPR_COMPLIANCE.md): export and deletion of a session's history
- [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md): environment and secrets for the history variables
