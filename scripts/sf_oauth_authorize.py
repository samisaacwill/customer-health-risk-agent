"""One-time helper to obtain a Salesforce OAuth2 refresh token via the
Authorization Code flow (needed because this org blocks the legacy
username-password OAuth flow).

Usage:
    python scripts/sf_oauth_authorize.py url
        Prints the URL to open in your browser and log in/approve.

    python scripts/sf_oauth_authorize.py exchange <code>
        Exchanges the `code` param from the redirect URL for tokens and
        writes SF_REFRESH_TOKEN into .env.
"""

import base64
import hashlib
import re
import secrets
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from dotenv import load_dotenv
import os

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
REDIRECT_URI = "https://login.salesforce.com/services/oauth2/success"
VERIFIER_PATH = Path(
    "/private/tmp/claude-501/-Users-kavvya-NoteBookInterview/"
    "b685b1f7-d6d5-4e01-b7bd-65c180b12830/scratchpad/sf_pkce_verifier.txt"
)


def _print_authorize_url():
    load_dotenv(ENV_PATH)
    domain = os.environ.get("SF_DOMAIN", "login")
    consumer_key = os.environ["SF_CONSUMER_KEY"]

    # This org's Connected App requires PKCE on the authorization code flow.
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    VERIFIER_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERIFIER_PATH.write_text(code_verifier)

    url = (
        f"https://{domain}.salesforce.com/services/oauth2/authorize"
        f"?response_type=code&client_id={quote(consumer_key)}"
        f"&redirect_uri={quote(REDIRECT_URI, safe='')}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256"
    )
    print("Open this URL in your browser, log in, and click Allow:\n")
    print(url)
    print(
        "\nAfter approving, you'll land on a Salesforce 'success' page whose "
        "URL contains '?code=...'. Copy everything after 'code=' (and before "
        "any '&') and run:\n"
        "\n  python scripts/sf_oauth_authorize.py exchange <code>\n"
    )


def _exchange_code(code: str):
    load_dotenv(ENV_PATH)
    domain = os.environ.get("SF_DOMAIN", "login")
    consumer_key = os.environ["SF_CONSUMER_KEY"]
    consumer_secret = os.environ["SF_CONSUMER_SECRET"]

    if not VERIFIER_PATH.exists():
        print(
            "No PKCE verifier found - run 'python scripts/sf_oauth_authorize.py url' "
            "again first (it must be the same run that produced this code).",
            file=sys.stderr,
        )
        sys.exit(1)
    code_verifier = VERIFIER_PATH.read_text()

    url = f"https://{domain}.salesforce.com/services/oauth2/token"
    response = requests.post(
        url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": consumer_key,
            "client_secret": consumer_secret,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Exchange failed ({response.status_code}): {response.text}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    refresh_token = data["refresh_token"]
    instance_url = data["instance_url"]

    print(f"Success. instance_url = {instance_url}")
    _write_env_var("SF_REFRESH_TOKEN", refresh_token)
    print("Wrote SF_REFRESH_TOKEN to .env")


def _write_env_var(key: str, value: str):
    text = ENV_PATH.read_text()
    pattern = re.compile(rf"^{key}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(text):
        text = pattern.sub(line, text, count=1)
    else:
        text = text.rstrip("\n") + f"\n{line}\n"
    ENV_PATH.write_text(text)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("url", "exchange"):
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "url":
        _print_authorize_url()
    else:
        if len(sys.argv) < 3:
            print("Usage: python scripts/sf_oauth_authorize.py exchange <code>")
            sys.exit(1)
        _exchange_code(sys.argv[2])
