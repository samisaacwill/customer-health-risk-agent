"""Salesforce data access for the Customer Health & Risk Detection agent.

Uses simple-salesforce with a session obtained via the OAuth2 Authorization
Code flow (a Connected App's consumer key/secret + a stored refresh token).
Plain username/password/security-token auth (SOAP) and the OAuth2
username-password flow both failed against this org: many orgs created
since Summer '23 block SOAP login and the legacy OAuth username-password
grant by default, and the latter is incompatible with mandatory MFA anyway.
The refresh token is obtained once via scripts/sf_oauth_authorize.py (see
README) and then used here to mint short-lived access tokens on each run.
"""

import os

import requests
from simple_salesforce import Salesforce

CUSTOMER_NAMES = [
    "Acme Logistics",
    "Northwind Retail",
    "Globex Manufacturing",
    "BrightPath Healthcare",
    "Vertex Financial",
]


def _get_access_token() -> tuple[str, str]:
    """Exchange the stored refresh token for a fresh access token.

    Returns (access_token, instance_url).
    """
    domain = os.environ.get("SF_DOMAIN", "login")
    consumer_key = os.environ["SF_CONSUMER_KEY"]
    consumer_secret = os.environ["SF_CONSUMER_SECRET"]
    refresh_token = os.environ["SF_REFRESH_TOKEN"]

    url = f"https://{domain}.salesforce.com/services/oauth2/token"
    response = requests.post(
        url,
        data={
            "grant_type": "refresh_token",
            "client_id": consumer_key,
            "client_secret": consumer_secret,
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"], data["instance_url"]


def get_client() -> Salesforce:
    access_token, instance_url = _get_access_token()
    return Salesforce(instance_url=instance_url, session_id=access_token)


def fetch_accounts(sf: Salesforce) -> list[dict]:
    """Fetch the 5 demo Accounts: name, renewal date, industry."""
    names_clause = ", ".join(f"'{name}'" for name in CUSTOMER_NAMES)
    query = (
        "SELECT Id, Name, Renewal_Date__c, Industry "
        f"FROM Account WHERE Name IN ({names_clause})"
    )
    result = sf.query(query)
    return [
        {
            "id": record["Id"],
            "name": record["Name"],
            "renewal_date": record.get("Renewal_Date__c"),
            "industry": record.get("Industry"),
        }
        for record in result["records"]
    ]


def fetch_cases_for_account(sf: Salesforce, account_id: str) -> list[dict]:
    """Fetch related Cases for one Account: subject, status, priority."""
    query = (
        "SELECT Id, Subject, Status, Priority FROM Case "
        f"WHERE AccountId = '{account_id}'"
    )
    result = sf.query(query)
    return [
        {
            "id": record["Id"],
            "subject": record.get("Subject"),
            "status": record.get("Status"),
            "priority": record.get("Priority"),
        }
        for record in result["records"]
    ]


def fetch_accounts_with_cases(sf: Salesforce) -> list[dict]:
    """Fetch all 5 Accounts, each with its related Cases attached."""
    accounts = fetch_accounts(sf)
    for account in accounts:
        account["cases"] = fetch_cases_for_account(sf, account["id"])
    return accounts


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    client = get_client()
    for acct in fetch_accounts_with_cases(client):
        print(f"{acct['name']}: {len(acct['cases'])} case(s)")
