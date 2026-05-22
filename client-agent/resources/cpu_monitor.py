import psutil
import time

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

if __name__ == "__main__":
    while True:
        cpu = get_cpu_usage()
        print(f"CPU Usage: {cpu}%")
        time.sleep(2)