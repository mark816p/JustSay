import sqlite3
import os
import datetime

DB_PATH = "justsay_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create History table
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            audio_path TEXT,
            transcript TEXT
        )
    ''')
    # Create Prompts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_text TEXT,
            is_active INTEGER DEFAULT 0
        )
    ''')
    # Insert default prompt if table is empty
    c.execute("SELECT COUNT(*) FROM prompts")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO prompts (prompt_text, is_active) VALUES (?, ?)", 
                  ("Transcribe accurately, maintaining punctuation and capitalization.", 1))
    conn.commit()
    conn.close()

def save_history(audio_path, transcript):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO history (audio_path, transcript) VALUES (?, ?)", (audio_path, transcript))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, audio_path, transcript FROM history ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1], "audio_path": r[2], "transcript": r[3]} for r in rows]

def get_active_prompt():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prompt_text FROM prompts WHERE is_active=1 LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def get_all_prompts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, prompt_text, is_active FROM prompts ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "prompt_text": r[1], "is_active": bool(r[2])} for r in rows]

def set_active_prompt(prompt_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE prompts SET is_active=0")
    c.execute("UPDATE prompts SET is_active=1 WHERE id=?", (prompt_id,))
    conn.commit()
    conn.close()

def add_prompt(text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO prompts (prompt_text, is_active) VALUES (?, 0)", (text,))
    conn.commit()
    conn.close()

def delete_prompt(prompt_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM prompts WHERE id=?", (prompt_id,))
    conn.commit()
    conn.close()
