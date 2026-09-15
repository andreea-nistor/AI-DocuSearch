"""
Internationalization (i18n) module for AI DocuSearch.
Detects user language from browser Accept-Language header or IP geolocation,
and provides translation utilities.
"""

import os
from typing import Optional, Dict
import streamlit as st

# Translation dictionary - add more languages/translations as needed
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
    },
    "fr": {
        "title": "AI DocuSearch",
        "description": "Votre moteur de recherche IA personnel pour les documents.\nTéléchargez un PDF et trouvez instantanément les réponses cachées à l'intérieur — clauses, définitions, résumés, explications.",
        "budget_info": "Essayez gratuitement: vous pouvez poser ~25 questions sur un document d'environ 100 pages. Les documents plus volumineux supporteront moins de questions.",
        "upload_prompt": "Télécharger un fichier PDF, DOCX ou TXT",
        "file_saved": "📁 Fichier enregistré",
        "extracting": "⏳ Extraction du texte du document...",
        "extracted": "✅ Extrait",
        "chars": "caractères",
        "mb": "MB",
        "pages": "pages",
        "in": "en",
        "seconds": "s",
        "ask_question": "Posez une question sur le document...",
        "processing": "⏳ Traitement de votre question...",
        "completed": "✅",
        "document_info": "Informations du document",
        "positive": "Positif",
        "negative": "Négatif",
        "upload_first": "👆 Veuillez d'abord télécharger un document",
        "failed_save": "❌ Échec de la sauvegarde du fichier",
        "failed_extract": "❌ Échec de l'extraction du texte",
        "ocr_note": "⚠️ **Remarque sur les PDF numérisés**",
        "ocr_tip": "📌 **Conseil**: Pour de meilleurs résultats, utilisez des PDF avec du texte sélectionnable",
        "upload_prompt_multimodal": "Téléchargez un fichier PDF, DOCX, TXT, PNG, JPEG ou WebP",
        "interpreting_pictures": "🖼️ Interprétation des images avec le modèle de vision...",
        "picture_interpretation_incomplete": "🖼️ L'interprétation des images était incomplète",
        "picture_pages_truncated": "🖼️ Seules les {count} premières pages ont été interprétées pour les images (MEDIA_MAX_PAGES).",
        "picture_descriptions_label": "description(s) d'image",
        "no_text_or_pictures": "Aucun texte ni description d'image n'a pu être extrait de ce fichier.",
        "answer_includes_picture_description": "🖼️ Cette réponse inclut une description d'image générée par IA.",
    },
    "es": {
        "title": "AI DocuSearch",
        "description": "Tu motor de búsqueda IA personal para documentos.\nCarga un PDF y encuentra instantáneamente las respuestas ocultas dentro — cláusulas, definiciones, resúmenes, explicaciones.",
        "budget_info": "Prueba gratis: puedes hacer ~25 preguntas en un documento de ~100 páginas. Los documentos más grandes soportarán menos preguntas.",
        "upload_prompt": "Carga un archivo PDF, DOCX o TXT",
        "file_saved": "📁 Archivo guardado",
        "extracting": "⏳ Extrayendo texto del documento...",
        "extracted": "✅ Extraído",
        "chars": "caracteres",
        "mb": "MB",
        "pages": "páginas",
        "in": "en",
        "seconds": "s",
        "ask_question": "Haz una pregunta sobre el documento...",
        "processing": "⏳ Procesando tu pregunta...",
        "completed": "✅",
        "document_info": "Información del documento",
        "positive": "Positivo",
        "negative": "Negativo",
        "upload_first": "👆 Por favor, carga un documento primero",
        "failed_save": "❌ Error al guardar el archivo",
        "failed_extract": "❌ Error al extraer el texto",
        "ocr_note": "⚠️ **Nota sobre PDF escaneados**",
        "ocr_tip": "📌 **Consejo**: Para mejores resultados, usa PDF con texto seleccionable",
        "upload_prompt_multimodal": "Carga un archivo PDF, DOCX, TXT, PNG, JPEG o WebP",
        "interpreting_pictures": "🖼️ Interpretando imágenes con el modelo de visión...",
        "picture_interpretation_incomplete": "🖼️ La interpretación de imágenes fue incompleta",
        "picture_pages_truncated": "🖼️ Solo se interpretaron las primeras {count} páginas para imágenes (MEDIA_MAX_PAGES).",
        "picture_descriptions_label": "descripción(es) de imagen",
        "no_text_or_pictures": "No se pudo extraer texto ni descripciones de imágenes de este archivo.",
        "answer_includes_picture_description": "🖼️ Esta respuesta incluye una descripción de imagen generada por IA.",
    },
    "de": {
        "title": "AI DocuSearch",
        "description": "Deine persönliche KI-Suchmaschine für Dokumente.\nLade ein PDF hoch und finde sofort die verborgenen Antworten — Klauseln, Definitionen, Zusammenfassungen, Erklärungen.",
        "budget_info": "Kostenlos testen: Du kannst ~25 Fragen zu einem ~100-seitigen Dokument stellen. Größere Dokumente ermöglichen weniger Fragen.",
        "upload_prompt": "PDF-, DOCX- oder TXT-Datei hochladen",
        "file_saved": "📁 Datei gespeichert",
        "extracting": "⏳ Text aus Dokument wird extrahiert...",
        "extracted": "✅ Extrahiert",
        "chars": "Zeichen",
        "mb": "MB",
        "pages": "Seiten",
        "in": "in",
        "seconds": "s",
        "ask_question": "Stelle eine Frage zum Dokument...",
        "processing": "⏳ Verarbeitung deiner Frage...",
        "completed": "✅",
        "document_info": "Dokumentinformationen",
        "positive": "Positiv",
        "negative": "Negativ",
        "upload_first": "👆 Bitte laden Sie zunächst ein Dokument hoch",
        "failed_save": "❌ Fehler beim Speichern der Datei",
        "failed_extract": "❌ Fehler beim Extrahieren des Textes",
        "ocr_note": "⚠️ **Hinweis zu gescannten PDFs**",
        "ocr_tip": "📌 **Tipp**: Verwenden Sie für beste Ergebnisse PDF mit auswählbarem Text",
        "upload_prompt_multimodal": "PDF-, DOCX-, TXT-, PNG-, JPEG- oder WebP-Datei hochladen",
        "interpreting_pictures": "🖼️ Bilder werden mit dem Vision-Modell interpretiert...",
        "picture_interpretation_incomplete": "🖼️ Die Bildinterpretation war unvollständig",
        "picture_pages_truncated": "🖼️ Nur die ersten {count} Seiten wurden auf Bilder untersucht (MEDIA_MAX_PAGES).",
        "picture_descriptions_label": "Bildbeschreibung(en)",
        "no_text_or_pictures": "Aus dieser Datei konnten weder Text noch Bildbeschreibungen extrahiert werden.",
        "answer_includes_picture_description": "🖼️ Diese Antwort enthält eine KI-generierte Bildbeschreibung.",
    },
}


