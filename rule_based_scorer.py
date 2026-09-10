"""Free, deterministic health scorer - no LLM, no API key, no cost.

Reads customers.json, issues_data.json, and metrics.json, and writes
health_results.json (health_score, reasoning, recommended_action per
customer). Two rules, no LLM call:

  1. Usage tier, from test_cases_created (metrics.json):
       - 0 test cases created in the 7-day OR the 30-day window -> Red
       - 1-9 created in the 7-day window                        -> Red
       - 10-20 created in the 7-day window                      -> Yellow
       - 21+ created in the 7-day window                        -> Green
  2. Jira override: any open (not Done/Closed/Resolved) Jira issue with
     priority High/Urgent -> automatic Red, regardless of the usage tier.

customers.json's support-case priority is no longer part of scoring - it's
still shown in the report for context, but the two rules above are the
whole algorithm now.

Run standalone: `python rule_based_scorer.py`. Also wired into
.github/workflows/health-report.yml to run automatically after the
Jira data-refresh step and before the report is rendered.
"""

import json
import os

ACCOUNTS_PATH = os.path.join(os.path.dirname(__file__), "customers.json")
ISSUES_PATH = os.path.join(os.path.dirname(__file__), "issues_data.json")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "metrics.json")
HEALTH_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "health_results.json")


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def score_account(account: dict, jira_issues: list, metrics: dict) -> dict:
    """Usage tier (test_cases_created) + a Jira high-priority override.
    See module docstring for the exact thresholds."""
    created_7d = metrics.get("test_cases_created_7d", 0)
    created_30d = metrics.get("test_cases_created_30d", 0)

    if created_7d == 0 or created_30d == 0:
        score = "Red"
        zero_window = "7-day" if created_7d == 0 else "30-day"
        reasons = [f"0 test cases created in the {zero_window} window"]
    elif created_7d < 10:
        score = "Red"
        reasons = [f"only {created_7d} test cases created in the last 7 days (critically low)"]
    elif created_7d <= 20:
        score = "Yellow"
        reasons = [f"{created_7d} test cases created in the last 7 days (10-20 range)"]
    else:
        score = "Green"
        reasons = [f"{created_7d} test cases created in the last 7 days (21+ range)"]

    high_priority_jira = [
        i
        for i in jira_issues
        if (i.get("priority") or "").lower() in ("high", "urgent")
        and (i.get("status") or "").lower() not in ("done", "closed", "resolved")
    ]
    if high_priority_jira:
        score = "Red"
        reasons.append(
            f"{len(high_priority_jira)} open high/urgent-priority Jira ticket(s) - automatic escalation"
        )

    if score == "Red":
        action = "Escalate to CS leadership and get an executive check-in on the calendar before renewal."
    elif score == "Yellow":
        action = "Proactively check in with the customer and monitor usage over the next reporting period."
    else:
        action = "No action needed beyond the standard quarterly check-in."

    reasoning = "; ".join(reasons).capitalize() + "."
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
