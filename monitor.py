import os
import time
from watchdog.events import FileSystemEventHandler
from real_debrid import upload_magnet_to_realdebrid
from download import copy_file_with_progress
from tinydb import TinyDB, Query
from arrs import get_arr_folder

def wait():
    time.sleep(1)

# Initialize TinyDB
db = TinyDB('InRD.json')

class MagnetFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Triggered when a file or directory is created in the magnet folder."""
        file_path = event.src_path
        print(f"Created: {file_path}")
        time.sleep(0.5)

        if file_path.endswith(".magnet"):
            print(f"Processing .magnet file: {file_path}")
            with open(file_path, 'r') as file:
                magnet_link = file.read().strip()
                result = upload_magnet_to_realdebrid(magnet_link=magnet_link, magnet_file_path=file_path)
                if result:
                    arr_folder = get_arr_folder(file_path)
                    if arr_folder:
                        for file_name in result['filename']:
                            print(file_name)
                            db.insert({"filename": file_name, "arr_folder": arr_folder})
                            print(f"Added to database: {file_name} (arr_folder: {arr_folder})")
                            wait()

class RcloneFileHandler(FileSystemEventHandler):
    def __init__(self, downloads_folder):
        self.downloads_folder = downloads_folder

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
            file = Query()
            result = db.search(file.filename == file_name_match)
            print(f'Result: {result}')
            if result:
                arr_folder = result[0]['arr_folder']
                print(f"File found in database: {file_name}")
                dst_file = os.path.join(arr_folder, file_name)
                copy_file_with_progress(file_path, dst_file)
                db.remove(file.filename == file_name_match)
                wait()

def process_existing_files(folder, handler):
    """Process existing files in the folder when the script starts."""
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if any(file.lower().endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]):
                file_name = os.path.basename(file_path)
                file_name_match = file_name.lower()
                file = Query()
                result = db.search(file.filename == file_name_match)
                if result:
                    arr_folder = result[0]['arr_folder']
                    print(f"File found in database: {file_name}")
                    dst_file = os.path.join(arr_folder, file_name)
                    copy_file_with_progress(file_path, dst_file)
                    db.remove(file.filename == file_name_match)
                    wait()