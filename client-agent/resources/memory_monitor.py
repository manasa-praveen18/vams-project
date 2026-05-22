import psutil

def get_memory_usage():
    ram = psutil.virtual_memory()
    return {
        "total_gb": round(ram.total / (1024**3), 2),
        "used_gb": round(ram.used / (1024**3), 2),
        "percent": ram.percent
    }

if __name__ == "__main__":
    import time
    while True:
        mem = get_memory_usage()
        print(f"RAM: {mem['used_gb']}GB / {mem['total_gb']}GB ({mem['percent']}%)")
        time.sleep(2)