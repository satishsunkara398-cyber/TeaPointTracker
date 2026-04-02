import sqlite3
import shutil
import os

def get_connection():
    return sqlite3.connect("teapoint.db", check_same_thread=False)

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # Sales table
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        amount REAL,
        payment_type TEXT,
        notes TEXT
    )
    """)

    # Expenses table
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        amount REAL,
        category TEXT,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()
# =================================================
# 📋 Auto Backup
# =================================================
def backup_db():
    if os.path.exists("teapoint.db"):
        shutil.copy("teapoint.db", "backup_teapoint.db")
