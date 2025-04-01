import os
import queue
import threading
import pickle
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from monitor import MagnetFileHandler, RcloneFileHandler
import time

load_dotenv()

print('Starting monitors...')

# Set up the folders to monitor
magnet_folder = os.getenv('ARR_TORRENTS_PATH')
downloads_folder = os.getenv('ARR_DOWNLOAD_PATH')
rclone_folder = os.getenv('RCLONE_PATH')



# Create a queue to store new magnets
magnet_queue = queue.Queue()

# Load the queue from a file if it exists
queue_file = 'magnet_queue.pkl'
if os.path.exists(queue_file):
    try:
        with open(queue_file, 'rb') as f:
            saved_queue = pickle.load(f)
            while not saved_queue.empty():
                magnet_queue.put(saved_queue.get())
        print("Loaded queue from file.")
    except Exception as e:
        print(f"Error loading queue from file: {e}")

# Create a lock to ensure only one item is processed at a time in RcloneFileHandler
rclone_lock = threading.Lock()

# Create observers for both folders
magnet_event_handler = MagnetFileHandler(magnet_folder, magnet_queue)
rclone_event_handler = RcloneFileHandler(rclone_folder, magnet_queue, rclone_lock)

# Start the RcloneFileHandler processing loop in a separate thread
rclone_thread = threading.Thread(target=rclone_event_handler.start_processing)
rclone_thread.start()

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


try:
    while True:
        time.sleep(1)  # Keep the main thread alive
except KeyboardInterrupt:
    print("Program interrupted. Saving queue and stopping handlers...")
    magnet_observer.stop()
    rclone_observer.stop()
    rclone_event_handler.stop_processing()  # Stop the RcloneFileHandler processing loop

    # Save the queue to a file
    try:
        with open(queue_file, 'wb') as f:
            pickle.dump(magnet_queue, f)
        print("Queue saved to file.")
    except Exception as e:
        print(f"Error saving queue to file: {e}")

magnet_observer.join()
rclone_observer.join()
rclone_thread.join()  # Wait for the RcloneFileHandler thread to finish
