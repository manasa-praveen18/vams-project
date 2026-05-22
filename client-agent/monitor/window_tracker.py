import win32gui
import win32process
import psutil
import time
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import logger
from database.db_manager import insert_log, create_tables
from resources.cpu_monitor import get_cpu_usage
from resources.memory_monitor import get_memory_usage
from resources.disk_monitor import get_disk_usage
from resources.network_monitor import get_network_usage
from monitor.idle_detector import is_idle, start_listeners
from config.settings import POLL_INTERVAL

def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process = psutil.Process(pid)
        app_name = process.name()
    except:
        app_name = "Unknown"
    return app_name, title

def start_monitoring():
    last_app = None
    last_title = None
    start_time = time.time()
    start_timestamp = datetime.now().isoformat()

    while True:
        app, title = get_active_window()

        if app != last_app:
            if last_app is not None:
                end_timestamp = datetime.now().isoformat()
                duration = int(time.time() - start_time)

                cpu = get_cpu_usage()
                mem = get_memory_usage()
                disk = get_disk_usage()
                net = get_network_usage()

                insert_log(
                    app_name=last_app,
                    window_title=last_title,
                    start_time=start_timestamp,
                    end_time=end_timestamp,
                    duration=duration,
                    is_idle=is_idle(),
                    cpu_usage=cpu,
                    memory_usage=mem['percent'],
                    disk_usage=disk['percent'],
                    upload_kb=net['upload_kb'],
                    download_kb=net['download_kb']
                )
                logger.info(f"Saved: {last_app} | Duration: {duration}s")

            last_app = app
            last_title = title
            start_time = time.time()
            start_timestamp = datetime.now().isoformat()

        time.sleep(POLL_INTERVAL)