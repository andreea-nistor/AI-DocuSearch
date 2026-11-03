# Step 11: GDPR Compliance & Legal Framework

**Status:** Experimental privacy controls. These are technical controls for privacy obligations and are not a legal compliance certification. Legal and security review is required before production use.

## Overview

Step 11 adds the consent gate, local data export, local data deletion, and in-app legal pages to AI DocuSearch. The goal is to make the data flow visible to users before any document is processed and to give them simple controls over the data the app stores for their browser session.

The implementation has three parts:

- A consent notice that blocks the app until the user accepts it.
- A footer with data management controls (download, delete) and links to the legal pages.
- Three legal pages (Privacy Policy, Terms of Service, Third-Party Services) rendered from Markdown files in `Policies/`.

All of the code for this step lives in [src/gdpr_compliance.py](../src/gdpr_compliance.py), with the page wiring in [app_pages/home.py](../app_pages/home.py) and [web_app.py](../web_app.py).

## Goals

- Obtain consent before any document is processed.
- Let the user export their session data as portable JSON (access and portability).
- Let the user delete the history and feedback files that the app stores for their session (erasure).
- Disclose third-party data sharing in plain language.
- Keep the legal text in versioned Markdown so it can be reviewed and edited without touching code.

## Design Decisions

- **Session-scoped identity.** Each Streamlit session gets a random UUID hex identifier on first load. Export and deletion act only on the files named after that identifier, so one user cannot read or delete another session's data through the UI.
- **Consent is a session flag, not a stored record.** The acceptance is kept in `st.session_state` and survives reruns, but it is not written to disk. A page refresh or new browser session asks again.
- **Gate in the page flow, not in each feature.** The consent check runs early in `app_pages/home.py`, after the language choice and before the upload and question controls render. Nothing downstream needs to check consent again.
- **Footer instead of sidebar.** The data controls sit in a footer that renders on every page load. The old sidebar function still exists only as a no-op for backward compatibility.
- **Legal pages as dedicated Streamlit pages.** Privacy Policy, Terms of Service, and Third-Party Services are registered as hidden pages in `web_app.py`, so links stay inside the app rather than opening external files.
- **Markdown source with a Romanian variant.** `src/i18n.py` reads `Policies/<NAME>.md` and prefers `Policies/<NAME>.ro.md` when the user chose Romanian.

## How the Flow Works

1. **Language choice.** The start screen asks for English or Română. The consent notice is shown in the chosen language.
2. **Consent gate.** `show_consent_banner()` checks `gdpr_consent_given` in session state. If it is not `True`, the banner shows the processing notice, links to the Privacy Policy and Terms of Service, and a single "I Agree & Continue" button. `home.py` calls `st.stop()` until the button is clicked, then the button sets the flag and reruns the page.
3. **Normal use.** Once accepted, uploads, questions, history logging, and cost tracking work as usual. The banner is not shown again for the rest of the session.
4. **Footer.** After the main content, `show_gdpr_footer()` renders the data management row, which contains:
   - **Download Data:** builds the export and reveals a download button for the JSON file.
   - **Delete Data:** shows a warning and a confirmation checkbox. Deletion runs only after the checkbox is ticked.
   - **Privacy Policy, Terms of Service, Third-Party Services:** page links.
   - A short list of the user's rights (text only, see Limitations).

### Data Export

`export_user_data(session_id, history_manager, feedback_manager)` builds a dictionary with:

- `export_date`, `session_id`, and `version` (`"1.0"`).
- `questions_and_answers`: one entry per history record, with timestamp, question, answer, document name, mode, and metrics.
- `feedback`: one entry per feedback record, with timestamp, rating, question, feedback type, comment, and document name.
- `cost_tracking`: total cost, remaining budget, budget percentage, query count, and the budget limit (USD 0.50).
- `metadata`: counts of questions and feedback entries, the export format, and a portability note.

Each part is read inside its own `try` block. If history, feedback, or cost data fails to load, the error is printed and the other sections are still exported with empty values.

The footer serializes the dictionary as UTF-8 JSON with indentation and offers it as `docusearch_data_<session_id>_<YYYYMMDD_HHMMSS>.json` with MIME type `application/json`.

### Data Deletion

`delete_user_data(session_id, history_manager, feedback_manager)` does the following:

