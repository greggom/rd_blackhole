import os
import time
from watchdog.events import FileSystemEventHandler
from real_debrid import upload_magnet_to_realdebrid
from download import copy_file_with_progress
from arrs import get_arr_folder, create_locked_mkv_file, delete_blank_mkv_file, search_and_mark_failed
from torrents import read_magnet_file

def wait():
    time.sleep(1)

# Removing tinydb, it is unreliable for what is needed.
# # Initialize TinyDB
# db = TinyDB('InRD.json')

class MagnetFileHandler(FileSystemEventHandler):

    def __init__(self, magnet_folder, magnet_queue):
        """
        Initialize the MagnetFileHandler with the folder to monitor.
        """
        self.magnet_folder = magnet_folder
        self.magnet_queue = magnet_queue
        self.process_existing_magnets()

    def process_existing_magnets(self):
        """
        Process existing .magnet files in the magnet folder when the script starts.
        """
        print("Checking for existing magnet/torrent files...")
        for root, _, files in os.walk(self.magnet_folder):
            for file in files:
                if file.endswith(".magnet") or file.endswith(".torrent"):
                    file_path = os.path.join(root, file)
                    self.process_magnet_file(file_path)

    def process_magnet_file(self, file_path):
        """
        Process a single .magnet file.
        """
        print(f"Processing magnet/torrent file: {file_path}")
        magnet_link = read_magnet_file(file_path)
        result = upload_magnet_to_realdebrid(magnet_link=magnet_link, magnet_file_path=file_path)
        if result:
            arr_folder = get_arr_folder(file_path)
            if arr_folder:
                for file_name in result['filename']:
                    self.magnet_queue.put({"filename": file_name, "arr_folder": arr_folder})
                    print(f"Added to queue: {file_name} (arr_folder: {arr_folder})")
                    wait()

                    # Create a blank locked .mkv file in the arr_folder
                    mkv_file_path = os.path.join(arr_folder, file_name)
                    create_locked_mkv_file(mkv_file_path)


    def on_created(self, event):
        """
        Triggered when a file or directory is created in the magnet folder.
        """
        file_path = event.src_path
        print(f"Created: {file_path}")
        time.sleep(0.5)

        if file_path.endswith(".magnet") or file_path.endswith(".torrent"):
            self.process_magnet_file(file_path)

class RcloneFileHandler(FileSystemEventHandler):
    def __init__(self, rclone_folder, magnet_queue, rclone_lock):
        """
        Initialize the RcloneFileHandler with the folder to monitor, the queue, and the lock.
        """
        self.rclone_folder = rclone_folder
        self.magnet_queue = magnet_queue
        self.rclone_lock = rclone_lock
        self.running = True  # Flag to control the loop
        self.file_timeout = 60 * 60
        self.file_timers = {}

    def start_processing(self):
        """
        Continuously process files in the queue by searching for them by name in the rclone folder and its subfolders.
        Filenames are compared in lowercase to match the queue entries.
        """
        while self.running:
            with self.rclone_lock:  # Acquire the lock to ensure only one item is processed at a time
                if not self.magnet_queue.empty():
                    item = self.magnet_queue.get()
                    file_name = item["filename"]  # Filename in the queue is already lowercase
                    arr_folder = item["arr_folder"]

                    # Initialize the timer for the file if it's not already being tracked
                    if file_name not in self.file_timers:
                        self.file_timers[file_name] = time.time()

                    # Search for the file by name in the rclone folder and its subfolders
                    file_found = False
                    for root, _, files in os.walk(self.rclone_folder):
                        for entry_name in files:
                            if entry_name == file_name:  # Compare filenames in lowercase
                                file_path = os.path.join(root, entry_name)
                                print(f"File found in rclone folder: {file_path}")

                                # Delete the blank locked .mkv file before copying the actual file
                                mkv_file_path = os.path.join(arr_folder, file_name)
                                delete_blank_mkv_file(mkv_file_path)

                                # Copy the actual file to the arr_folder
                                dst_file = os.path.join(arr_folder, file_name)
                                copy_file_with_progress(file_path, dst_file)
                                file_found = True
                                break
                        if file_found:
                            break

                    if not file_found:
                        # Check if the file has been in the queue for longer than the timeout
                        if time.time() - self.file_timers[file_name] > self.file_timeout:
                            print(
                                f"File not found after 1 hour: {file_name}. Marking as failed and triggering a new search.")
                            # Mark the release as failed in Sonarr or Radarr
                            release_title = os.path.splitext(file_name)[0]  # Remove file extension
                            search_and_mark_failed(release_title, None)  # Pass None for magnet_file_path since it's not available
                            # Remove the file from the timers dictionary
                            del self.file_timers[file_name]
                        else:
                            # If the file doesn't exist and the timeout hasn't been reached, put it back in the queue
                            self.magnet_queue.put(item)
                            print(f"File not found: {file_name}. Retrying later...")
                    else:
                        # If the file is found, remove it from the timers dictionary
                        if file_name in self.file_timers:
                            del self.file_timers[file_name]

            time.sleep(5)  # Wait for 5 seconds before checking the queue again

    def stop_processing(self):
        """
        Stop the processing loop.
        """
        self.running = False