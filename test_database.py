import os
import sqlite3
import database


def test_database_init(tmp_path):
    db_file = tmp_path / "test_data.db"
    database.DB_PATH = str(db_file)
    database.init_db()
    
    assert os.path.exists(db_file)
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    
    # Verify tables exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in c.fetchall()}
    assert {"history", "prompts", "users", "dictionary"}.issubset(tables)
    conn.close()


def test_dictionary_operations(tmp_path):
    db_file = tmp_path / "test_data.db"
    database.DB_PATH = str(db_file)
    database.init_db()
    
    database.add_to_dictionary("Wispr")
    words = database.get_dictionary()
    assert "Wispr" in words
    
    # Duplicate insertion should be ignored
    database.add_to_dictionary("Wispr")
    words = database.get_dictionary()
    assert words.count("Wispr") == 1


def test_history_operations(tmp_path):
    db_file = tmp_path / "test_data.db"
    database.DB_PATH = str(db_file)
    database.init_db()
    
    database.save_history("Hello world testing dictation")
    history = database.get_history()
    assert len(history) == 1
    assert history[0]["transcript"] == "Hello world testing dictation"
    assert history[0]["word_count"] == 4
    
    stats = database.get_statistics()
    assert stats["total_dictations"] == 1
    assert stats["total_words"] == 4
    
    database.clear_history()
    assert len(database.get_history()) == 0
