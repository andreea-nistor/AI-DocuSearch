# Step 9: Internationalization

> **Current status:** Implemented. The app offers two UI languages, English and Romanian. The user picks one on the start screen before the consent notice. Automatic language detection and the French, Spanish, and German translations from the original plan were not implemented.

## Overview

The application is bilingual. Every user-facing string in the Home page, the GDPR consent flow, and the legal pages is looked up through a single translation helper. Romanian users also get Romanian legal documents. The LLM is instructed to answer in the language of the question, so the answer language follows the user's question even when the UI language differs.

## Goals

- Offer English and Romanian UI text with a simple, explicit choice made by the user.
- Keep all translated strings in one place so new text can be added without touching page layout code.
- Keep the chosen language stable across Streamlit reruns.
- Serve Romanian legal documents when they exist, with English as the binding fallback.
- Make the LLM answer in the question's language, independent of the UI language.

## Design Decisions

- **Explicit choice over detection.** The language is chosen by the user on the first screen. Browser `Accept-Language` headers and IP geolocation were considered and removed. Explicit choice avoids inaccurate guesses, avoids an external geolocation call, and avoids processing the user's IP address for a cosmetic setting.
- **Dictionary-based translation.** `TRANSLATIONS` in [src/i18n.py](../src/i18n.py) maps language codes to string keys. `translate()` looks up the key in the active language, falls back to English, then to a caller-supplied default, and finally to the key itself. Missing translations therefore degrade to English rather than failing.
- **Session state as the source of truth.** The choice is stored in `st.session_state` under `user_language`, with a separate flag `user_language_chosen` that records that the user has actively selected a language. Streamlit reruns therefore keep the same language without repeating the gate.
- **Language-matched legal documents.** Each legal page reads its Markdown from `Policies/`. The Romanian version is used when a `.ro.md` file exists, otherwise the English file is shown. The English texts are the binding versions.
- **Prompt-level language control.** Translation covers only UI text. Document content and LLM answers are not translated. The prompts in `prompts/` tell the model to respond in the language of the question.

## How the Flow Works

1. A new Streamlit session has no `user_language_chosen` flag, so `show_language_selector()` in [src/i18n.py](../src/i18n.py) renders a bilingual prompt with an "English" and a "Română" button.
2. Clicking a button calls `set_language()`, which validates the code against `SUPPORTED_LANGUAGES`, stores it in `st.session_state`, and sets the chosen flag. Unsupported codes raise `ValueError`.
3. [app_pages/home.py](../app_pages/home.py) calls `st.stop()` until a language is chosen. The consent banner from [src/gdpr_compliance.py](../src/gdpr_compliance.py) is then shown in the selected language.
4. After consent, all Home page text, metric labels, feedback buttons, and error messages are rendered through `translate()`.
5. The Privacy Policy, Terms of Service, and Third-Party Services pages call `read_legal_document()`, which selects the Romanian or English Markdown file.
6. When a question is asked, the prompt templates in `prompts/rag_prompt.txt` and `prompts/direct_llm_prompt.txt` include the instruction to answer in the question's language. Both prompts also receive `document_info`, a string such as `Document: <name> | Pages: <n>`, so the model can answer questions about the file name and page count.

## Translation Scope

Translated in the current implementation:

- Page title, description, budget notice, and upload prompts
- Extraction, processing, and error messages
- Metric labels and the detailed timing expander
- Feedback buttons and confirmation messages
- Picture interpretation messages (when multimodal mode is enabled)
- Consent banner, GDPR data controls, and navigation links
- Legal page navigation and the Romanian legal documents

Not translated:

- Document content
- LLM answers (these follow the question's language through the prompt instruction)

## Configuration

No environment variables control internationalization. The supported languages are fixed in `SUPPORTED_LANGUAGES` in [src/i18n.py](../src/i18n.py). The default language, `DEFAULT_LANGUAGE`, is English and is used when no choice has been stored.

## Error Handling and Fallbacks

- A missing translation key falls back to the English string, then to the default argument, then to the key name. The UI does not crash on a missing key.
- `set_language()` rejects unsupported codes with `ValueError`.
- `read_legal_document()` falls back to the English Markdown when the Romanian file is absent.
- Before a language is chosen, `get_user_language()` returns English, so helper functions are safe to call early.

## Adding a Language

Adding a language requires three changes in [src/i18n.py](../src/i18n.py):

- Add an entry to `TRANSLATIONS` with every key used by the UI. Keys missing from the new entry fall back to English.
- Add the code and display name to `SUPPORTED_LANGUAGES`.
- Add a selector button in `show_language_selector()`.

Legal documents for a new language use the `<name>.<code>.md` naming pattern in `Policies/`. The LLM already responds in the question's language, so prompt changes are not required.

## Tests

- [test_src/test_legal_pages.py](../test_src/test_legal_pages.py) covers the language gate (both buttons set the expected session state) and navigation to the legal pages in English.

Run it from the repository root:

```powershell
python -m test_src.test_legal_pages
```

Romanian legal page rendering and the translation fallback behavior do not have dedicated tests in the repository.

## Limitations

- Only English and Romanian are supported. Adding languages is manual.
- Language choice is per session, so a user must pick a language again in a new browser session.
- Translation coverage is not audited for every string. Some UI text may still be English-only.
- The LLM answer language depends on the model following the prompt instruction. This is not guaranteed.
- Romanian legal documents must be kept in sync with the English versions by hand.

## Related Files

- [src/i18n.py](../src/i18n.py): translation dictionary, language state, selector, and legal document loader
- [app_pages/home.py](../app_pages/home.py): language gate and translated Home page
- [app_pages/privacy_policy.py](../app_pages/privacy_policy.py), [app_pages/terms_of_service.py](../app_pages/terms_of_service.py), [app_pages/third_party_services.py](../app_pages/third_party_services.py): legal pages
- [src/gdpr_compliance.py](../src/gdpr_compliance.py): translated consent banner and data controls
- [prompts/rag_prompt.txt](../prompts/rag_prompt.txt) and [prompts/direct_llm_prompt.txt](../prompts/direct_llm_prompt.txt): answer-language instruction
- [Policies/](../Policies/): English and Romanian legal documents
- [test_src/test_legal_pages.py](../test_src/test_legal_pages.py): language gate and navigation tests

## Related

- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md): LLM calls and prompt loading
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): pipeline that produces the answer
- [STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md](STEP_7_STREAMLIT_CLOUD_DEPLOYMENT.md): deployment of the Streamlit app
- [STEP_11_GDPR_COMPLIANCE.md](STEP_11_GDPR_COMPLIANCE.md): consent banner and legal pages
