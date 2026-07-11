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
            transcript TEXT,
            word_count INTEGER DEFAULT 0
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
    # Create Users table (for Google Login & Settings)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            speaking_style TEXT DEFAULT 'Casual',
            theme TEXT DEFAULT 'Dark',
            hotkey_ptt TEXT DEFAULT 'ctrl+windows',
            hotkey_toggle TEXT DEFAULT 'ctrl+windows+space'
        )
    ''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN hotkey_ptt TEXT DEFAULT 'ctrl+windows'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN hotkey_toggle TEXT DEFAULT 'ctrl+windows+space'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE users ADD COLUMN onboarded INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Insert default local user if not present
    c.execute("SELECT COUNT(*) FROM users WHERE email='localuser@localhost'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (email, name, speaking_style, theme, hotkey_ptt, hotkey_toggle, onboarded) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("localuser@localhost", "Guest User", "Casual", "Dark", "ctrl+windows", "ctrl+windows+space", 0))

    # Create Dictionary table (for Auto-dictionary)
    c.execute('''
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE
        )
    ''')
    
    # Insert default prompt if table is empty
    c.execute("SELECT COUNT(*) FROM prompts")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO prompts (prompt_text, is_active) VALUES (?, ?)", 
                  ("Transcribe accurately, maintaining proper capitalization, natural punctuation, and smart formatting (e.g. capitalize names, add commas, format acronyms properly).", 1))
    conn.commit()
    conn.close()

# --- History ---
def save_history(audio_path, transcript):
    word_count = len(transcript.split())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO history (audio_path, transcript, word_count) VALUES (?, ?, ?)", (audio_path, transcript, word_count))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, audio_path, transcript, word_count FROM history ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1], "audio_path": r[2], "transcript": r[3], "word_count": r[4]} for r in rows]

def clear_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM history")
    conn.commit()
    conn.close()

def get_statistics():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(word_count) FROM history")
    row = c.fetchone()
    conn.close()
    total_dictations = row[0] if row and row[0] else 0
    total_words = row[1] if row and row[1] else 0
    return {"total_dictations": total_dictations, "total_words": total_words}

# --- Prompts ---
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

# --- Users & Settings ---
def save_user(email, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, name) VALUES (?, ?)", (email, name))
    conn.commit()
    conn.close()

def get_user_settings(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT speaking_style, theme, hotkey_ptt, hotkey_toggle, onboarded FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "speaking_style": row[0],
            "theme": row[1],
            "hotkey_ptt": row[2] or "ctrl+windows",
            "hotkey_toggle": row[3] or "ctrl+windows+space",
            "onboarded": bool(row[4])
        }
    return None

def update_user_settings(email, speaking_style, theme, hotkey_ptt="ctrl+windows", hotkey_toggle="ctrl+windows+space", onboarded=1):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET speaking_style=?, theme=?, hotkey_ptt=?, hotkey_toggle=?, onboarded=? WHERE email=?", 
              (speaking_style, theme, hotkey_ptt, hotkey_toggle, int(onboarded), email))
    conn.commit()
    conn.close()

# --- Dictionary ---
def add_to_dictionary(word):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO dictionary (word) VALUES (?)", (word,))
    conn.commit()
    conn.close()

def get_dictionary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT word FROM dictionary")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
