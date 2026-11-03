"""
Internationalization (i18n) for AI DocuSearch.

Supported languages: English (en, default) and Romanian (ro). The user picks the language on the
start screen (show_language_selector) before the consent notice. Provides translate() and a helper
for the legal Markdown documents.
"""

from pathlib import Path
from typing import Optional
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POLICIES_DIR = PROJECT_ROOT / "Policies"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en": "English", "ro": "Română"}
LANGUAGE_CHOSEN_KEY = "user_language_chosen"

# Translation dictionary (English and Romanian only)
TRANSLATIONS = {
    "en": {
        "title": "AI DocuSearch",
        "description": "Your personal AI search engine for documents.\nUpload a PDF and instantly find the answers hidden inside — clauses, definitions, summaries, explanations.",
        "budget_info": "Try for FREE: you can ask ~25 questions on a ~100 page document. Larger documents will support fewer questions.",
        "upload_prompt": "Upload a PDF, DOCX or TXT file",
        "file_saved": "📁 File saved",
        "extracting": "⏳ Extracting text from document...",
        "extracted": "✅ Extracted",
        "chars": "chars",
        "mb": "MB",
        "pages": "pages",
        "in": "in",
        "seconds": "s",
        "ask_question": "Ask a question about the document...",
        "processing": "⏳ Processing your question...",
        "completed": "✅",
        "document_info": "Document Info",
        "positive": "Positive",
        "negative": "Negative",
        "upload_first": "👆 Please upload a document to get started",
        "failed_save": "❌ Failed to save file",
        "failed_extract": "❌ Failed to extract text",
        "ocr_note": "⚠️ **Note on scanned PDFs**",
        "ocr_tip": "📌 **Tip**: For best results, use PDFs with selectable text",
        "upload_prompt_multimodal": "Upload a PDF, DOCX, TXT, PNG, JPEG, or WebP file",
        "interpreting_pictures": "🖼️ Interpreting pictures with the vision model...",
        "picture_interpretation_incomplete": "🖼️ Picture interpretation was incomplete",
        "picture_pages_truncated": "🖼️ Only the first {count} pages were interpreted for pictures (MEDIA_MAX_PAGES).",
        "picture_descriptions_label": "picture description(s)",
        "no_text_or_pictures": "No text or picture descriptions could be extracted from this file.",
        "answer_includes_picture_description": "🖼️ This answer includes an AI-generated picture description.",
        "mobile_detected": "📱 **Mobile Device Detected**: Hybrid mode intelligently adapts to your device's capabilities. It will use fast, efficient processing optimized for mobile.",
        "share_feedback": "Share feedback",
        "share_feedback_help": "Open the AI DocuSearch testing feedback form in a new tab.",
        "trial_nearly_complete": "**Free testing trial nearly complete:** You are approaching the trial limit. Only a small amount of usage remains.",
        "trial_complete": "**Free testing trial complete:** Your free testing trial has ended. Please share your experience using the form below. Your feedback will help improve AI DocuSearch and is greatly appreciated.",
        "metric_total_time": "Total time",
        "metric_chunks_used": "Chunks used",
        "metric_context_size": "Context size",
        "metric_tokens_est": "Tokens (est.)",
        "metric_tokens_actual": "Tokens (actual)",
        "detailed_metrics": "Detailed timing & tokens",
        "metric_build_time": "Build/index time",
        "metric_retrieval_time": "Retrieval time",
        "metric_generation_time": "Generation time",
        "metric_temperature": "Temperature",
        "metric_prompt_tokens": "Prompt tokens",
        "metric_completion_tokens": "Completion tokens",
        "metric_live_api": "Live API used",
        "yes": "Yes",
        "no_simulated": "No (simulated fallback)",
        "lite_mode_note": "⚠ Ran in lite (keyword-search) mode",
        "fallback_cause": "fallback cause",
        "helpful_question": "👍 Was this answer helpful?",
        "helpful_btn": "👍 Helpful",
        "not_helpful_btn": "👎 Not helpful",
        "feedback_thanks": "✅ Thanks for the feedback!",
        "feedback_improve": "📝 We'll use this to improve!",
        "answer_heading": "Answer",
        "hide_metrics": "📊 Hide metrics",
        "show_metrics": "📊 Show metrics",
        "avatar_user": "YOU",
        "avatar_bot": "BOT",
        "ocr_tip_detail": "📌 **Tip**: For best results, use PDFs with selectable text (not scanned images). If you have a scanned PDF in a non-English language, OCR may need configuration.",
        "document_too_large": "📏 **Document too large**:",
        "could_not_read_pdf": "📄 **Could not read this PDF**:",
        "error_short": "❌ Error",
        "error_label": "❌ **Error**:",
        "troubleshooting": "**Troubleshooting:**\n- Check your API key in Streamlit secrets\n- Try with a smaller document\n- Check the Streamlit Cloud logs for details",
        "simulated_warning": "The language model is not configured. This simulated preview was not saved to history or counted toward your usage.",
        "provider_error": "The language model provider could not complete this request. No answer was saved and the request was not counted toward this app's usage budget.",
        "provider_retry": "Please try again later or contact the application operator if the problem continues.",
        "privacy_section": "### 🔒 Privacy & Data Management",
        "download_data": "📥 Download Data",
        "download_help": "Export your data (GDPR right to portability)",
        "save_json": "💾 Save JSON",
        "data_ready": "✅ Your data is ready!",
        "delete_data": "🗑️ Delete Data",
        "delete_help": "Delete all your data (GDPR right to erasure)",
        "delete_warning": "⚠️ This will permanently delete ALL your data!",
        "delete_confirm": "I understand - delete everything",
        "all_deleted": "✅ All data deleted!",
        "delete_error": "❌ Error deleting data",
        "gdpr_rights": "**Your GDPR Rights:**\n- ✅ Access your data (📥 Download)\n- ✅ Delete your data (🗑️ Delete)\n- ✅ Data portability (JSON format)\n- ✅ Restrict processing\n- ✅ Object to tracking",
        "nav_home": "Home",
        "nav_privacy": "Privacy Policy",
        "nav_terms": "Terms of Service",
        "nav_third_party": "Third-Party Services",
        "consent_title": "🔒 **Privacy & Data Processing Notice**",
        "consent_body": "By using AI DocuSearch, you consent to:\n- **Processing your documents** with AI models (text excerpts, and page images when picture interpretation is enabled, are sent to the configured LLM provider)\n- **Storing chat history** for 30 days and feedback for 90 days (auto-deleted after)\n- **Analytics & debugging** via LangSmith for performance monitoring",
        "consent_rights": "✅ **Your rights:**\n- 📥 Download your data anytime\n- 🗑️ Delete your data anytime\n- ⏰ Auto-deletion after 30 days (history) / 90 days (feedback)",
        "consent_agree": "✅ I Agree & Continue",
        "consent_required": "⚠️ You must consent to use this service",
    },
    "ro": {
        "title": "AI DocuSearch",
        "description": "Motorul tău personal de căutare AI pentru documente.\nÎncarcă un PDF și găsește instantaneu răspunsurile ascunse în interior — clauze, definiții, rezumate, explicații.",
        "budget_info": "Încearcă gratuit: poți pune ~25 de întrebări pe un document de ~100 de pagini. Documentele mai mari vor suporta mai puține întrebări.",
        "upload_prompt": "Încarcă un fișier PDF, DOCX sau TXT",
        "file_saved": "📁 Fișier salvat",
        "extracting": "⏳ Se extrage textul din document...",
        "extracted": "✅ Extras",
        "chars": "caractere",
        "mb": "MB",
        "pages": "pagini",
        "in": "în",
        "seconds": "s",
        "ask_question": "Pune o întrebare despre document...",
        "processing": "⏳ Se procesează întrebarea...",
        "completed": "✅",
        "document_info": "Informații document",
        "positive": "Pozitiv",
        "negative": "Negativ",
        "upload_first": "👆 Te rog, încarcă mai întâi un document",
        "failed_save": "❌ Eșec la salvarea fișierului",
        "failed_extract": "❌ Eșec la extragerea textului",
        "ocr_note": "⚠️ **Notă privind PDF-urile scanate**",
        "ocr_tip": "📌 **Sfat**: Pentru rezultate optime, folosește PDF-uri cu text selectabil",
        "upload_prompt_multimodal": "Încarcă un fișier PDF, DOCX, TXT, PNG, JPEG sau WebP",
        "interpreting_pictures": "🖼️ Se interpretează imaginile cu modelul de viziune...",
        "picture_interpretation_incomplete": "🖼️ Interpretarea imaginilor a fost incompletă",
        "picture_pages_truncated": "🖼️ Doar primele {count} pagini au fost interpretate pentru imagini (MEDIA_MAX_PAGES).",
        "picture_descriptions_label": "descriere(i) de imagine",
        "no_text_or_pictures": "Nu s-a putut extrage text sau descrieri de imagini din acest fișier.",
        "answer_includes_picture_description": "🖼️ Acest răspuns include o descriere de imagine generată de AI.",
        "mobile_detected": "📱 **Dispozitiv mobil detectat**: Modul hibrid se adaptează automat la capacitățile dispozitivului tău. Folosește o procesare rapidă și eficientă, optimizată pentru mobil.",
        "share_feedback": "Trimite feedback",
        "share_feedback_help": "Deschide formularul de feedback pentru testarea AI DocuSearch într-un tab nou.",
        "trial_nearly_complete": "**Perioada de testare gratuită aproape s-a încheiat:** Te apropii de limita de utilizare. Mai rămâne doar o cantitate mică.",
        "trial_complete": "**Perioada de testare gratuită s-a încheiat:** Perioada ta de testare gratuită a expirat. Te rugăm să îți împărtășești experiența folosind formularul de mai jos. Feedback-ul tău ajută la îmbunătățirea AI DocuSearch și este foarte apreciat.",
        "metric_total_time": "Timp total",
        "metric_chunks_used": "Fragmente utilizate",
        "metric_context_size": "Dimensiune context",
        "metric_tokens_est": "Tokeni (est.)",
        "metric_tokens_actual": "Tokeni (reali)",
        "detailed_metrics": "Timp și tokeni detaliat",
        "metric_build_time": "Timp de construire/indexare",
        "metric_retrieval_time": "Timp de căutare",
        "metric_generation_time": "Timp de generare",
        "metric_temperature": "Temperatură",
        "metric_prompt_tokens": "Tokeni de prompt",
        "metric_completion_tokens": "Tokeni de răspuns",
        "metric_live_api": "API live utilizat",
        "yes": "Da",
        "no_simulated": "Nu (răspuns simulat de rezervă)",
        "lite_mode_note": "⚠ Rulat în modul lite (căutare după cuvinte cheie)",
        "fallback_cause": "cauza rezervei",
        "helpful_question": "👍 Ți-a fost util acest răspuns?",
        "helpful_btn": "👍 Util",
        "not_helpful_btn": "👎 Nu a fost util",
        "feedback_thanks": "✅ Mulțumim pentru feedback!",
        "feedback_improve": "📝 Vom folosi acest lucru pentru a ne îmbunătăți!",
        "answer_heading": "Răspuns",
        "hide_metrics": "📊 Ascunde metricile",
        "show_metrics": "📊 Afișează metricile",
        "avatar_user": "TU",
        "avatar_bot": "BOT",
        "ocr_tip_detail": "📌 **Sfat**: Pentru rezultate optime, folosește PDF-uri cu text selectabil (nu imagini scanate). Dacă ai un PDF scanat într-o limbă non-engleză, OCR poate necesita configurare.",
        "document_too_large": "📏 **Document prea mare**:",
        "could_not_read_pdf": "📄 **Nu s-a putut citi acest PDF**:",
        "error_short": "❌ Eroare",
        "error_label": "❌ **Eroare**:",
        "troubleshooting": "**Depanare:**\n- Verifică cheia API în secretele Streamlit\n- Încearcă cu un document mai mic\n- Verifică jurnalele Streamlit Cloud pentru detalii",
        "simulated_warning": "Modelul de limbaj nu este configurat. Această previzualizare simulată nu a fost salvată în istoric și nu a fost contorizată în utilizarea ta.",
        "provider_error": "Furnizorul modelului de limbaj nu a putut finaliza această cerere. Niciun răspuns nu a fost salvat, iar cererea nu a fost contorizată în bugetul de utilizare al aplicației.",
        "provider_retry": "Te rugăm să încerci din nou mai târziu sau să contactezi operatorul aplicației dacă problema persistă.",
        "privacy_section": "### 🔒 Confidențialitate și gestionarea datelor",
        "download_data": "📥 Descarcă datele",
        "download_help": "Exportă datele tale (dreptul la portabilitate, GDPR)",
        "save_json": "💾 Salvează JSON",
        "data_ready": "✅ Datele tale sunt pregătite!",
        "delete_data": "🗑️ Șterge datele",
        "delete_help": "Șterge toate datele tale (dreptul la ștergere, GDPR)",
        "delete_warning": "⚠️ Aceasta va șterge definitiv TOATE datele tale!",
        "delete_confirm": "Am înțeles - șterge tot",
        "all_deleted": "✅ Toate datele au fost șterse!",
        "delete_error": "❌ Eroare la ștergerea datelor",
        "gdpr_rights": "**Drepturile tale GDPR:**\n- ✅ Acces la datele tale (📥 Descărcare)\n- ✅ Ștergerea datelor tale (🗑️ Ștergere)\n- ✅ Portabilitatea datelor (format JSON)\n- ✅ Restricționarea prelucrării\n- ✅ Opoziție la urmărire",
        "nav_home": "Acasă",
        "nav_privacy": "Politica de confidențialitate",
        "nav_terms": "Termeni și condiții",
        "nav_third_party": "Servicii terțe",
        "consent_title": "🔒 **Notificare privind confidențialitatea și prelucrarea datelor**",
        "consent_body": "Prin utilizarea AI DocuSearch, îți dai consimțământul pentru:\n- **Prelucrarea documentelor tale** cu modele AI (fragmente de text și, dacă interpretarea imaginilor este activată, imagini ale paginilor sunt trimise furnizorului LLM configurat)\n- **Stocarea istoricului conversațiilor** timp de 30 de zile și a feedback-ului timp de 90 de zile (șterse automat ulterior)\n- **Analize și depanare** prin LangSmith, pentru monitorizarea performanței",
        "consent_rights": "✅ **Drepturile tale:**\n- 📥 Descarcă-ți datele oricând\n- 🗑️ Șterge-ți datele oricând\n- ⏰ Ștergere automată după 30 de zile (istoric) / 90 de zile (feedback)",
        "consent_agree": "✅ Sunt de acord și continui",
        "consent_required": "⚠️ Trebuie să îți dai consimțământul pentru a folosi serviciul",
    },
}


