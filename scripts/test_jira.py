"""Standalone smoke test: connect to Jira and fetch + match issues to customers.

Does not touch customers.json, Claude, or email.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

import jira_client


def main() -> None:
    load_dotenv()
    print(f"Fetching issues from Jira project {jira_client.PROJECT_KEY}...\n")

    issues = jira_client.fetch_project_issues()
    print(f"Fetched {len(issues)} issue(s) total:\n")
    for issue in issues:
        print(f"- [{issue['key']}] ({issue['status']} / {issue['priority']}) {issue['summary']}")

    print("\nMatched to customers:\n")
    by_customer = jira_client.match_issues_to_customers(issues)
    for customer, customer_issues in by_customer.items():
        print(f"- {customer}: {len(customer_issues)} issue(s)")
        for issue in customer_issues:
            print(f"    [{issue['key']}] {issue['summary']}")


if __name__ == "__main__":
    main()
