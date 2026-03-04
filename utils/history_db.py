import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "history.db")

def init_db():
    """Initializes the SQLite database for analysis history."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            filename TEXT,
            jd_preview TEXT,
            match_score INTEGER,
            tier TEXT,
            full_result_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(filename, jd_text, match_score, tier, full_result):
    """Saves a new analysis record to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Short preview of JD
        jd_preview = (jd_text[:100] + '...') if len(jd_text) > 100 else jd_text
        
        c.execute('''
            INSERT INTO analysis_history (timestamp, filename, jd_preview, match_score, tier, full_result_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filename,
            jd_preview,
            match_score,
            tier,
            json.dumps(full_result)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving to history: {e}")
        return False

def get_history(limit=50):
    """Retrieves the analysis history from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, timestamp, filename, jd_preview, match_score, tier, full_result_json FROM analysis_history ORDER BY id DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "timestamp": row[1],
                "filename": row[2],
                "jd_preview": row[3],
                "match_score": row[4],
                "tier": row[5],
                "result": json.loads(row[6])
            })
        return history
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

def delete_history_item(item_id):
    """Deletes a specific history item."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM analysis_history WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting history item: {e}")
        return False

def clear_all_history():
    """Clears the entire history table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM analysis_history')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False
