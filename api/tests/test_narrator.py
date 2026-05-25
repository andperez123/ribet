from unittest.mock import MagicMock, patch

from app.services.narrator import narrate_findings_batch
from app.services.rules.runner import RuleFinding


def test_narrator_off_returns_empty():
    with patch("app.services.narrator.settings") as mock_settings:
        mock_settings.ribet_narration = "off"
        mock_settings.openai_api_key = "sk-test"
        result = narrate_findings_batch([], "Acme", None, None)
    assert result == {}


def test_narrator_mock_openai():
    finding = RuleFinding(
        finding_type="ar_aging",
        title="AR over 90 elevated",
        detail="22% of AR is over 90 days",
        severity="high",
        confidence=0.9,
        business_impact="cash",
        department="finance",
        category="ar",
        suggested_action="Review top overdue accounts",
    )
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"narratives":[{"fingerprint":"ar-90","narrative":"Cash collection slowed.","recommendation":"Call top 5 accounts."}]}'
            )
        )
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.services.narrator.settings") as mock_settings:
        mock_settings.ribet_narration = "on"
        mock_settings.openai_api_key = "sk-test"
        with patch("openai.OpenAI", return_value=mock_client):
            result = narrate_findings_batch([finding], "Acme", None, None)

    assert "ar-90" in result
    assert result["ar-90"]["narrative"]
