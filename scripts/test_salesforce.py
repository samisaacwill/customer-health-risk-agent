"""Standalone smoke test: connect to Salesforce and fetch the 5 demo accounts.

Does not touch Jira, Claude, or email.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

import salesforce_client


def main() -> None:
    load_dotenv()
    print("Connecting to Salesforce...")
    sf = salesforce_client.get_client()
    print("Connected. Fetching accounts + cases...\n")

    accounts = salesforce_client.fetch_accounts_with_cases(sf)
    print(f"Fetched {len(accounts)} account(s):\n")
    for account in accounts:
        print(f"- {account['name']}")
        print(f"    Industry:      {account['industry']}")
        print(f"    Renewal date:  {account['renewal_date']}")
        print(f"    Cases ({len(account['cases'])}):")
        if not account["cases"]:
            print("      (none)")
        for case in account["cases"]:
            print(f"      - [{case['status']} / {case['priority']}] {case['subject']}")
        print()


if __name__ == "__main__":
    main()
