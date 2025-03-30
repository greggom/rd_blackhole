import os
from watchdog.events import FileSystemEventHandler
from real_debrid import upload_magnet_to_realdebrid  # Import the function
from download import copy_file_with_progress  # Import the file copy function
from tinydb import TinyDB, Query
from arrs import get_arr_folder  # Import the function to determine the arr folder

# Initialize TinyDB
db = TinyDB('InRD.json')


class MagnetFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        """
        Triggered when a file or directory is created in the magnet folder.
        """
        file_path = event.src_path
        print(f"Created: {file_path}")

        # Check if the file is a .magnet file
        if file_path.endswith(".magnet"):
            print(f"Processing .magnet file: {file_path}")
            # Read the magnet link from the file
            with open(file_path, 'r') as file:
                magnet_link = file.read().strip()
                print(f"Magnet link: {magnet_link}")
                # Upload the magnet link to Real-Debrid
                result = upload_magnet_to_realdebrid(magnet_link)
                if result:
                    print(f"Torrent ID: {result['id']}")
                    print(f"Filename: {result['filename']}")
                    # Determine the arr folder
                    arr_folder = get_arr_folder(file_path)
                    if arr_folder:
                        # Write to the database
                        db.insert({
                            "filename": result["filename"],
                            "arr_folder": arr_folder
                        })
                        print(f"Added to database: {result['filename']} (arr_folder: {arr_folder})")

class RcloneFileHandler(FileSystemEventHandler):
    def __init__(self, downloads_folder):
        self.downloads_folder = downloads_folder

    def on_created(self, event):
        """
        Triggered when a file or directory is created in the rclone folder.
        """
        file_path = event.src_path
        print(f"Created in rclone folder: {file_path}")
        self.process_file(file_path)

    def process_file(self, file_path):
        """
        Process a file in the rclone folder.
        """
        # Check if the file is a video file
        if any(file_path.lower().endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]):
            print(f"Video file found: {file_path}")
            # Check if the file is in the database
            file_name = os.path.basename(file_path)
            File = Query()
            result = db.search(File.filename == file_name)
            if result:
                print(f"File found in database: {file_name}")
                # Copy the file to the downloads folder
                dst_file = os.path.join(self.downloads_folder, file_name)
                copy_file_with_progress(file_path, dst_file)
            else:
                print(f"File not found in database: {file_name}")

def process_existing_files(folder, handler):
    """
    Process existing files in the folder when the script starts.
    Only copy the file if its filename is found in the InRD.json TinyDB file.
    """
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            # Check if the file is a video file
            if any(file.lower().endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]):
                print(f"Video file found: {file_path}")
                # Check if the file is in the database
                file_name = os.path.basename(file_path)
                file = Query()
                result = db.search(file.filename == file_name)
                if result:
                    print(f"File found in database: {file_name}")
                    # Copy the file to the downloads folder
                    dst_file = os.path.join(handler.downloads_folder, file_name)
                    copy_file_with_progress(file_path, dst_file)
                else:
                    print(f"File not found in database: {file_name}")
