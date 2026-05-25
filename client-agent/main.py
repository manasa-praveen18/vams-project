import sys
import os
import threading
import requests

sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import logger
from database.db_manager import create_tables
from monitor.idle_detector import start_listeners
from monitor.window_tracker import start_monitoring
from sync.sync_manager import sync_loop
from config.settings import SERVER_URL, DEVICE_ID, AUTH_TOKEN

session_id = None

def send_login():
    global session_id
    try:
        response = requests.post(
            f"{SERVER_URL}/api/session/login",
            params={"device_id": DEVICE_ID},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=5
        )
        if response.status_code == 200:
            session_id = response.json()["session_id"]
            logger.info(f"Session started: {session_id}")
    except Exception as e:
        logger.warning(f"Could not record login: {e}")

def send_logout():
    global session_id
    if session_id:
        try:
            requests.post(
                f"{SERVER_URL}/api/session/logout",
                params={"session_id": session_id},
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=5
            )
            logger.info("Session ended")
        except Exception as e:
            logger.warning(f"Could not record logout: {e}")

def main():
    logger.info("VAMS client agent starting...")

    create_tables()
    logger.info("Database initialised")

    start_listeners()
    logger.info("Idle detection started")

    send_login()

    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
    logger.info("Sync service started")

    logger.info("Starting activity monitoring...")
    try:
        start_monitoring()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        send_logout()

if __name__ == "__main__":
    main()