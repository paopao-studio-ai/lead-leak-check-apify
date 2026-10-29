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


def test_build_reports_empty_and_bad_csv():
    items, errors = build_reports({})
    assert not items and "Nothing to check" in errors[0]
    items, errors = build_reports({"runHistoryCsv": "a,b\n1,2\n"})
    assert not items and "status" in errors[0]


# --- default / empty input: Console prefill is NOT applied to API, scheduled or Store test runs ---
from src.main import SAMPLE_DESCRIPTION, has_pipeline_input, sample_report  # noqa: E402

ROOT = Path(__file__).parent.parent
ACTOR_DIR = ROOT / ".actor"


def test_empty_input_falls_back_to_sample():
    for inp in ({}, {"pipelineDescription": "   "}, {"pipelineConfig": {}}, {"expectedIntervalMinutes": 30}):
        assert not has_pipeline_input(inp)
    item = sample_report()
    assert item["inputType"] == "sample" and item["risk_score"] > 0 and item["findings"]
    assert "sample" in item["notes"][0] and item["report_markdown"]


def test_sample_matches_prefill():
    schema = json.loads((ACTOR_DIR / "input_schema.json").read_text())
    assert schema["properties"]["pipelineDescription"]["prefill"] == SAMPLE_DESCRIPTION
    items, errors = build_reports({"pipelineDescription": SAMPLE_DESCRIPTION})
    assert not errors and len(items) == 1


def test_actor_json_references_existing_files():
    actor = json.loads((ACTOR_DIR / "actor.json").read_text())
    refs = [actor["input"], actor["output"], actor["dockerfile"], actor["readme"],
            actor["storages"]["dataset"], actor["storages"]["keyValueStore"]]
    for ref in refs:
        assert (ACTOR_DIR / ref).resolve().is_file(), ref


def test_output_schema_exposes_dataset_and_report():
    out = json.loads((ACTOR_DIR / "output_schema.json").read_text())
    assert out["actorOutputSchemaVersion"] == 1
    templates = {k: v["template"] for k, v in out["properties"].items()}
    assert all(v["type"] == "string" for v in out["properties"].values())
    assert templates["results"].startswith("{{links.apiDefaultDatasetUrl}}/items")
    assert templates["report"] == "{{links.apiDefaultKeyValueStoreUrl}}/records/REPORT.md"
    kvs = json.loads((ACTOR_DIR / "key_value_store_schema.json").read_text())
    assert kvs["collections"]["report"]["key"] == "REPORT.md"


def test_readme_is_store_ready():
    text = (ROOT / "README.md").read_text()
    for needle in ("## Input", "## Output", "Pay per report", "REPORT.md"):
        assert needle in text, needle
    assert "placeholder" not in text.lower() and "TODO" not in text
