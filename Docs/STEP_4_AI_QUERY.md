# Step 4: AI Query and Answer Generation

This step sends a prepared prompt to a language model and turns the provider's reply into a result
the rest of the application can trust. The core logic lives in
[src/ai_query.py](../src/ai_query.py). Every answer comes back with a `response_status` that
decides whether the Streamlit app may display it as a real answer, count its cost, save it to
history, or accept a rating.

## Goals

- Work with any OpenAI-compatible `/chat/completions` endpoint, not a single vendor.
- Never present a fake or failed response as a real answer.
- Report timing and token usage for cost tracking, even when the provider omits usage data.
- Stay usable without credentials, so local development and the test suite run offline.
- Keep tracing (LangSmith) optional and unable to break an answer.

## Design Decisions

- **One public function.** `generate_answer_with_meta()` returns a dictionary containing the answer
  and all metadata. The RAG pipeline, the Direct LLM path, the Hybrid path, and picture
  interpretation all use it, so they share one response contract.
- **Explicit response states.** Three states are possible: `success`, `simulated`, and `error`.
  Only `success` is treated as a real answer by the UI.
- **Generic configuration first.** The `LLM_*` variables are the documented settings. The `OPENAI_*`,
  `XAI_*`, and `GROK_*` names remain as fallbacks for older setups.
- **Plain HTTP.** The request is a direct `requests.post` call with a 60-second timeout. There is no
  provider SDK dependency and no retry loop.
- **Prompts live outside Python.** Templates are in [prompts/](../prompts/), and their sampling
  temperature is set by an optional first-line directive (see [src/prompt_loader.py](../src/prompt_loader.py)).

## How the Flow Works

1. **Resolve temperature.** An explicit `temperature` argument wins. Otherwise `LLM_TEMPERATURE` is
   used, and if that is unset the default is `0.2`.
2. **Resolve provider settings.** The API key, base URL, and model are read from the environment
   using the precedence in the configuration table below. If `OPENAI_API_KEY` is set without a base
   URL, the base URL defaults to `https://api.openai.com/v1`.
3. **Check completeness.** A live request is attempted only when the API key, base URL, and model
   are all present. Otherwise the function takes the simulated path (step 7).
4. **Start a trace run (optional).** If LangSmith is configured, a run is created before the request
   (see LangSmith Tracing below).
5. **Build the request.** The payload contains the model, a system message, a user message, and the
   temperature. The system message is a fixed safety preamble that tells the model that document
   content, picture descriptions, and images are untrusted data, not instructions. Text-only
   requests send the prompt as a string. When images are supplied, the user message becomes a list
   of text and `image_url` parts that carry base64 data URLs.
6. **Call the provider.** The request is posted to `{base URL}/chat/completions`. The answer is read
   from `choices[0].message.content`. Any exception, including network errors, timeouts, HTTP error
   statuses, malformed JSON, or an unexpected response shape, is caught and turned into an `error`
   result.
7. **Simulated path.** When configuration is incomplete, no request is sent. The function returns a
   preview beginning with `[SIMULATED ANSWER]`, built from the first 100 characters of the prompt,
   and marks it as an estimate.
8. **Account for tokens.** On success, the provider's `usage` values are used. If prompt or
   completion tokens are missing or zero, they are estimated as roughly one token per four
   characters. The `estimated_tokens` flag is set when any estimate was used.
9. **Close the trace run (optional).** The run is updated with the outputs on success, or with the
   error message on failure.
10. **Return the result.** The dictionary is returned with the fields listed in the Response Contract
    section.

## Configuration

