import sqlite3
from datetime import datetime
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect('command_stats.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_stats (
            command TEXT PRIMARY KEY,
            usage_count INTEGER DEFAULT 0
        )
        ''')
        conn.commit()

def increment_command(command: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO command_stats (command, usage_count)
        VALUES (?, 1)
        ON CONFLICT(command) DO UPDATE SET usage_count = usage_count + 1
        ''', (command,))
        conn.commit()

def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT command, usage_count FROM command_stats ORDER BY usage_count DESC')
        return cursor.fetchall()