def get_user_language() -> str:
    """Return the language chosen on the start screen (English by default)."""
    return st.session_state.get("user_language", DEFAULT_LANGUAGE)


def has_chosen_language() -> bool:
    """Return True once the user has picked a language on the start screen."""
    return bool(st.session_state.get(LANGUAGE_CHOSEN_KEY, False))


def translate(key: str, default: Optional[str] = None) -> str:
    """
    Get translated text for a key in the user's language.

    Falls back to English, then to ``default`` (or the key itself).
    """
    lang = get_user_language()
    text = TRANSLATIONS.get(lang, {}).get(key, None)

    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, None)

    if text is None:
        text = default or key

    return text


def set_language(language_code: str) -> None:
    """Store the language chosen by the user (also used as the button callback)."""
    if language_code not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language_code}")
    st.session_state["user_language"] = language_code
    st.session_state[LANGUAGE_CHOSEN_KEY] = True


def show_language_selector() -> bool:
    """
    Show the bilingual language choice (English / Română) before the consent notice.

    Returns True once a language has been chosen, False while the choice is pending.
    """
    if has_chosen_language():
        return True

    st.title("AI DocuSearch")
    st.markdown("### 🌍 Choose your language / Alege limba")
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "English",
            key="language_button_en",
            on_click=set_language,
            args=("en",),
            use_container_width=True,
        )
    with col2:
        st.button(
            "Română",
            key="language_button_ro",
            on_click=set_language,
            args=("ro",),
            use_container_width=True,
        )
    return False


def read_legal_document(name: str) -> str:
    """
    Read a legal Markdown document in the user's language.

    ``name`` is the file stem, e.g. ``"PRIVACY_POLICY"``. Romanian uses ``<name>.ro.md``
    when present. English ``<name>.md`` is the binding version and the fallback.
    """
    if get_user_language() == "ro":
        ro_path = POLICIES_DIR / f"{name}.ro.md"
        if ro_path.exists():
            return ro_path.read_text(encoding="utf-8")
    return (POLICIES_DIR / f"{name}.md").read_text(encoding="utf-8")
