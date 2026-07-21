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
from config.settings import SERVER_URL, DEVICE_ID, AUTH_TOKEN, DEVICE_NAME, API_ENDPOINT_REGISTER

session_id = None

def auto_register():
    """Auto-register device if no DEVICE_ID or AUTH_TOKEN found in .env"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    current_device_id = os.getenv("DEVICE_ID")
    current_token = os.getenv("AUTH_TOKEN")
    
    if current_device_id and current_token:
        logger.info("Device already registered, skipping registration")
        return current_device_id, current_token

    logger.info("No credentials found, auto-registering with server...")
    try:
        username = os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
        response = requests.post(
            f"{SERVER_URL}{API_ENDPOINT_REGISTER}",
            json={"username": username, "device_name": DEVICE_NAME},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            device_id = data["device_id"]
            token = data["token"]

            # Save to .env file
            with open(env_path, 'w') as f:
                f.write(f"DEVICE_ID={device_id}\n")
                f.write(f"AUTH_TOKEN={token}\n")

            # Set in current process environment
            os.environ["DEVICE_ID"] = device_id
            os.environ["AUTH_TOKEN"] = token

            logger.info(f"Auto-registration successful. Device ID: {device_id}")
            return device_id, token
        else:
            logger.error(f"Registration failed: {response.status_code}")
            return None, None
    except Exception as e:
        logger.error(f"Auto-registration error: {e}")
        return None, None

def send_login():
    global session_id
    device_id = os.getenv("DEVICE_ID")
    auth_token = os.getenv("AUTH_TOKEN")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/session/login",
            params={"device_id": device_id},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=5
        )
        if response.status_code == 200:
            session_id = response.json()["session_id"]
            logger.info(f"Session started: {session_id}")
    except Exception as e:
        logger.warning(f"Could not record login: {e}")

def send_logout():
    global session_id
    auth_token = os.getenv("AUTH_TOKEN")
    if session_id:
        try:
            requests.post(
                f"{SERVER_URL}/api/session/logout",
                params={"session_id": session_id},
                headers={"Authorization": f"Bearer {auth_token}"},
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

    # Auto-register if no credentials
    auto_register()

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