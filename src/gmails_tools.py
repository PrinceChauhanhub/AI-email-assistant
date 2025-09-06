from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_PATH = "secrets/token.json"

def get_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build('gmail', 'v1', credentials=creds)

def fetch_support_emails(max_results=10):
    service = get_service()
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = m.get("payload", {})
        headers = payload.get("headers", [])
        subject = sender = date = ""
        for h in headers:
            if h["name"] == "From":
                sender = h["value"]
            if h["name"] == "Subject":
                subject = h["value"]
            if h["name"] == "Date":
                date = h["value"]

        body = ""
        if "data" in payload.get("body", {}):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        elif "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break

        if any(k in subject.lower() for k in ["support", "query", "request", "help"]):
            emails.append({
                "id": m["id"],
                "sender": sender,
                "subject": subject,
                "body": body,
                "date": date
            })
    return emails

def send_reply(to, subject, body):
    service = get_service()
    msg = email.message.EmailMessage()
    msg.set_content(body)
    msg["To"] = to
    msg["From"] = "me"
    msg["Subject"] = f"Re: {subject}"

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    message = {"raw": raw}
    service.users().messages().send(userId="me", body=message).execute()
