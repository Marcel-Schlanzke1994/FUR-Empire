from fur_empire.game import Game


def test_report_keeps_historical_text_and_structured_message_parameters():
    game = object.__new__(Game)
    state = {"reports": []}
    game.report(state, "Existing title", "Existing body")
    historical = state["reports"][0]
    assert "title_key" not in historical
    game.report(
        state,
        "Auftrag abgeschlossen",
        "Bioforst ist jetzt Stufe 2.",
        title_key="report.order_title",
        body_key="report.order_body",
        message_params={"label_key": "catalog.buildings.wood.name", "level": 2},
    )
    current = state["reports"][0]
    assert current["title_key"] == "report.order_title"
    assert current["message_params"]["level"] == 2
    assert current["body"] == "Bioforst ist jetzt Stufe 2."
    assert state["reports"][1] == historical
