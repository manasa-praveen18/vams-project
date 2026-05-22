import time
from pynput import mouse, keyboard
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

last_activity_time = time.time()
from config.settings import IDLE_THRESHOLD

def on_activity(*args):
    global last_activity_time
    last_activity_time = time.time()

def is_idle():
    return (time.time() - last_activity_time) > IDLE_THRESHOLD

def get_idle_duration():
    return int(time.time() - last_activity_time)

def start_listeners():
    mouse_listener = mouse.Listener(
        on_move=on_activity,
        on_click=on_activity,
        on_scroll=on_activity
    )
    keyboard_listener = keyboard.Listener(
        on_press=on_activity
    )
    mouse_listener.start()
    keyboard_listener.start()
if __name__ == "__main__":
    start_listeners()
    while True:
        print(f"Idle: {is_idle()} | Idle for: {get_idle_duration()}s")
        time.sleep(2)