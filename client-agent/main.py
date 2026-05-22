import sys
import os
import threading

sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import logger
from database.db_manager import create_tables
from monitor.idle_detector import start_listeners
from monitor.window_tracker import start_monitoring
from sync.sync_manager import sync_loop

def main():
    logger.info("VAMS client agent starting...")

    create_tables()
    logger.info("Database initialised")

    start_listeners()
    logger.info("Idle detection started")

    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
    logger.info("Sync service started")

    logger.info("Starting activity monitoring...")
    start_monitoring()

if __name__ == "__main__":
    main()