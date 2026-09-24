"""AutoMailSender backend: a stateless Flask API that sends one Gmail message per request.

Runs as a Vercel serverless function, or locally with:  python api/index.py
The browser reads the Excel file, fills the template for each person and calls /api/send.
"""

import base64
import html
import os
import re
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from flask import Flask, jsonify, request, send_from_directory

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public")
ON_VERCEL = bool(os.environ.get("VERCEL"))

# Vercel caps request bodies at 4.5 MB and base64 adds ~33%, so keep attachments under 3 MB there.
MAX_ATTACHMENT_BYTES = 3 * 1024 * 1024 if ON_VERCEL else 25 * 1024 * 1024
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024


def html_to_text(body_html):
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", body_html)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(re.sub(r"\n{3,}", "\n\n", text)).strip()


def gmail_login(gmail, password):
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
    smtp.login(gmail, password)
    return smtp


def credentials(data):
    gmail = (data.get("gmail") or "").strip()
    password = (data.get("appPassword") or "").replace(" ", "")
    if not gmail or not password:
        raise ValueError("Enter your Gmail address and App Password.")
    return gmail, password


def smtp_error(e):
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return ("Gmail rejected the login. Check the address and use a 16-character "
                "App Password (not your normal password).")
    return str(e) or e.__class__.__name__


@app.get("/api/config")
def config():
    return jsonify(maxAttachmentBytes=MAX_ATTACHMENT_BYTES, onVercel=ON_VERCEL)


@app.post("/api/verify")
def verify():
    data = request.get_json(silent=True) or {}
    try:
        gmail, password = credentials(data)
        gmail_login(gmail, password).quit()
    except Exception as e:  # noqa: BLE001
        return jsonify(error=smtp_error(e)), 400
    return jsonify(ok=True)


@app.post("/api/send")
def send():
    data = request.get_json(silent=True) or {}
    try:
        gmail, password = credentials(data)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    to_addr = (data.get("to") or "").strip()
    subject = data.get("subject") or ""
    body_html = data.get("html") or ""
    if not EMAIL_RE.match(to_addr):
        return jsonify(error="Missing or invalid email address"), 400
    if not subject.strip() or not body_html.strip():
        return jsonify(error="Subject and message cannot be empty."), 400

    sender_name = (data.get("senderName") or "").strip()
    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, gmail)) if sender_name else gmail
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(html_to_text(body_html))
    msg.add_alternative(
        '<html><body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.5">'
        f"{body_html}</body></html>",
        subtype="html",
    )

    total = 0
    for att in data.get("attachments") or []:
        content = base64.b64decode(att["data"])
        total += len(content)
        maintype, _, subtype = (att.get("type") or "application/octet-stream").partition("/")
        msg.add_attachment(content, maintype=maintype, subtype=subtype or "octet-stream",
                           filename=os.path.basename(att.get("name") or "attachment"))
    if total > MAX_ATTACHMENT_BYTES:
        return jsonify(error=f"Attachments exceed {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB."), 400

    try:
        smtp = gmail_login(gmail, password)
        try:
            smtp.send_message(msg)
        finally:
            smtp.quit()
    except Exception as e:  # noqa: BLE001
        return jsonify(error=smtp_error(e)), 502
    return jsonify(ok=True)


# Local development only: on Vercel the static page in public/ is served by the CDN.
@app.get("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  AutoMailSender running at  http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port)
