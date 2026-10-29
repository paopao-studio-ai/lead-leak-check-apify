# Lead Leak Check: find dropped leads in Zapier, Make and n8n

Your Zapier, Make or n8n runs say **Success**, but some leads still never hear back. Nobody owned the reply, a filter stopped on an empty field, the workflow was off for a day, or an AI draft sat unsent.

This Actor reads a description of your lead pipeline and returns a **0–100 risk score** with **ranked findings**. Each finding says why leads leak there and gives a concrete fix.

- **No logins, no scraping, no API keys.** Everything runs on 15 offline rules. Your data is only used for this run.
- **Unstated safeguards are reported as `verify`**, never as safe, so a vague description never looks like a clean bill of health.
- The same rules are open source as an MCP server: [lead-leak-check-mcp](https://github.com/paopao-studio-ai/lead-leak-check-mcp).

## Input

Fill in any one or more of these fields. Each one produces one report, which is one dataset item.

| Field | What to paste |
|---|---|
| `pipelineDescription` | Plain English: "Typeform and WhatsApp leads go to Google Sheets via Zapier on the free plan. Nobody is assigned. No error alerts." |
| `pipelineConfig` | Structured JSON for exact results (shape below) |
| `runHistoryCsv` | Run-history export with a `status` column and, optionally, a `timestamp` column |
| `expectedIntervalMinutes` | Optional. Expected minutes between runs, used for the CSV gap check |

```json
{
  "name": "Typeform -> Google Sheets -> Slack #sales",
  "sources": [{ "type": "web_form", "required_contact_field": false }, { "type": "whatsapp", "logged_to_storage": false }],
  "storage": { "type": "google_sheets", "dedupe": false },
  "routing": { "owner_assignment": "none", "after_hours_coverage": false },
  "response": { "sla_minutes": 30, "auto_ack": true, "ai_drafts": true, "human_send_step": false },
  "monitoring": { "error_alerts": false, "unanswered_lead_alert": false, "run_history_review": "never" },
  "automation": { "platform": "zapier", "plan": "free" },
  "timezone": { "business_tz": "America/New_York", "automation_tz": "UTC" },
  "follow_up": { "sequence": false }
}
```

## Output

One dataset item per report:

```json
{
  "inputType": "config",
  "pipeline": "Typeform -> Google Sheets -> Slack #sales",
  "risk_score": 100,
  "counts": { "high": 4, "medium": 5, "low": 3, "verify": 0 },
  "findings": [
    {
      "id": "no-owner",
      "severity": "high",
      "title": "Nobody owns the first reply",
      "why": "Leads posted to a shared sheet or channel are seen by everyone and answered by no one.",
      "fix": "Assign an owner per lead (round robin or fixed) at the moment it is created, and name them in the notification.",
      "evidence": ""
    }
  ],
  "notes": [],
  "report_markdown": "# Lead leak risk: ..."
}
```

A combined Markdown report is also saved to the default key-value store as `REPORT.md`.

## What it checks

Owner assignment, unanswered-lead (SLA) alerts, error alerts, response-time target, system of record, chat leads (WhatsApp/DM) not logged, silent filters on empty fields, unsent AI drafts, after-hours coverage, instant acknowledgement, deduplication, timezone mismatch, free-plan limits, follow-up sequence and run-history review. From a run-history CSV it flags failed and halted runs, quietly filtered runs, long gaps with no runs and a stale last run.

## Pricing

Pay per event: you pay only for each report produced, which is one dataset item. Empty or invalid input is not charged.

## Run locally

```bash
pip install -r requirements.txt
mkdir -p storage/key_value_stores/default
echo '{"pipelineDescription": "WhatsApp leads land in HubSpot via Make.com. Nobody is assigned."}' > storage/key_value_stores/default/INPUT.json
APIFY_LOCAL_STORAGE_DIR=./storage python -m src
pip install pytest && python -m pytest -q tests
```

Or `apify run` with the [Apify CLI](https://docs.apify.com/cli).

Made by [Paopao Studio](https://paopao-studio.pages.dev/?utm_source=apify&utm_medium=readme). MIT license.
