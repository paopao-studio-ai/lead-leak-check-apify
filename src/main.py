"""Apify Actor: Lead Leak Check.

Input (any combination; each one produces one dataset item = one charged "report" event):
  pipelineDescription  plain-English description of the lead pipeline
  pipelineConfig       structured JSON config (see README)
  runHistoryCsv        Zapier/Make/n8n run-history CSV (status + optional timestamp column)
  expectedIntervalMinutes  expected minutes between runs (optional, for the CSV check)

If none of the three inputs is filled (e.g. an API call or a scheduled/test run with `{}`; Console
prefill is not applied there), the Actor analyses a built-in SAMPLE pipeline so every run produces at
least one dataset item. The sample report is marked inputType="sample" and is not charged.
"""
from __future__ import annotations

import json
from typing import Any

from apify import Actor

from .lead_leak_check import analyze_history, check_config, check_description

EVENT = "report"

# Same text as the input-schema prefill. Used only when the run input has no pipeline at all.
SAMPLE_DESCRIPTION = (
    "Leads come from a Typeform and WhatsApp into Google Sheets via Zapier on the free plan. "
    "Nobody is assigned; Slack pings #sales. ChatGPT drafts replies. No error alerts."
)
INPUT_KEYS = ("pipelineDescription", "pipelineConfig", "runHistoryCsv")


def has_pipeline_input(inp: dict[str, Any]) -> bool:
    """True if at least one of the three pipeline inputs carries content."""
    for key in INPUT_KEYS:
        v = inp.get(key)
        if isinstance(v, str):
            if v.strip():
                return True
        elif v:
            return True
    return False


def sample_report() -> dict[str, Any]:
    item = {"inputType": "sample", **check_description(SAMPLE_DESCRIPTION).as_dict()}
    item["notes"] = [
        "No pipeline input was provided, so this is a free demo report for a built-in sample pipeline. "
        "Fill in pipelineDescription, pipelineConfig or runHistoryCsv to audit your own pipeline.",
        *item.get("notes", []),
    ]
    return item


def build_reports(inp: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Pure function: input dict -> (dataset items, input errors). No Apify calls, easy to test."""
    items: list[dict[str, Any]] = []
    errors: list[str] = []

    desc = (inp.get("pipelineDescription") or "").strip()
    if desc:
        try:
            items.append({"inputType": "description", **check_description(desc).as_dict()})
        except ValueError as e:
            errors.append(f"pipelineDescription: {e}")

    cfg = inp.get("pipelineConfig")
    if isinstance(cfg, str) and cfg.strip():
        try:
            cfg = json.loads(cfg)
        except json.JSONDecodeError as e:
            errors.append(f"pipelineConfig is not valid JSON: {e}")
            cfg = None
    if cfg:
        try:
            items.append({"inputType": "config", **check_config(cfg).as_dict()})
        except ValueError as e:
            errors.append(f"pipelineConfig: {e}")

    csv_text = (inp.get("runHistoryCsv") or "").strip()
    if csv_text:
        interval = inp.get("expectedIntervalMinutes")
        try:
            interval = float(interval) if interval not in (None, "") else None
        except (TypeError, ValueError):
            interval = None
        try:
            items.append({"inputType": "run_history", **analyze_history(csv_text, interval).as_dict()})
        except ValueError as e:
            errors.append(f"runHistoryCsv: {e}")

    if not items and not errors:
        errors.append("Nothing to check: fill in pipelineDescription, pipelineConfig or runHistoryCsv.")
    return items, errors


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        if not isinstance(inp, dict):
            inp = {}
        Actor.log.info(f"Input fields received: {sorted(k for k in inp if inp.get(k) not in (None, '', {}, []))}")

        if not has_pipeline_input(inp):
            Actor.log.warning(
                "No pipeline input provided (prefill is not applied to API/scheduled runs). "
                "Running the built-in sample pipeline instead; this report is not charged."
            )
            item = sample_report()
            await Actor.push_data(item)  # demo output, deliberately not charged
            Actor.log.info(f"sample: risk score {item['risk_score']}/100, {len(item['findings'])} findings")
            await Actor.set_value("REPORT.md", item["report_markdown"], content_type="text/markdown")
            await Actor.set_status_message("1 sample report written (no input given; not charged)")
            return

        items, errors = build_reports(inp)
        for e in errors:
            Actor.log.warning(e)

        charging = Actor.get_charging_manager()
        pushed: list[dict[str, Any]] = []
        for item in items:
            # Respect the user's max-charge-per-run limit: push nothing that cannot be paid for.
            if charging.compute_push_data_limit(items_count=1, event_name=EVENT, is_default_dataset=True) < 1:
                Actor.log.warning("Max charge per run reached; stopping before the next report.")
                break
            # One "report" event per analysis; push_data respects the user's max-charge limit.
            res = await Actor.push_data(item, charged_event_name=EVENT)
            pushed.append(item)
            Actor.log.info(f"{item['inputType']}: risk score {item['risk_score']}/100, {len(item['findings'])} findings")
            if res is not None and res.event_charge_limit_reached:
                Actor.log.warning("Max charge per run reached; stopping.")
                break

        if not pushed:
            reason = "; ".join(errors) or "Max charge per run is too low for one report; raise it and run again."
            await Actor.fail(status_message=reason)
            return
        md = "\n\n---\n\n".join(i["report_markdown"] for i in pushed)
        await Actor.set_value("REPORT.md", md, content_type="text/markdown")
        await Actor.set_status_message(
            f"{len(pushed)} report(s) written" + (f"; {len(errors)} input problem(s)" if errors else "")
        )
