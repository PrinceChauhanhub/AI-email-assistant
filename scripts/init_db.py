# scripts/init_db.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database import Database
def main():
    print("Initializing DB...")
    Database()
    print("DB initialized at db/emails.db")

if __name__ == "__main__":
    main()
