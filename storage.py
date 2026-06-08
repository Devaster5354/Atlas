import sqlite3

import config

conn = sqlite3.connect(config.DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS readings (
    time TEXT,
    temp REAL,
    comp_temp REAL,
    pressure REAL,
    aq REAL
)
""")

def insert(data):
    cur.execute(
        "INSERT INTO readings VALUES (datetime('now'), ?, ?, ?, ?)",
        (data["temp"], data["comp_temp"], data["pressure"], data["aq"])
    )
    conn.commit()

def fetch_recent(limit=100):
    cur.execute("SELECT * FROM readings ORDER BY time DESC LIMIT ?", (limit,))
    return cur.fetchall()