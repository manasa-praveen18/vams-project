import psutil

def get_disk_usage():
    disk = psutil.disk_usage('C:\\')
    io = psutil.disk_io_counters()
    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "percent": disk.percent,
        "read_mb": round(io.read_bytes / (1024**2), 2),
        "write_mb": round(io.write_bytes / (1024**2), 2)
    }

if __name__ == "__main__":
    import time
    while True:
        disk = get_disk_usage()
        print(f"Disk: {disk['used_gb']}GB / {disk['total_gb']}GB ({disk['percent']}%) | Read: {disk['read_mb']}MB | Write: {disk['write_mb']}MB")
        time.sleep(2)