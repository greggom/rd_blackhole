import os
import time
from watchdog.events import FileSystemEventHandler
from real_debrid import upload_magnet_to_realdebrid
from download import copy_file_with_progress
from arrs import get_arr_folder

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
        print("Checking for existing .magnet files...")
        for root, _, files in os.walk(self.magnet_folder):
            for file in files:
                if file.endswith(".magnet"):
                    file_path = os.path.join(root, file)
                    self.process_magnet_file(file_path)

    def process_magnet_file(self, file_path):
        """
        Process a single .magnet file.
        """
        print(f"Processing existing .magnet file: {file_path}")
        with open(file_path, 'r') as file:
            magnet_link = file.read().strip()
            result = upload_magnet_to_realdebrid(magnet_link=magnet_link, magnet_file_path=file_path)
            if result:
                arr_folder = get_arr_folder(file_path)
                if arr_folder:
                    for file_name in result['filename']:
                        print(file_name)
                        self.magnet_queue.put({"filename": file_name, "arr_folder": arr_folder})
                        print(f"Added to queue: {file_name} (arr_folder: {arr_folder})")
                        wait()

    def on_created(self, event):
        """
        Triggered when a file or directory is created in the magnet folder.
        """
        file_path = event.src_path
        print(f"Created: {file_path}")
        time.sleep(0.5)

        if file_path.endswith(".magnet"):
            print(f"Processing new .magnet file: {file_path}")
            self.process_magnet_file(file_path)

class RcloneFileHandler(FileSystemEventHandler):
    def __init__(self, downloads_folder, magnet_queue):
        self.downloads_folder = downloads_folder
        self.magnet_queue = magnet_queue

    def on_created(self, event):
        """Triggered when a file or directory is created in the rclone folder."""
        file_path = event.src_path
        print(f"Created in rclone folder: {file_path}")
        self.process_file(file_path)

    def process_file(self, file_path):
        """Process a file in the rclone folder."""
        if any(file_path.lower().endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]):
            file_name = os.path.basename(file_path)
            file_name_match = file_name.lower()
            print(file_name_match)

            # Check if the file is in the queue
            while not self.magnet_queue.empty():
                item = self.magnet_queue.get()
                print('Filename {}'.format(item['filename'].lower()))
                print(f'Match: {file_name_match}')
                if item["filename"].lower() == file_name_match:
                    arr_folder = item["arr_folder"]
                    print(f"File found in queue: {file_name}")
                    dst_file = os.path.join(arr_folder, file_name)
                    copy_file_with_progress(file_path, dst_file)
                    print(f"Copied file to: {dst_file}")
                    wait()
                    break
                else:
                    # If the file doesn't match, put it back in the queue for later processing
                    self.magnet_queue.put(item)

def process_existing_files(folder, handler):
    """Process existing files in the folder when the script starts."""
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if any(file.lower().endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]):
                file_name = os.path.basename(file_path)
                file_name_match = file_name.lower()
                handler.process_file(file_path)