| Variable | Purpose | Notes |
|---|---|---|
| `LLM_API_KEY` | Bearer token for the provider | Fallbacks: `OPENAI_API_KEY`, `XAI_API_KEY`, `GROK_API_KEY` |
| `LLM_API_BASE` | Base URL of the OpenAI-compatible API | Fallbacks: `OPENAI_API_BASE`, `XAI_API_BASE`, `GROK_API_BASE`; defaults to OpenAI's URL when only `OPENAI_API_KEY` is set |
| `LLM_MODEL` | Chat model for text requests | Fallbacks: `OPENAI_MODEL`, `XAI_MODEL`, `GROK_MODEL` |
| `VISION_MODEL` | Model used when images are attached | Falls back to `LLM_MODEL` when unset |
| `LLM_TEMPERATURE` | Default sampling temperature | Used when no argument or prompt directive sets one; default `0.2` |
| `LANGSMITH_TRACING` | Enables tracing when set to `true` | Tracing also needs `LANGSMITH_API_KEY` |
| `LANGSMITH_API_KEY` | LangSmith credential | Optional |
| `LANGSMITH_PROJECT` | LangSmith project name | Defaults to `default` |
| `LANGSMITH_FEEDBACK_ENABLED` | Allows user ratings to be sent to LangSmith | Defaults to enabled; read by [src/langsmith_feedback.py](../src/langsmith_feedback.py) |

Example of a minimal provider setup (values are placeholders):

```env
LLM_API_KEY=your_key_here
LLM_API_BASE=https://api.example.com/v1
LLM_MODEL=your-model-name
```

Real values belong in `.env` locally or in Streamlit Cloud secrets. Both are excluded from source
control. See [.env.example](../.env.example) for the list of variables the project expects.

### Temperature Precedence

For callers that load a prompt file, the order is:

1. A `# temperature: <value>` directive on the first line of the prompt file
2. `LLM_TEMPERATURE`
3. `0.2`

The directive is passed to `generate_answer_with_meta()` as its explicit argument, so it overrides
the environment variable. The directive line is removed before the prompt is sent. Both current
templates set `0.4`.

## Response Contract

`generate_answer_with_meta()` always returns these keys:

| Key | Meaning |
|---|---|
| `answer` | Provider text, a `[SIMULATED ANSWER]` preview, or an empty string on error |
| `elapsed_seconds` | Wall-clock time spent in the function |
| `response_status` | `success`, `simulated`, or `error` |
| `error_type` | `None` on success, `configuration_missing`, or the name of the exception class |
| `error_message` | Exception text, the configuration message, or `None` |
| `used_live_api` | `True` only for a successful provider call |
| `langsmith_run_id` | Trace run ID as a string, or `None` |
| `prompt_tokens`, `completion_tokens`, `total_tokens` | Token counts |
| `estimated_tokens` | `True` when any count was estimated |
| `temperature` | Temperature actually used |

The three states behave as follows in the app:

- **success:** the answer is displayed, counted toward cost, saved to history, and can be rated.
- **simulated:** a warning is shown with the preview. Nothing is counted, saved, or rated. Token
  values are estimates.
- **error:** an error message and a retry hint are shown. The answer is empty, token counts are
  zero, and nothing is counted, saved, or rated.

Zero tokens on an error describe the app's accounting only. The provider may still bill for work
done before the failure, so the provider dashboard is the source of truth for charges.

## Prompt Templates

| Template | Placeholders | Used by |
|---|---|---|
| `prompts/rag_prompt.txt` | `{context}`, `{question}`, `{document_info}` | RAG path in [src/pipeline.py](../src/pipeline.py) |
| `prompts/direct_llm_prompt.txt` | `{document_text}`, `{question}`, `{document_info}` | Direct LLM path in [app_pages/home.py](../app_pages/home.py) |
| `prompts/picture_description_prompt.txt` | `{document_info}`, `{page_label}` | [src/visual_ingest.py](../src/visual_ingest.py) |

Both text templates ask the model to answer in the same language as the question, wrap the document
in `<document>` tags, and state that the document is untrusted. Before substitution,
[src/prompt_loader.py](../src/prompt_loader.py) replaces any literal `<document>` or `</document>`
inside the substituted text with look-alike characters, so document content cannot close the
boundary early.

## Multimodal Requests

Picture interpretation calls the same function with `images=[data_url, ...]`. The model is taken from
`VISION_MODEL`, and the request uses the content-part format. The picture-description workflow is
described in [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md). Calls without
images are unchanged.

## LangSmith Tracing

Tracing runs only when `LANGSMITH_TRACING` is `true` and `LANGSMITH_API_KEY` is set. The code does
not use the `@traceable` decorator for this function. Instead it manages the run directly:

- A run named `generate_answer` is created before the provider request, with the question (trimmed),
  prompt length, model, and image count as inputs.
