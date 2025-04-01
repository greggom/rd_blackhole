import os
import queue
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

import db
from monitor import MagnetFileHandler, RcloneFileHandler, process_existing_files
import time

load_dotenv()

print('Starting monitors...')

# Set up the folders to monitor
magnet_folder = os.getenv('ARR_TORRENTS_PATH')
downloads_folder = os.getenv('ARR_DOWNLOAD_PATH')
rclone_folder = os.getenv('RCLONE_PATH')

# Create db for first time
db.create_rd_db()

# Create a queue to store new magnets
magnet_queue = queue.Queue()

# Create observers for both folders and pass the same queue
magnet_event_handler = MagnetFileHandler(magnet_folder, magnet_queue)
rclone_event_handler = RcloneFileHandler(downloads_folder, magnet_queue)

# Create and start the observers
magnet_observer = Observer()
rclone_observer = PollingObserver()

magnet_observer.schedule(magnet_event_handler, magnet_folder, recursive=True)
rclone_observer.schedule(rclone_event_handler, rclone_folder, recursive=True)

# Start the observers
magnet_observer.start()
rclone_observer.start()

print(f"Monitoring magnet folder: {magnet_folder}")
print(f"Monitoring rclone folder: {rclone_folder}")

# Process existing files in the rclone folder after starting the observers
process_existing_files(rclone_folder, rclone_event_handler)

try:
    while True:
        time.sleep(1)  # Keep the main thread alive
except KeyboardInterrupt:
    magnet_observer.stop()
    rclone_observer.stop()

magnet_observer.join()
rclone_observer.join()
