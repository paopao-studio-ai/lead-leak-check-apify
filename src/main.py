"""Apify Actor: Lead Leak Check.

Input (any combination; each one produces one dataset item = one charged "report" event):
  pipelineDescription  plain-English description of the lead pipeline
  pipelineConfig       structured JSON config (see README)
  runHistoryCsv        Zapier/Make/n8n run-history CSV (status + optional timestamp column)
  expectedIntervalMinutes  expected minutes between runs (optional, for the CSV check)
"""
from __future__ import annotations

import json
from typing import Any

from apify import Actor

from .lead_leak_check import analyze_history, check_config, check_description

EVENT = "report"


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
        items, errors = build_reports(inp)
        for e in errors:
            Actor.log.warning(e)

        pushed = 0
        for item in items:
            # One "report" event per analysis; push_data respects the user's max-charge limit.
            res = await Actor.push_data(item, charged_event_name=EVENT)
            pushed += 1
            Actor.log.info(f"{item['inputType']}: risk score {item['risk_score']}/100, {len(item['findings'])} findings")
            if res is not None and res.event_charge_limit_reached:
                Actor.log.warning("Max charge per run reached; stopping.")
                break

        if items:
            md = "\n\n---\n\n".join(i["report_markdown"] for i in items[:pushed])
            await Actor.set_value("REPORT.md", md, content_type="text/markdown")
        if not items:
            await Actor.fail(status_message="; ".join(errors))
            return
        await Actor.set_status_message(f"{pushed} report(s) written" + (f"; {len(errors)} input problem(s)" if errors else ""))
