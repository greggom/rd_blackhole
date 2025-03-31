import os
import schedule
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

import db
from monitor import MagnetFileHandler, RcloneFileHandler, process_existing_files
import time

load_dotenv()

print('starting')

# Set up the folders to monitor
magnet_folder = os.getenv('ARR_TORRENTS_PATH')
downloads_folder = os.getenv('ARR_DOWNLOAD_PATH')
rclone_folder = os.getenv('RCLONE_PATH')

# Create db for first time
db.create_rd_db()

# Create observers for both folders
magnet_event_handler = MagnetFileHandler()
rclone_event_handler = RcloneFileHandler(downloads_folder)

def run_process_existing_files():
    """
    Run the process_existing_files function.
    """
    print('Checking for existing files.')
    process_existing_files(rclone_folder, rclone_event_handler)

# Schedule the function to run every hour
schedule.every().hour.do(run_process_existing_files)

# Run the scheduled task once at the beginning
run_process_existing_files()

# Process existing files in the rclone folder before starting the observer
process_existing_files(rclone_folder, rclone_event_handler)

magnet_observer = Observer()
rclone_observer = PollingObserver()

magnet_observer.schedule(magnet_event_handler, magnet_folder, recursive=True)
rclone_observer.schedule(rclone_event_handler, rclone_folder, recursive=True)

# Start the observers
magnet_observer.start()
rclone_observer.start()

print(f"Monitoring magnet folder: {magnet_folder}")
print(f"Monitoring rclone folder: {rclone_folder}")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    magnet_observer.stop()
    rclone_observer.stop()

magnet_observer.join()
rclone_observer.join()
