import os

from dotenv import load_dotenv
from tqdm import tqdm
import time

load_dotenv()
max_retries = os.getenv('MAX_RETRIES')

def copy_file_with_progress(src, dst, max_retries=max_retries, retry_delay=2):
    """
    Copy a file from src to dst with a progress bar.
    Retries the operation if it fails, up to a maximum number of retries.

    Args:
        src (str): Source file path.
        dst (str): Destination file path.
        max_retries (int): Maximum number of retry attempts (default: 3).
        retry_delay (int): Delay in seconds between retries (default: 2).
    """
    retries = 0
    while retries < int(max_retries):
        try:
            # Ensure the destination directory exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Get the size of the source file
            file_size = os.path.getsize(src)

            # Initialize the progress bar
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(src)) as pbar:
                # Copy the file with a callback to update the progress bar
                with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                    while True:
                        buf = fsrc.read((1024 * 1024) * 2)  # Read in chunks of 1MB
                        if not buf:
                            break
                        fdst.write(buf)
                        pbar.update(len(buf))  # Update the progress bar

            print(f"File copied successfully to: {dst}")
            return  # Exit the function if the copy succeeds

        except Exception as e:
            retries += 1
            print(f"Attempt {retries} failed: {e}")
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Max retries ({max_retries}) reached. Giving up.")
                raise  # Re-raise the exception if all retries fail
