import psutil
import time

def get_network_usage():
    net1 = psutil.net_io_counters()
    time.sleep(1)
    net2 = psutil.net_io_counters()
    return {
        "upload_kb": round((net2.bytes_sent - net1.bytes_sent) / 1024, 2),
        "download_kb": round((net2.bytes_recv - net1.bytes_recv) / 1024, 2)
    }

if __name__ == "__main__":
    while True:
        net = get_network_usage()
        print(f"Upload: {net['upload_kb']}KB/s | Download: {net['download_kb']}KB/s")