import time
from scheduler import start_scheduler

if __name__ == "__main__":
    start_scheduler()
    while True:
        time.sleep(60)
