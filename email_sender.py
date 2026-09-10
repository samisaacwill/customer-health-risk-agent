"""Sends the HTML Customer Health & Risk report via Gmail SMTP."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_report(html_body: str, subject: str = "Customer Health & Risk Report") -> None:
    """Send html_body as an HTML email using Gmail SMTP + an app password.

    Reads EMAIL_SENDER, EMAIL_APP_PASSWORD, EMAIL_RECIPIENT from the
    environment (see .env.example).
    """
    sender = os.environ["EMAIL_SENDER"]
    app_password = os.environ["EMAIL_APP_PASSWORD"]
    recipient = os.environ["EMAIL_RECIPIENT"]

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], message.as_string())