def detect_language_from_header() -> Optional[str]:
    """Detect language from browser Accept-Language header.
    
    On Streamlit Cloud, this is the only reliable way to detect user language
    since IP geolocation sees Streamlit's server IP, not the user's actual location.
    """
    try:
        # Method 1: Streamlit >= 1.37 exposes request headers via st.context
        try:
            import streamlit as st

            accept_lang = st.context.headers.get("Accept-Language", "")
            if accept_lang:
                print(f"[i18n] Found Accept-Language header: {accept_lang}", flush=True)
                # Parse: en-US,en;q=0.9,fr;q=0.8,de;q=0.7
                langs = [lang.split(';')[0].split('-')[0].lower().strip() for lang in accept_lang.split(',')]
                for lang in langs:
                    if lang in TRANSLATIONS:
                        print(f"[i18n] Matched language from header: {lang}", flush=True)
                        return lang
        except Exception as e:
            print(f"[i18n] Header method 1 failed: {type(e).__name__}", flush=True)
        
        # Method 2: Try environment variable (set by some cloud providers)
        env_lang = os.getenv("HTTP_ACCEPT_LANGUAGE", "")
        if env_lang:
            print(f"[i18n] Found HTTP_ACCEPT_LANGUAGE env: {env_lang}", flush=True)
            langs = [lang.split('-')[0].lower().strip() for lang in env_lang.split(',')]
            for lang in langs:
                if lang in TRANSLATIONS:
                    print(f"[i18n] Matched language from env: {lang}", flush=True)
                    return lang
    
    except Exception as e:
        print(f"[i18n] Accept-Language detection error: {type(e).__name__}: {e}", flush=True)
    
    print("[i18n] No Accept-Language header found", flush=True)
    return None


