import os
import shutil
from tqdm import tqdm

def copy_file_with_progress(src, dst):
    """
    Copy a file from src to dst with a progress bar.
    """
    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    # Get the size of the source file
    file_size = os.path.getsize(src)

    # Initialize the progress bar
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(src)) as pbar:
        # Copy the file with a callback to update the progress bar
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                buf = fsrc.read((1024 * 1024) * 100)  # Read in chunks of 10MB
                if not buf:
                    break
                fdst.write(buf)
                pbar.update(len(buf))  # Update the progress bar

    print(f"File copied successfully to: {dst}")