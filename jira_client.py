"""Jira Cloud data access for the Customer Health & Risk Detection agent.

Uses the Jira Cloud REST API v3 with email + API token (basic auth).
Issues are matched to customers by checking whether the customer's name
appears in the issue summary text (no custom Jira field required for
this demo).
"""

import os

import requests

from salesforce_client import CUSTOMER_NAMES

PROJECT_KEY = "KAN"


def _auth_and_base_url() -> tuple[str, tuple[str, str]]:
    base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
    email = os.environ["JIRA_EMAIL"]
    api_token = os.environ["JIRA_API_TOKEN"]
    return base_url, (email, api_token)


def fetch_project_issues() -> list[dict]:
    """Fetch all issues in the KAN project via the Enhanced JQL Search API."""
    base_url, auth = _auth_and_base_url()
    url = f"{base_url}/rest/api/3/search/jql"

    issues: list[dict] = []
    next_page_token = None
    while True:
        body = {
            "jql": f"project = {PROJECT_KEY} ORDER BY created DESC",
            "fields": ["summary", "status", "priority", "issuetype"],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token

        response = requests.post(url, json=body, auth=auth, timeout=30)
        response.raise_for_status()
        data = response.json()

        for record in data.get("issues", []):
            fields = record.get("fields", {})
            issues.append(
                {
                    "key": record.get("key"),
                    "summary": fields.get("summary"),
                    "status": (fields.get("status") or {}).get("name"),
                    "priority": (fields.get("priority") or {}).get("name"),
                }
            )

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return issues


def match_issues_to_customers(issues: list[dict]) -> dict[str, list[dict]]:
    """Group issues by customer, matching on customer name in the summary."""
    matched: dict[str, list[dict]] = {name: [] for name in CUSTOMER_NAMES}
    for issue in issues:
        summary = issue.get("summary") or ""
        for name in CUSTOMER_NAMES:
            if name.lower() in summary.lower():
                matched[name].append(issue)
    return matched


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    all_issues = fetch_project_issues()
    by_customer = match_issues_to_customers(all_issues)
    for customer, customer_issues in by_customer.items():
        print(f"{customer}: {len(customer_issues)} issue(s)")