def detect_language_from_ip() -> Optional[str]:
    """
    Detect language from user IP using geolocation API (fallback).
    
    NOTE: On Streamlit Cloud, this will NOT work because the app sees
    Streamlit's server IP, not the user's actual IP. This is only useful
    for local deployments or platforms that forward X-Forwarded-For headers.
    """
    try:
        import requests
        
        # Check if we're on Streamlit Cloud (unlikely to get user IP)
        is_streamlit_cloud = os.getenv("STREAMLIT_SERVER_HEADLESS") == "true"
        
        if is_streamlit_cloud:
            print("[i18n] On Streamlit Cloud - skipping IP geolocation (unreliable)", flush=True)
            return None
        
        # Try HTTPS first, then HTTP
        try:
            response = requests.get('https://ip-api.com/json/?fields=countryCode', timeout=3)
        except:
            response = requests.get('http://ip-api.com/json/?fields=countryCode', timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('countryCode', '').lower()
            
            print(f"[i18n] IP geolocation detected country: {country_code}", flush=True)
            
            # Map country codes to languages
            country_to_lang = {
                'ro': 'ro',  # Romania -> Romanian
                'fr': 'fr',  # France -> French
                'es': 'es',  # Spain -> Spanish
                'de': 'de',  # Germany -> German
                'at': 'de',  # Austria -> German
                'ch': 'de',  # Switzerland -> German (primary)
                'be': 'fr',  # Belgium -> French
                'gb': 'en',  # UK -> English
                'us': 'en',  # USA -> English
            }
            lang = country_to_lang.get(country_code)
            if lang in TRANSLATIONS:
                print(f"[i18n] IP detection mapped {country_code} to language: {lang}", flush=True)
                return lang
    except Exception as e:
        print(f"[i18n] IP detection failed: {type(e).__name__}", flush=True)
    return None


def detect_language_from_browser() -> Optional[str]:
    """
    Attempt to detect browser language via Streamlit mechanisms.
    On Streamlit Cloud, this is limited, so the Accept-Language header method is preferred.
    """
    # This function is kept for future use, but currently returns None
    # as there's no reliable way to get browser language on Streamlit Cloud without sidebars
    return None


def get_user_language() -> str:
    """
    Detect user language with fallback chain:
    1. Cached in session state
    2. Browser Accept-Language header
    3. Browser navigator.language (via JavaScript)
    4. IP geolocation (local deployments only)
    5. Default to English
    """
    if "user_language" not in st.session_state:
        lang = None
        
        # Try Accept-Language header first (most accurate on non-Streamlit platforms)
        lang = detect_language_from_header()
        if lang:
            print(f"[i18n] Detected language from Accept-Language header: {lang}", flush=True)
        
        # Try browser detection (Streamlit Cloud compatible)
        if not lang:
            lang = detect_language_from_browser()
            if lang:
                print(f"[i18n] Detected language from browser: {lang}", flush=True)
        
        # Fall back to IP geolocation (local deployments only, skipped on Streamlit Cloud)
        if not lang:
            lang = detect_language_from_ip()
            if lang:
                print(f"[i18n] Detected language from IP geolocation: {lang}", flush=True)
        
        # Default to English
        if not lang:
            lang = "en"
            print(f"[i18n] No language detected, defaulting to: {lang}", flush=True)
        
        st.session_state.user_language = lang
        print(f"[i18n] Final detected language: {lang}", flush=True)
    
    return st.session_state.user_language


def translate(key: str, default: Optional[str] = None) -> str:
    """
    Get translated text for a key in the user's language.
    
    Args:
        key: Translation key (e.g., "upload_prompt")
        default: Fallback text if key not found
    
    Returns:
        Translated text
    """
    lang = get_user_language()
    text = TRANSLATIONS.get(lang, {}).get(key, None)
    
    if text is None:
        # Fall back to English if not found in user's language
        text = TRANSLATIONS.get("en", {}).get(key, None)
    
    if text is None:
        # Fall back to provided default or key itself
        text = default or key
    
    return text


def set_language(language_code: str) -> None:
    """Allow user to manually override language."""
    if language_code in TRANSLATIONS:
        st.session_state.user_language = language_code
    else:
        raise ValueError(f"Unsupported language: {language_code}")


def get_supported_languages() -> Dict[str, str]:
    """Get list of supported languages."""
    return {
        "en": "English",
        "ro": "Română",
        "fr": "Français",
        "es": "Español",
        "de": "Deutsch",
    }


def add_language_selector_sidebar() -> None:
    """Add language selector to Streamlit sidebar."""
    with st.sidebar:
        st.markdown("### 🌍 Language / Limbă")
        current_lang = get_user_language()
        supported = get_supported_languages()
        
        selected_lang = st.selectbox(
            "Select language",
            options=list(supported.keys()),
            format_func=lambda x: f"{supported[x]} ({x.upper()})",
            index=list(supported.keys()).index(current_lang),
            key="language_selector"
        )
        
        if selected_lang != current_lang:
            set_language(selected_lang)
            st.rerun()
