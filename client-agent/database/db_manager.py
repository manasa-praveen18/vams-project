import sqlite3
import os
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'vams.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    from database.models import CREATE_ACTIVITY_LOGS_TABLE
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_ACTIVITY_LOGS_TABLE)
    conn.commit()
    conn.close()

def insert_log(app_name, window_title, start_time, end_time, duration, is_idle=False, cpu_usage=None, memory_usage=None, disk_usage=None, upload_kb=None, download_kb=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO activity_logs 
        (app_name, window_title, start_time, end_time, duration, is_idle, cpu_usage, memory_usage, disk_usage, upload_kb, download_kb, synced)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (app_name, window_title, start_time, end_time, duration, is_idle, cpu_usage, memory_usage, disk_usage, upload_kb, download_kb))
    conn.commit()
    conn.close()

def get_unsynced_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs WHERE synced = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_as_synced(log_ids):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("UPDATE activity_logs SET synced = 1 WHERE id = ?", [(id,) for id in log_ids])
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully")