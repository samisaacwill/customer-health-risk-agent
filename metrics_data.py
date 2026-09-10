"""Sample usage-metrics data for the 5 demo customers.

Generates metrics.json: flat, per-customer usage records (test cases
created, dry runs, active users, each over the last 7 and 30 days).
Kept as clean flat JSON so it can also be read directly by Grafana
Cloud's Infinity data source plugin (JSON -> root selector `$[*]`).

The numbers are handcrafted to tell a specific story:
  - Acme Logistics, Globex Manufacturing, Vertex Financial: usage has
    dropped sharply in the last 7 days relative to the 30-day trend
    (at risk).
  - BrightPath Healthcare, Northwind Retail: usage in the last 7 days
    is proportional to the 30-day trend (stable, healthy). Northwind
    also has zero open support tickets.
"""

import json
import os

METRICS_PATH = os.path.join(os.path.dirname(__file__), "metrics.json")

METRICS = [
    {
        "customer_name": "Acme Logistics",
        "trend": "declining",
        "test_cases_created_7d": 18,
        "test_cases_created_30d": 210,
        "dry_runs_7d": 25,
        "dry_runs_30d": 340,
        "active_users_7d": 6,
        "active_users_30d": 18,
    },
    {
        "customer_name": "Northwind Retail",
        "trend": "stable",
        "test_cases_created_7d": 68,
        "test_cases_created_30d": 275,
        "dry_runs_7d": 105,
        "dry_runs_30d": 430,
        "active_users_7d": 24,
        "active_users_30d": 25,
    },
    {
        "customer_name": "Globex Manufacturing",
        "trend": "declining",
        "test_cases_created_7d": 15,
        "test_cases_created_30d": 180,
        "dry_runs_7d": 20,
        "dry_runs_30d": 290,
        "active_users_7d": 5,
        "active_users_30d": 15,
    },
    {
        "customer_name": "BrightPath Healthcare",
        "trend": "stable",
        "test_cases_created_7d": 76,
        "test_cases_created_30d": 310,
        "dry_runs_7d": 115,
        "dry_runs_30d": 480,
        "active_users_7d": 27,
        "active_users_30d": 28,
    },
    {
        "customer_name": "Vertex Financial",
        "trend": "declining",
        "test_cases_created_7d": 22,
        "test_cases_created_30d": 250,
        "dry_runs_7d": 30,
        "dry_runs_30d": 400,
        "active_users_7d": 7,
        "active_users_30d": 22,
    },
]


def generate_metrics() -> list[dict]:
    """Write METRICS to metrics.json and return it."""
    with open(METRICS_PATH, "w") as f:
        json.dump(METRICS, f, indent=2)
    return METRICS


def load_metrics() -> list[dict]:
    """Load metrics.json, generating it first if it doesn't exist yet."""
    if not os.path.exists(METRICS_PATH):
        return generate_metrics()
    with open(METRICS_PATH) as f:
        return json.load(f)


def metrics_by_customer() -> dict[str, dict]:
    return {record["customer_name"]: record for record in load_metrics()}


if __name__ == "__main__":
    data = generate_metrics()
    print(f"Wrote {len(data)} customer metric records to {METRICS_PATH}")
