# Step 10: Cost Tracking and Budget Management

Status: Implemented

## Goal

Step 10 gives users a visible estimate of how much of the free testing allowance a session has used, and stops new questions once that allowance is exhausted. The allowance is a fixed $0.50 USD per browser session. The figures are an internal estimate based on token counts and fixed rates. They are not a billing record; the LLM provider's dashboard remains the authoritative source for actual charges.

## Design Decisions

- **Session-local state.** The tracker lives in `st.session_state` under the key `llm_cost_tracker`. Nothing is written to disk, so each new browser session starts with a fresh budget. This is deliberate for the free testing trial.
- **Fixed, provider-independent rates.** The rates are constants in the cost tracker module and are not read from `LLM_MODEL` or the configured provider. They are described in the code as placeholder estimates until per-provider pricing is implemented.
- **Only real answers are charged.** Costs are added only when a query returns `response_status == "success"`. Simulated answers and provider failures are never charged, stored in history, or rated.
- **Enforcement at the page level.** When the budget is exhausted, the Home page stops rendering before the chat input, so no further question can be submitted.
- **Module-level helpers, no class.** The tracker is a set of functions over one session-state dictionary, which keeps the Streamlit page code short.

## Pricing Constants

| Constant | Value | Meaning |
|----------|-------|---------|
| `ASSUMED_INPUT_COST_PER_1K` | 0.03 | USD per 1,000 prompt tokens |
| `ASSUMED_OUTPUT_COST_PER_1K` | 0.10 | USD per 1,000 completion tokens |
| `FREE_BUDGET_USD` | 0.50 | Budget per session |
| `WARNING_THRESHOLD` | 0.80 | Warning shown at 80% of budget |
| `BLOCK_THRESHOLD` | 1.00 | Defined in the module, but blocking is currently triggered by `track_query_cost()` when the total reaches `FREE_BUDGET_USD` |

The cost of one query is `(prompt_tokens / 1000) * 0.03 + (completion_tokens / 1000) * 0.10`. For example, 1,500 prompt tokens and 200 completion tokens cost about $0.065, so the default budget covers roughly 25 such questions. The same arithmetic applies to picture-interpretation calls (see [STEP 12](STEP_12_PICTURE_INTERPRETATION.md)).

## How the Flow Works

1. **Initialization.** On each run, the Home page calls `initialize_cost_tracker()`. This creates the session dictionary (total cost, query count, query log, blocked flag) only if it does not already exist.
2. **Budget display.** Before the chat area, the page shows a budget notice, a link to the feedback form, and a cost badge. The badge shows the percentage of budget used, with a green, warning, or stop emoji depending on the level. The feedback link is hidden once the budget is blocked.
3. **Warning.** When the usage percentage reaches 80% and the budget is not yet blocked, the page shows a "nearly complete" warning.
4. **Charging a query.** After a Hybrid-mode answer, the page checks `response_status`. Only on `success` does it call `track_query_cost()` with the prompt and completion token counts. That call computes the cost, updates the total and count, appends an entry to the query log (timestamp, tokens, cost), and sets `blocked` once the total reaches $0.50.
5. **Picture interpretation.** When multimodal picture interpretation runs during upload, its aggregated prompt and completion tokens are also charged through the same function, provided the counts are non-zero.
6. **Blocking.** On the next run, `is_blocked()` returns `True`. The page shows a trial-complete message and a feedback link, then stops rendering. The chat input is not shown.

Because the page re-evaluates these checks on every rerun, the badge and warning update immediately after each answer.

## Token Counts

Token counts come from `generate_answer_with_meta()` in [src/ai_query.py](../src/ai_query.py). The provider's `usage` values are used when present. If the provider omits them (reported as zero), the code uses a rough estimate of about four characters per token and marks the result as estimated. Failed provider calls return zero tokens. Simulated answers (no API configuration) use the same estimate but are not charged because their status is not `success`.

## Session State

The dictionary stored under `llm_cost_tracker` has these keys:

- `total_cost_usd`: cumulative estimated spend
- `queries_count`: number of charged queries
- `queries`: list of entries with `timestamp`, `prompt_tokens`, `completion_tokens`, and `cost_usd`
- `blocked`: whether the budget has been exhausted

Helper functions also expose the remaining budget, the usage percentage, and a detailed breakdown. The `reset_cost_tracker()` function can clear the dictionary, but no page currently calls it.

## Configuration

Cost tracking has no environment variables. The rates and budget are code constants in [src/cost_tracker.py](../src/cost_tracker.py). Changing them requires a code change and redeploy.

## Error Handling and Fallbacks

- A failed or unconfigured LLM call never reaches the tracker, so users are not charged for errors.
- If the Hybrid path returns a non-success status, the answer is not logged to history and no feedback is attached.
- Budget checks rely only on session state, so they do not depend on external services.
- In the GDPR export, cost data is read inside a `try` block. A failure there is logged and the rest of the export still runs.

## Privacy and GDPR

The GDPR export ([src/gdpr_compliance.py](../src/gdpr_compliance.py)) includes a `cost_tracking` section with total cost, remaining budget, budget percentage, and query count. The export also records a hard-coded budget limit of $0.50. Cost data is not stored on the server, so it disappears when the browser session ends. The Google Forms feedback link opens in a new tab and is not connected to the local feedback storage.

## Internationalization

The budget notice, warning, and blocked messages are translated through [src/i18n.py](../src/i18n.py). The current translations cover English and Romanian only. The budget notice states the approximate number of questions for a 100-page document.

## Tests

Run the tests from the repository root:

```powershell
python -m test_src.test_ai_query
```

- `test_streamlit_budget_limit_blocks_chat_input` in [test_src/test_ai_query.py](../test_src/test_ai_query.py) loads the app with Streamlit's `AppTest`, sets the tracker to a blocked state, and checks that the trial-complete message, the feedback link, and the absence of chat input are shown.

No dedicated unit test exists for the arithmetic in `calculate_query_cost()` or `track_query_cost()`. Those functions are verified only indirectly.

Manual check: open the app, ask several questions, confirm the badge and warning appear near 80%, and confirm questions are blocked at 100%.

## Limitations

- **Estimate only.** Rates are fixed placeholders and do not match any specific provider or model. Actual billing can differ.
- **Per-session budget.** Users can open a new session to get a new budget. There is no account-level or server-side limit.
- **No paid tier.** The app has no mechanism to raise the limit.
- **Approximate token estimates.** The four-characters-per-token fallback is rough, especially for non-English text.
- **Reset is not wired.** `reset_cost_tracker()` exists but no UI path calls it.

## Related Files

- [src/cost_tracker.py](../src/cost_tracker.py): tracker logic and constants
- [app_pages/home.py](../app_pages/home.py): initialization, badge, warning, blocking, and charging
- [src/ai_query.py](../src/ai_query.py): token metadata and response status
- [src/gdpr_compliance.py](../src/gdpr_compliance.py): cost data in the data export
- [src/i18n.py](../src/i18n.py): budget messages
- [test_src/test_ai_query.py](../test_src/test_ai_query.py): budget-blocking test

## Related

- [STEP 4: AI Query](STEP_4_AI_QUERY.md): the LLM call that produces token counts
- [STEP 5: Pipeline](STEP_5_PIPELINE.md): the Hybrid flow that returns the result dictionary
- [STEP 11: GDPR Compliance](STEP_11_GDPR_COMPLIANCE.md): data export that includes cost data
- [STEP 12: Picture Interpretation](STEP_12_PICTURE_INTERPRETATION.md): vision calls that are also charged
