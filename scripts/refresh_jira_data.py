"""Refresh issues_data.json from live Jira data.

Run this whenever Jira issues change and you want the report to reflect
it. It does not touch customers.json, health_results.json, or email.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

import jira_client

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "issues_data.json"


def main() -> None:
    load_dotenv()
    print(f"Fetching issues from Jira project {jira_client.PROJECT_KEY}...")
    issues = jira_client.fetch_project_issues()
    by_customer = jira_client.match_issues_to_customers(issues)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(by_customer, f, indent=2)
    print(f"Wrote issues for {len(by_customer)} customer(s) to {OUTPUT_PATH}")
    print("Note: health_results.json was NOT regenerated - re-run the health analysis if scores may have changed.")


if __name__ == "__main__":
    main()
