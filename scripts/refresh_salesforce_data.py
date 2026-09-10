"""Refresh accounts_data.json from live Salesforce data.

Run this whenever Salesforce data changes and you want the report to
reflect it. It does not touch Jira, health_results.json, or email.

This org rotates the Salesforce refresh token on every use (see
salesforce_client.py). Locally, the rotated token is written back into
.env automatically. In CI there's no .env file, so this script instead
writes it to $GITHUB_OUTPUT (as `new_refresh_token`) for a workflow step
to pick up and update the SF_REFRESH_TOKEN secret with - see
.github/workflows/health-report.yml.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

import salesforce_client

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "accounts_data.json"


def main() -> None:
    load_dotenv()
    print("Connecting to Salesforce...")
    sf = salesforce_client.get_client()
    accounts = salesforce_client.fetch_accounts_with_cases(sf)

    data = [
        {
            "name": account["name"],
            "industry": account.get("industry"),
            "renewal_date": account.get("renewal_date"),
            "cases": [
                {"subject": c["subject"], "status": c["status"], "priority": c["priority"]}
                for c in account["cases"]
            ],
        }
        for account in accounts
    ]

    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {len(data)} account(s) to {OUTPUT_PATH}")
    print("Note: health_results.json was NOT regenerated - re-run the health analysis if scores may have changed.")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if salesforce_client.new_refresh_token and github_output:
        with open(github_output, "a") as f:
            f.write(f"new_refresh_token={salesforce_client.new_refresh_token}\n")
        print("Refresh token was rotated by Salesforce - wrote new_refresh_token to $GITHUB_OUTPUT.")


if __name__ == "__main__":
    main()
