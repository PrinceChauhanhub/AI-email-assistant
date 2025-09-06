import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.gmails_tools import fetch_support_emails, send_reply
from src.email_processor import EmailProcessor
from src.response_generator import ResponseGenerator
from src.database import Database

def main():
    print("Fetching emails...")
    emails = fetch_support_emails(max_results=10)
    if not emails:
        print("No support emails found.")
        return

    processor = EmailProcessor()
    responder = ResponseGenerator()
    db = Database()

    my_email = "idf6877@gmail.com"  # <-- Replace with your actual Gmail address
    import re
    def extract_email(sender):
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1)
        return sender.strip()

    for email in emails:
        if db.is_replied(email["id"]):
            print(f"Reply already sent for: {email['subject']}")
            continue
        sender_email = extract_email(email["sender"]).lower()
        if sender_email == my_email.lower():
            continue
        processed = processor.process_email(email)
        draft = responder.generate_response(email, processed)
        db.save_email(email, processed, draft)
        print(f"Processed: {email['subject']} | Priority: {processed['priority_label']}")

        # Auto-send urgent replies (optional)
        if processed["priority_label"] == "Urgent":
            print(f"Sending auto-reply to {email['sender']}")
            send_reply(email["sender"], email["subject"], draft)
            # Mark as replied
            cur = db.conn.cursor()
            cur.execute("UPDATE emails SET status='Replied' WHERE id=?", (email["id"],))
            db.conn.commit()

if __name__ == "__main__":
    main()
