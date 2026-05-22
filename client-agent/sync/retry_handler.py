import time
from utils.logger import logger
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

MAX_RETRIES = 3
INITIAL_WAIT = 60  # seconds

def retry_upload(upload_func, logs):
    attempt = 0
    wait_time = INITIAL_WAIT

    while attempt < MAX_RETRIES:
        try:
            success = upload_func(logs)
            if success:
                logger.info(f"Sync successful on attempt {attempt + 1}")
                return True
        except Exception as e:
            logger.error(f"Sync attempt {attempt + 1} failed: {e}")

        attempt += 1
        if attempt < MAX_RETRIES:
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2  # double the wait each time

    logger.error(f"Sync failed after {MAX_RETRIES} attempts")
    return False