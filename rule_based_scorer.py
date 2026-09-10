"""Free, deterministic health scorer - no LLM, no API key, no cost.

Reads accounts_data.json, issues_data.json, and metrics.json, and writes
health_results.json (health_score, reasoning, recommended_action per
customer) using fixed weights instead of an LLM call. This replaces the
Claude-authored, hand-written analysis with something that can run
automatically in CI on every scheduled run - the tradeoff is mechanical
reasoning ("2 open high-priority cases") instead of an LLM's more nuanced
read (e.g. weighing a near-term renewal date alongside the numbers).

Run standalone: `python rule_based_scorer.py`. Also wired into
.github/workflows/health-report.yml to run automatically after the
Salesforce/Jira data-refresh steps and before the report is rendered.
"""

import json
import os

ACCOUNTS_PATH = os.path.join(os.path.dirname(__file__), "accounts_data.json")
ISSUES_PATH = os.path.join(os.path.dirname(__file__), "issues_data.json")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "metrics.json")
HEALTH_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "health_results.json")


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def score_account(account: dict, jira_issues: list, metrics: dict) -> dict:
    """Weigh open-case severity, open Jira issues, and usage trend into a
    Green/Yellow/Red score - the same three signals the earlier
    LLM-based SYSTEM_PROMPT scored on, applied as fixed rules instead."""
    cases = account.get("cases", [])
    open_cases = [c for c in cases if (c.get("status") or "").lower() not in ("closed", "resolved")]
    high_priority_open = [c for c in open_cases if (c.get("priority") or "").lower() in ("high", "urgent")]
    open_jira = [i for i in jira_issues if (i.get("status") or "").lower() not in ("done", "closed", "resolved")]
    declining = (metrics.get("trend") or "").lower() == "declining"

    risk = 0
    reasons = []
    if high_priority_open:
        risk += 2
        reasons.append(f"{len(high_priority_open)} open high/urgent-priority case(s)")
    elif len(open_cases) >= 2:
        risk += 1
        reasons.append(f"{len(open_cases)} open case(s)")
    if open_jira:
        risk += 1
        reasons.append(f"{len(open_jira)} open Jira issue(s)")
    if declining:
        risk += 2
        reasons.append("usage declining over the last 7 days vs. the 30-day trend")

    if risk >= 4:
        score = "Red"
        action = "Escalate to CS leadership and get an executive check-in on the calendar before renewal."
    elif risk >= 1:
        score = "Yellow"
        action = "Proactively check in with the customer and monitor usage over the next reporting period."
    else:
        score = "Green"
        action = "No action needed beyond the standard quarterly check-in."

    reasoning = (
        "; ".join(reasons).capitalize() + "."
        if reasons
        else "No open high-priority cases or issues, and usage is stable."
    )
    return {"health_score": score, "reasoning": reasoning, "recommended_action": action}


def generate_health_results() -> list[dict]:
    accounts = _load_json(ACCOUNTS_PATH)
    issues_by_customer = _load_json(ISSUES_PATH)
    metrics_by_customer = {m["customer_name"]: m for m in _load_json(METRICS_PATH)}

    results = []
    for account in accounts:
        name = account["name"]
        analysis = score_account(
            account, issues_by_customer.get(name, []), metrics_by_customer.get(name, {})
        )
        results.append({"customer_name": name, **analysis})

    with open(HEALTH_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    results = generate_health_results()
    print(f"Wrote health analysis for {len(results)} customer(s) to {HEALTH_RESULTS_PATH}")
    for r in results:
        print(f"  - {r['customer_name']}: {r['health_score']}")