1. Deletes `history/user_<session_id>.json` if a history manager is present and the file exists.
2. Deletes `feedback/user_<session_id>.json` if a feedback manager is present and the file exists.
3. Resets in-memory state: `chat_history` is emptied, and `document_text`, `rag_pipeline`, and `page_count` are set to `None`.
4. Returns `True`. Any exception is printed and the function returns `False`, and the footer shows an error message.

After a successful deletion the footer shows a success message and calls `st.rerun()`.

What is not cleared: the cost tracker for the session, the session identifier, the language choice, the consent flag, and any other Streamlit state keys. Data already sent to a third-party provider is not recalled by this step.

## Third-Party Data Sharing

| Service | Data sent | Purpose |
|---------|-----------|---------|
| Configured LLM provider | Document excerpts or full text (Direct LLM fallback), questions, and page images when picture interpretation is enabled | Answer generation and picture description |
| LangSmith | Traces and metrics, only when tracing is enabled | Debugging and monitoring |
| Streamlit Cloud | App data | Hosting |

The full disclosure is on the Third-Party Services page and in `Policies/THIRD_PARTY_SERVICES.md`. RAG answers send only the retrieved chunks to the LLM. The Direct LLM fallback can send the full extracted text.

## Configuration

Step 11 itself has no required settings. The related retention and tracing variables are:

| Variable | Default | Effect |
|----------|---------|--------|
| `HISTORY_ENABLED` | `true` | When false, history is not written, and the history retention cleanup is skipped. |
| `HISTORY_RETENTION_DAYS` | `30` | History files whose entries are all older than this are deleted by the hourly cleanup. |
| `FEEDBACK_RETENTION_DAYS` | `90` | Feedback files older than this (by file age) are deleted by the hourly cleanup. |
| `LANGSMITH_TRACING` | `false` when unset | Set to `false` to disable LangSmith tracing. |

The retention cleanup runs from `app_pages/home.py` through a Streamlit cache with a one-hour TTL, so the directory scan happens at most once per hour per server process.

## Error Handling and Fallbacks

- **Export errors:** each data source is isolated. A failure in cost, history, or feedback loading is logged and leaves that section empty instead of blocking the download.
- **Delete errors:** an exception stops the deletion and returns `False`, and the user sees an error message. Files already removed before the error stay removed.
- **Missing files:** deletion checks for existence before removing, so a session with no history or feedback completes without error.
- **Romanian legal text:** the English file is used when no `.ro.md` variant is available for a document.

## Tests

The repository has no dedicated unit tests for the export and deletion functions. The existing test that covers this step is:

```powershell
python -m test_src.test_legal_pages
```

It runs from the repository root and checks that:

- The start screen offers English and Română before the consent notice, and the chosen language is stored.
- The footer links to the Privacy Policy, Terms of Service, and Third-Party Services pages.
- Each legal page renders without an exception and shows its expected heading.

Other tests set `gdpr_consent_given` to `True` in session state so they can reach the main page. Export and deletion behavior is currently verified manually: accept the notice, ask a question, download the JSON, then delete the data and confirm the history file is gone.

## Limitations

- The consent notice blocks the whole app until accepted. There is no per-feature consent.
- Consent is not persisted across sessions or devices, so the notice appears again after a refresh.
- "Restrict processing" and "Object to tracking" appear as rights in the footer text, but no control implements them.
- Deletion does not reset the session cost tracker, and it cannot delete copies held by third-party providers or LangSmith.
- Email-based deletion requests, audit logs, and a data protection impact assessment are not implemented.
- The privacy contact details in the legal documents are placeholders that must be replaced before production use.

## Related

- [STEP_6_HISTORY_TRACKING.md](STEP_6_HISTORY_TRACKING.md): history files that export and deletion act on.
- [STEP_8_FEEDBACK_COLLECTION.md](STEP_8_FEEDBACK_COLLECTION.md): feedback files included in export and deletion.
- [STEP_9_INTERNATIONALIZATION.md](STEP_9_INTERNATIONALIZATION.md): language choice shown before the consent notice.
- [STEP_10_COST_TRACKING.md](STEP_10_COST_TRACKING.md): cost data included in the export.
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md): page images sent to the LLM provider, disclosed in the consent notice.
- [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md): hosting context for the third-party disclosure.
