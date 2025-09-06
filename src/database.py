# src/database.py
import sqlite3
import os
import json

class Database:
    def __init__(self, db_path="db/emails.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS emails (
                        id TEXT PRIMARY KEY,
                        sender TEXT,
                        subject TEXT,
                        body TEXT,
                        date TEXT,
                        sentiment TEXT,
                        priority_label TEXT,
                        priority_score REAL,
                        extracted TEXT,
                        summary TEXT,
                        draft TEXT,
                        status TEXT,
                        is_frustrated BOOLEAN DEFAULT 0,
                        contact_info TEXT,
                        requirements TEXT)''')
        self.conn.commit()

    def is_replied(self, email_id):
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM emails WHERE id=?", (email_id,))
        row = cur.fetchone()
        return row is not None and row[0] == "Replied"

    def save_email(self, email, processed, draft):
        cur = self.conn.cursor()
        # If status is already Replied, keep it. Otherwise, set to Pending.
        cur.execute("SELECT status FROM emails WHERE id=?", (email["id"],))
        row = cur.fetchone()
        status = row[0] if row and row[0] == "Replied" else "Pending"
        
        # Prepare additional fields
        is_frustrated = processed.get("is_frustrated", False)
        contact_info = json.dumps(processed.get("contact_info", {}))
        requirements = json.dumps(processed.get("requirements", []))
        
        cur.execute('''INSERT OR REPLACE INTO emails
                       (id, sender, subject, body, date, sentiment, priority_label, priority_score, extracted, summary, draft, status, is_frustrated, contact_info, requirements)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (email["id"], email["sender"], email["subject"], email["body"], email.get("date", ""),
                     processed.get("sentiment"), processed.get("priority_label"), processed.get("priority_score"),
                     json.dumps(processed.get("extracted")), processed.get("summary"), draft, status, 
                     is_frustrated, contact_info, requirements))
        self.conn.commit()

    def list_emails(self, limit=100):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM emails ORDER BY priority_score DESC, date DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return rows
