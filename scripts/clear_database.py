# scripts/clear_database.py
import sqlite3
import os

DB_PATH = "db/emails.db"

def clear_database():
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM emails")
        conn.commit()
        conn.close()
        print("Database cleared successfully!")
    else:
        print("Database file not found.")

if __name__ == "__main__":
    clear_database()
