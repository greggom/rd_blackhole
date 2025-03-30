import os
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from monitor import MagnetFileHandler, RcloneFileHandler, process_existing_files
import time

load_dotenv()

print('starting')

# Set up the folders to monitor
magnet_folder = os.getenv('ARR_TORRENTS_PATH')
downloads_folder = os.getenv('ARR_DOWNLOAD_PATH')
rclone_folder = os.getenv('RCLONE_PATH')



# Create observers for both folders
magnet_event_handler = MagnetFileHandler()
rclone_event_handler = RcloneFileHandler(downloads_folder)

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
