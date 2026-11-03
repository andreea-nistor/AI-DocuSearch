"""Streamlit navigation tests for the legal document pages."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

WEB_APP = Path(__file__).resolve().parent.parent / "web_app.py"


def test_language_gate_english_and_romanian() -> None:
    """The start screen offers English and Romanian before the consent notice."""
    app = AppTest.from_file(WEB_APP, default_timeout=30)
    app.run()
    assert not app.exception

    button_labels = [button.label for button in app.button]
    assert "English" in button_labels
    assert "Română" in button_labels

    next(b for b in app.button if b.label == "Română").click().run()
    assert not app.exception
    assert app.session_state["user_language"] == "ro"
    assert app.session_state["user_language_chosen"]

    app = AppTest.from_file(WEB_APP, default_timeout=30)
    app.run()
    next(b for b in app.button if b.label == "English").click().run()
    assert not app.exception
    assert app.session_state["user_language"] == "en"
    assert app.session_state["user_language_chosen"]


def test_legal_page_navigation() -> None:
    app = AppTest.from_file(WEB_APP, default_timeout=30)
    app.session_state["user_language"] = "en"
    app.session_state["user_language_chosen"] = True
    app.session_state["gdpr_consent_given"] = True
    app.run()

    link_labels = [link.label for link in app.get("page_link")]
    assert "Privacy Policy" in link_labels
    assert "Terms of Service" in link_labels
    assert "Third-Party Services" in link_labels

    app.switch_page("app_pages/privacy_policy.py").run()
    assert not app.exception
    assert any(
        "Privacy Policy for AI DocuSearch" in item.value for item in app.markdown
    )

    app.switch_page("app_pages/terms_of_service.py").run()
    assert not app.exception
    assert any(
        "Terms of Service for AI DocuSearch" in item.value for item in app.markdown
    )

    app.switch_page("app_pages/third_party_services.py").run()
    assert not app.exception
    assert any(
        "Third-Party Services Used by AI DocuSearch" in item.value
        for item in app.markdown
    )
    third_party_links = [link.label for link in app.get("page_link")]
    assert "Home" in third_party_links
    assert "Privacy Policy" in third_party_links
    assert "Terms of Service" in third_party_links


if __name__ == "__main__":
    test_language_gate_english_and_romanian()
    print("Language gate test passed.")
    test_legal_page_navigation()
    print("Legal page navigation test passed.")