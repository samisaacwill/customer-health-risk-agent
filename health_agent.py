"""Customer Health & Risk Detection agent.

Builds the Customer Health & Risk report from three JSON data sources:
  - accounts_data.json   Salesforce Account + Case snapshot
  - issues_data.json     Jira issues, matched to customers
  - metrics.json          Product usage metrics (see metrics_data.py)

and a fourth file, health_results.json, holding the health analysis
(score, reasoning, recommended action per account). That analysis is
written directly by Claude as a one-off step rather than called live via
the Anthropic API on every run, to avoid metered per-run billing for this
demo - see README.md for how to refresh it.

Refresh accounts_data.json / issues_data.json from live Salesforce/Jira
with scripts/refresh_salesforce_data.py and scripts/refresh_jira_data.py.
Run this script directly to build and (optionally) email the report.
"""

import json
import os

from dotenv import load_dotenv

ACCOUNTS_PATH = os.path.join(os.path.dirname(__file__), "accounts_data.json")
ISSUES_PATH = os.path.join(os.path.dirname(__file__), "issues_data.json")
HEALTH_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "health_results.json")


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def build_results() -> list[dict]:
    """Merge accounts_data.json + issues_data.json + metrics.json +
    health_results.json into the list of dicts report_generator.py expects."""
    import metrics_data

    accounts = _load_json(ACCOUNTS_PATH)
    issues_by_customer = _load_json(ISSUES_PATH)
    metrics_by_customer = metrics_data.metrics_by_customer()
    health_by_customer = {r["customer_name"]: r for r in _load_json(HEALTH_RESULTS_PATH)}

    results = []
    for account in accounts:
        name = account["name"]
        analysis = health_by_customer.get(name, {})
        results.append(
            {
                "account": account,
                "jira_issues": issues_by_customer.get(name, []),
                "metrics": metrics_by_customer.get(name, {}),
                "health_score": analysis.get("health_score", "Yellow"),
                "reasoning": analysis.get(
                    "reasoning", "No precomputed analysis available for this account."
                ),
                "recommended_action": analysis.get("recommended_action", "Review manually."),
            }
        )
    return results


def main() -> None:
    load_dotenv()

    print("=" * 60)
    print("Customer Health & Risk Detection Agent")
    print("=" * 60)

    print("\n[1/3] Loading account, issue, metric, and health-analysis data...")
    results = build_results()
    for result in results:
        print(f"        - {result['account']['name']}: {result['health_score']}")

    print("\n[2/3] Generating the report...")
    import report_generator

    html_report = report_generator.generate_report(results)
    print(f"      Report written to {report_generator.REPORT_PATH}")

    print("\n[3/3] Emailing the report (if configured)...")
    email_env_vars = ("EMAIL_SENDER", "EMAIL_APP_PASSWORD", "EMAIL_RECIPIENT")
    if all(os.environ.get(v) and not os.environ[v].startswith("your-") for v in email_env_vars):
        import email_sender

        email_sender.send_report(html_report)
        print("      Report emailed successfully.")
    else:
        print("      Skipping email - EMAIL_SENDER/EMAIL_APP_PASSWORD/EMAIL_RECIPIENT not set in .env.")

    print("\nDone.")


if __name__ == "__main__":
    main()
