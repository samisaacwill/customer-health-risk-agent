"""Builds the HTML Customer Health & Risk report from Claude's scored accounts."""

import html
import os
from datetime import datetime, timezone

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
REPORT_PATH = os.path.join(DOCS_DIR, "index.html")

COLORS = {
    "Green": {"bg": "#e6f4ea", "border": "#34a853", "text": "#1e7e34"},
    "Yellow": {"bg": "#fff8e1", "border": "#f9ab00", "text": "#b06f00"},
    "Red": {"bg": "#fce8e6", "border": "#ea4335", "text": "#c5221f"},
}
DEFAULT_COLOR = {"bg": "#f1f3f4", "border": "#9aa0a6", "text": "#5f6368"}


def _case_summary(cases: list) -> str:
    if not cases:
        return "No open support cases"
    open_cases = [c for c in cases if (c.get("status") or "").lower() not in ("closed", "resolved")]
    high_priority = [c for c in open_cases if (c.get("priority") or "").lower() in ("high", "urgent")]
    parts = [f"{len(open_cases)} open case(s)"]
    if high_priority:
        parts.append(f"{len(high_priority)} high/urgent")
    return ", ".join(parts)


def _render_case_rows(cases: list) -> str:
    if not cases:
        return "<li class='muted'>None</li>"
    return "".join(
        f"<li><strong>{html.escape(c.get('subject') or 'Untitled')}</strong> "
        f"&mdash; {html.escape(c.get('status') or 'Unknown')} / "
        f"{html.escape(c.get('priority') or 'Unknown')}</li>"
        for c in cases
    )


def _render_jira_rows(issues: list) -> str:
    if not issues:
        return "<li class='muted'>None</li>"
    return "".join(
        f"<li><strong>{html.escape(i.get('key') or '')}</strong> "
        f"{html.escape(i.get('summary') or '')} &mdash; "
        f"{html.escape(i.get('status') or 'Unknown')}</li>"
        for i in issues
    )


def _render_account_card(result: dict) -> str:
    account = result["account"]
    score = result.get("health_score", "Unknown")
    colors = COLORS.get(score, DEFAULT_COLOR)
    cases = account.get("cases", [])
    jira_issues = result.get("jira_issues", [])
    metrics = result.get("metrics", {})

    metrics_html = ""
    if metrics:
        metrics_html = f"""
        <div class="metrics">
          <div><span class="metric-label">Test cases (7d / 30d)</span>
            {metrics.get('test_cases_created_7d', '-')} / {metrics.get('test_cases_created_30d', '-')}</div>
          <div><span class="metric-label">Dry runs (7d / 30d)</span>
            {metrics.get('dry_runs_7d', '-')} / {metrics.get('dry_runs_30d', '-')}</div>
          <div><span class="metric-label">Active users (7d / 30d)</span>
            {metrics.get('active_users_7d', '-')} / {metrics.get('active_users_30d', '-')}</div>
          <div><span class="metric-label">Trend</span> {html.escape(str(metrics.get('trend', '-')))}</div>
        </div>
        """

    return f"""
    <div class="card" style="border-left-color: {colors['border']};">
      <div class="card-header">
        <h2>{html.escape(account['name'])}</h2>
        <span class="badge" style="background: {colors['bg']}; color: {colors['text']}; border: 1px solid {colors['border']};">
          {html.escape(score)}
        </span>
      </div>
      <div class="meta">
        {html.escape(str(account.get('industry') or 'Unknown industry'))} &middot;
        Renewal: {html.escape(str(account.get('renewal_date') or 'Unknown'))} &middot;
        {_case_summary(cases)}
      </div>
      {metrics_html}
      <p class="reasoning"><strong>Analysis:</strong> {html.escape(result.get('reasoning', ''))}</p>
      <p class="action"><strong>Recommended action:</strong> {html.escape(result.get('recommended_action', ''))}</p>
      <details>
        <summary>Support cases ({len(cases)})</summary>
        <ul>{_render_case_rows(cases)}</ul>
      </details>
      <details>
        <summary>Jira issues ({len(jira_issues)})</summary>
        <ul>{_render_jira_rows(jira_issues)}</ul>
      </details>
    </div>
    """


def generate_report(results: list) -> str:
    """Build the HTML report from scored account results and write report.html."""
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cards = "".join(_render_account_card(r) for r in results)

    counts = {"Green": 0, "Yellow": 0, "Red": 0}
    for r in results:
        counts[r.get("health_score", "Yellow")] = counts.get(r.get("health_score", "Yellow"), 0) + 1

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Customer Health & Risk Report</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #f8f9fa;
    color: #202124;
    margin: 0;
    padding: 32px 16px;
  }}
  .container {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  .subtitle {{ color: #5f6368; margin-top: 0; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 12px; margin-bottom: 24px; }}
  .summary span {{
    padding: 6px 14px; border-radius: 16px; font-size: 14px; font-weight: 600;
  }}
  .card {{
    background: #fff;
    border-left: 5px solid #9aa0a6;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08);
    padding: 20px 24px;
    margin-bottom: 20px;
  }}
  .card-header {{ display: flex; align-items: center; justify-content: space-between; }}
  .card-header h2 {{ margin: 0; font-size: 19px; }}
  .badge {{ padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 700; }}
  .meta {{ color: #5f6368; font-size: 13px; margin: 6px 0 14px; }}
  .metrics {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 24px;
    background: #f8f9fa; border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; font-size: 13px;
  }}
  .metric-label {{ display: block; color: #5f6368; font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; }}
  .reasoning, .action {{ font-size: 14px; margin: 8px 0; }}
  details {{ margin-top: 10px; font-size: 13px; }}
  summary {{ cursor: pointer; color: #1a73e8; }}
  ul {{ margin: 8px 0; padding-left: 20px; }}
  .muted {{ color: #9aa0a6; list-style: none; margin-left: -20px; }}
  footer {{ color: #9aa0a6; font-size: 12px; text-align: center; margin-top: 32px; }}
</style>
</head>
<body>
  <div class="container">
    <h1>Customer Health &amp; Risk Report</h1>
    <p class="subtitle">Generated {generated_at}</p>
    <div class="summary">
      <span style="background: {COLORS['Green']['bg']}; color: {COLORS['Green']['text']};">{counts.get('Green', 0)} Green</span>
      <span style="background: {COLORS['Yellow']['bg']}; color: {COLORS['Yellow']['text']};">{counts.get('Yellow', 0)} Yellow</span>
      <span style="background: {COLORS['Red']['bg']}; color: {COLORS['Red']['text']};">{counts.get('Red', 0)} Red</span>
    </div>
    {cards}
    <footer>Generated automatically by the Customer Health &amp; Risk Detection agent.</footer>
  </div>
</body>
</html>
"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(html_doc)
    return html_doc
