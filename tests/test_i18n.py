import pytest

from fur_empire.i18n import localized_error


@pytest.mark.parametrize(
    "language,expected",
    [
        ("de-DE", "Name oder Passwort stimmt nicht."),
        ("en-GB,en;q=0.9", "Name or password is incorrect."),
        ("es-ES", "El nombre o la contraseña no son correctos."),
        ("fr-FR", "Nom ou mot de passe incorrect."),
    ],
)
def test_authentication_error_uses_shared_message_key(language, expected):
    key, message = localized_error("Name oder Passwort stimmt nicht.", language)
    assert key == "error.invalid_credentials"
    assert message == expected


def test_unsupported_language_and_unknown_message_preserve_safe_fallback():
    assert localized_error("Keine Berechtigung.", "invalid") == (
        "error.permission",
        "Keine Berechtigung.",
    )
    assert localized_error("Existing uncatalogued message", "en") == (
        None,
        "Existing uncatalogued message",
    )
