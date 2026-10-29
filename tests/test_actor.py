import json
from pathlib import Path

from src.main import build_reports

EX = Path(__file__).parent.parent / "examples"


def test_description_only():
    items, errors = build_reports({"pipelineDescription": "Typeform leads go to Google Sheets via Zapier on the free plan. Nobody is assigned. No error alerts."})
    assert not errors and len(items) == 1
    it = items[0]
    assert it["inputType"] == "description" and it["risk_score"] > 0
    assert {"no-owner", "no-error-alert"} <= {f["id"] for f in it["findings"]}


def test_all_three_inputs():
    items, errors = build_reports({
        "pipelineDescription": "WhatsApp leads land in HubSpot. Round robin.",
        "pipelineConfig": json.loads((EX / "pipeline.json").read_text()),
        "runHistoryCsv": (EX / "run_history.csv").read_text(),
        "expectedIntervalMinutes": 30,
    })
    assert not errors
    assert [i["inputType"] for i in items] == ["description", "config", "run_history"]
    assert items[1]["risk_score"] == 100
    assert "failed-runs" in {f["id"] for f in items[2]["findings"]}


def test_config_as_json_string_and_bad_json():
    items, errors = build_reports({"pipelineConfig": '{"name": "x"}'})
    assert items and items[0]["pipeline"] == "x"
    items, errors = build_reports({"pipelineConfig": "{not json"})
    assert not items and "not valid JSON" in errors[0]


def test_empty_input_and_bad_csv():
    items, errors = build_reports({})
    assert not items and "Nothing to check" in errors[0]
    items, errors = build_reports({"runHistoryCsv": "a,b\n1,2\n"})
    assert not items and "status" in errors[0]