- After the call, the run is updated with the answer preview and token counts on success, or with
  the error text on failure.
- The client uses a 5-second connect timeout and a 10-second read timeout.
- The run ID is returned to the app so that a Helpful or Not helpful rating can be attached to the
  same run. Ratings are sent only when `LANGSMITH_FEEDBACK_ENABLED` is not turned off.

Any failure in tracing is logged to standard error and does not change the answer or its status.

## Integration

- [src/pipeline.py](../src/pipeline.py) passes the full result through `answer_question()`, adding
  retrieval details such as the chunk count and requested PDF pages.
- In the Hybrid mode of [app_pages/home.py](../app_pages/home.py), a RAG result whose status is not
  `success` is returned immediately. The app does not fall back to the Direct LLM path in that case.
  The fallback runs only when RAG succeeds but its answer is judged inconclusive, and never for an
  explicit page request.
- Cost tracking and history logging happen only for `success`. Feedback is offered only on stored
  history entries, so it follows the same rule.

## Error Handling and Fallbacks

- **Missing configuration:** the simulated path runs, and the app shows the preview as a warning.
  This keeps the interface usable during setup.
- **Provider failure:** any exception produces an `error` result with an empty answer. The failure is
  never stored as if it were an answer.
- **Tracing failure:** logged and ignored.
- **Usage missing from the provider:** token counts are estimated, and the flag is set.
- **Empty or unavailable context:** handled upstream in the pipeline, which can return a clear
  "page unavailable" prompt rather than sending unrelated text.

## Tests

The test module is [test_src/test_ai_query.py](../test_src/test_ai_query.py). Run it from the
repository root:

```powershell
python -m test_src.test_ai_query
```

The tests mock `requests.post` and the LangSmith client, so no network access is needed. They cover:

- A successful provider response is marked `success` and its token usage is reported.
- A request exception is marked `error`, returns an empty answer, and reports zero tokens.
- Missing configuration returns an explicit `simulated` result.
- The pipeline propagates a provider failure state unchanged.
- Page requests select the exact PDF page, support ranges, and are capped at five pages.
- Picture descriptions are disclosed as AI-generated in the prompt and the result.
- A literal `</document>` in document text cannot break the prompt boundary.
- In the Streamlit app, a provider failure is not saved to chat history or history storage.
- In the Streamlit app, a Hybrid page request does not fall back to the full document.
- Chat history escapes HTML from questions and answers.
- The cost budget limit blocks new questions.

The Streamlit tests run the real app through Streamlit's test harness, so Streamlit must be
installed in the environment.

## Limitations

- **No retries or streaming.** One request is made per call, with a fixed 60-second timeout that
  cannot be changed through configuration.
- **Token counts are approximate** when the provider omits usage data. The one-token-per-four-characters
  estimate is rough, especially for non-English text.
- **Errors report zero tokens**, which may understate real provider usage.
- **Error types are exception class names**, not HTTP status codes, so the app cannot distinguish
  an authentication failure from a rate limit.
- **Only the chat completions format is supported.** Providers that use a different response shape
  will produce an error result.
- **Prompt-injection protection is best effort.** The system preamble and the document-tag
  neutralization reduce risk but cannot guarantee that a model will ignore malicious text.
- **Unused import.** The module still imports `traceable` as a fallback, but this function does not
  use it.

## Related

- [STEP_1_INGEST.md](STEP_1_INGEST.md): text extraction that produces the document content
- [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md): chunking and page markers
- [STEP_3_EMBEDDING_INDEXING.md](STEP_3_EMBEDDING_INDEXING.md): retrieval used before generation
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): how RAG, Direct LLM, and Hybrid use this step
- [STEP_6_HISTORY_TRACKING.md](STEP_6_HISTORY_TRACKING.md): where successful answers are saved
- [STEP_8_FEEDBACK_COLLECTION.md](STEP_8_FEEDBACK_COLLECTION.md): ratings and LangSmith feedback
- [STEP_10_COST_TRACKING.md](STEP_10_COST_TRACKING.md): how token counts become cost
- [STEP_12_PICTURE_INTERPRETATION.md](STEP_12_PICTURE_INTERPRETATION.md): multimodal requests
