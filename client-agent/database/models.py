CREATE_ACTIVITY_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    window_title TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration INTEGER NOT NULL,
    is_idle BOOLEAN DEFAULT 0,
    cpu_usage REAL,
    memory_usage REAL,
    disk_usage REAL,
    upload_kb REAL,
    download_kb REAL,
    synced BOOLEAN DEFAULT 0
)
"""