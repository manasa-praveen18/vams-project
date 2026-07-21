import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import logger
from database.db_manager import get_unsynced_logs, mark_as_synced
from sync.retry_handler import retry_upload
from config.settings import SERVER_URL, API_ENDPOINT_UPLOAD, API_ENDPOINT_HEALTH, SYNC_INTERVAL, BATCH_SIZE
import time

def is_server_reachable():
    try:
        response = requests.get(f"{SERVER_URL}{API_ENDPOINT_HEALTH}", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_logs(logs):
    device_id = os.getenv("DEVICE_ID")
    auth_token = os.getenv("AUTH_TOKEN")
    
    payload = []
    for log in logs:
        payload.append({
            "id": log[0],
            "app_name": log[1],
            "window_title": log[2],
            "start_time": log[3],
            "end_time": log[4],
            "duration": log[5],
            "is_idle": log[6],
            "cpu_usage": log[7],
            "memory_usage": log[8],
            "disk_usage": log[9],
            "upload_kb": log[10],
            "download_kb": log[11]
        })

    response = requests.post(
        f"{SERVER_URL}{API_ENDPOINT_UPLOAD}",
        json={"device_id": device_id, "logs": payload},
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=10
    )
    return response.status_code == 200
def sync_loop():
    while True:
        try:
            if is_server_reachable():
                logs = get_unsynced_logs()
                if logs:
                    batches = [logs[i:i+BATCH_SIZE] for i in range(0, len(logs), BATCH_SIZE)]
                    for batch in batches:
                        success = retry_upload(upload_logs, batch)
                        if success:
                            log_ids = [log[0] for log in batch]
                            mark_as_synced(log_ids)
                            logger.info(f"Synced {len(batch)} records")
                else:
                    logger.info("No unsynced records found")
            else:
                logger.warning("Server unreachable, skipping sync")
        except Exception as e:
            logger.error(f"Sync error: {e}")

        time.sleep(SYNC_INTERVAL)