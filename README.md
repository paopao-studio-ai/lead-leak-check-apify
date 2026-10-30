# Lead Leak Check — Zapier, Make & n8n Lead Pipeline Audit

Your Zapier, Make or n8n runs say **Success**, but some leads still never hear back. Nobody owned the reply, a filter stopped on an empty field, the workflow was off for a day, or an AI draft sat unsent.

**Lead Leak Check audits your lead pipeline / lead-to-CRM workflow, not your website.** You paste a plain-English description, a JSON config, or a run-history CSV export; it returns a **0–100 leak-risk score** with **ranked findings**, and each finding says why leads leak there and gives a concrete fix. Built for agencies and automation freelancers auditing a client's lead routing, sales ops checking speed-to-lead safeguards, and founders running leads through Zapier/Make/n8n into Sheets, HubSpot or Slack.

- **No logins, no scraping, no API keys.** Everything runs on 15 offline rules over what you paste. Your data is only used for this run.
- **It does not crawl or test websites or contact forms.** It only knows what you describe or export.
- **Unstated safeguards are reported as `verify`**, never as safe, so a vague description never looks like a clean bill of health.
- **$0.05 per report**, the demo report for an empty input is not charged as a report (details under *Pricing*).
- The same rules are open source as an MCP server: [lead-leak-check-mcp](https://github.com/paopao-studio-ai/lead-leak-check-mcp).

## How to use it

1. Click **Try for free** / **Start**. The input is pre-filled with an example pipeline, so the first run works as-is.
2. Replace the example with your own pipeline: a few sentences, a JSON config, or a run-history CSV export.
3. Open the **Output** tab: one row per report with the risk score and ranked findings, plus the full Markdown report (`REPORT.md`).

Runs finish in a few seconds and use the smallest memory size.

## Input

Fill in any one or more of these fields. Each one produces one report, which is one dataset item.
If you start a run with **no input at all** (for example `{}` through the API, a schedule or an integration), the Actor analyses a built-in sample pipeline and returns one free demo report marked `"inputType": "sample"`, so you can see the output format.

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

One dataset item per report. This is the real (shortened) result for the pre-filled example, *"Leads come from a Typeform and WhatsApp into Google Sheets via Zapier on the free plan. Nobody is assigned; Slack pings #sales. ChatGPT drafts replies. No error alerts."*:

```json
{
  "inputType": "description",
  "pipeline": "described pipeline",
  "risk_score": 87,
  "counts": { "high": 2, "medium": 1, "low": 0, "verify": 11 },
  "findings": [
    {
      "id": "no-owner",
      "severity": "high",
      "title": "Nobody owns the first reply",
      "why": "Leads posted to a shared sheet or channel are seen by everyone and answered by no one.",
      "fix": "Assign an owner per lead (round robin or fixed) at the moment it is created, and name them in the notification.",
      "evidence": ""
    },
    {
      "id": "no-error-alert",
      "severity": "high",
      "title": "Failed or disabled automations are silent",
      "why": "Expired connections, plan limits or a teammate's edit can switch a workflow off with no notification.",
      "fix": "Turn on error notifications (Zapier/Make/n8n error workflow) to a channel someone watches, and alert when no run happened in the expected window.",
      "evidence": ""
    },
    {
      "id": "free-plan-limits",
      "severity": "medium",
      "title": "Automation runs on a free plan",
      "why": "Free tiers cap tasks/operations and polling frequency; when the cap is hit, runs stop until the next cycle.",
      "fix": "Check monthly task usage against lead volume and set a usage alert, or move the lead workflow to a paid or self-hosted plan.",
      "evidence": ""
    }
  ],
  "notes": [
    "Parsed from free text with keyword rules; send a JSON config (see check_pipeline) for exact results.",
    "11 safeguard(s) were not described; they are listed as 'verify'. Fill them in for a sharper result."
  ],
  "report_markdown": "# Lead leak risk: ..."
}
```

| Field | Meaning |
|---|---|
| `inputType` | `description`, `config`, `run_history`, or `sample` (built-in demo for an empty input) |
| `risk_score` | 0 = no known risk, 100 = leaking everywhere |
| `counts` | Findings per severity: `high`, `medium`, `low`, `verify` (not stated, please check) |
| `findings` | Ranked high to verify; each has `why` and a concrete `fix` |
| `report_markdown` | The same report as Markdown, ready to paste into a doc or ticket |

All reports of the run are also combined into one Markdown file, `REPORT.md`, in the run's key-value store. Both are linked on the **Output** tab and available through the API (`/datasets/{id}/items` and `/key-value-stores/{id}/records/REPORT.md`).

## What it checks

Owner assignment, unanswered-lead (SLA) alerts, error alerts, response-time target, system of record, chat leads (WhatsApp/DM) not logged, silent filters on empty fields, unsent AI drafts, after-hours coverage, instant acknowledgement, deduplication, timezone mismatch, free-plan limits, follow-up sequence and run-history review. From a run-history CSV it flags failed and halted runs, quietly filtered runs, long gaps with no runs and a stale last run.

## Pricing

**Pay per report: $0.05 per report** (one dataset item), plus Apify's standard Actor-start event of $0.00005 per GB of memory per run. There is no subscription. A run with all three fields filled in produces three reports. Empty or invalid input is never charged, and the demo report for an empty input is not charged as a report (only the tiny Actor-start event applies). If you set a maximum charge per run, the Actor stops before a report it cannot charge.

## FAQ

**Does it scan my website or test my contact form?** No. It does not fetch any URL. Describe the form and where its leads go, and the rules check the pipeline behind it.

**Does it log in to my Zapier, Make or n8n account?** No. It only reads what you paste. Nothing is fetched or stored outside your own Apify run.

**Why do I get `verify` findings?** The description did not mention that safeguard. The Actor will not assume it exists. State it (for example "errors alert #ops") or use the JSON config to clear it.

**Can I call it from Zapier, Make, n8n or an AI agent?** Yes. Use the Apify integration or the API with a JSON input, then read the dataset items or `REPORT.md`.

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
