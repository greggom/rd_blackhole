from dotenv import load_dotenv
import os.path
import bencodepy
import hashlib
import time

load_dotenv()

def get_extension(torrent_file_path):
    _, extension = os.path.splitext(torrent_file_path)
    return extension


def extract_magnet_from_torrent(torrent_file_path):
    """
    Extract the magnet link from a .torrent file using bencode.py.
    """
    # Read the torrent file
    with open(torrent_file_path, 'rb') as f:
        torrent_data = f.read()

    # Decode the torrent file
    metadata = bencodepy.decode(torrent_data)

    # Calculate the info hash
    info = metadata[b'info']
    info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
    info_hash_hex = info_hash.hex()

    # Create the magnet link
    magnet_link = f"magnet:?xt=urn:btih:{info_hash_hex}&dn={metadata[b'info'][b'name'].decode()}"

    f.close()
    return magnet_link

def read_magnet_file(file_path):
    """
    Read a .magnet or .torrent file and extract the magnet link.
    If it's a .torrent file, extract the magnet link from the torrent file.
    If it's a .magnet file, read the magnet link directly.
    """
    try:
        # Check the file extension
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()  # Ensure the extension is lowercase for comparison

        if extension == '.torrent':
            # Extract the magnet link from the torrent file
            magnet_link = extract_magnet_from_torrent(file_path)
            return magnet_link
        elif extension == '.magnet':
            # Read the magnet link directly from the .magnet file
            with open(file_path, 'r') as file:
                magnet_link = file.read().strip()  # Read the file and remove any extra whitespace
                return magnet_link
        else:
            print(f"Error: Unsupported file type '{extension}'. Expected '.magnet' or '.torrent'.")
            return None
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

def delete_file_with_retry(file_path, max_retries=6, delay=10):
    for attempt in range(max_retries):
        try:
            os.remove(file_path)
            print(f"Successfully deleted file: {file_path}")
            return
        except PermissionError:
            print(f"Attempt {attempt + 1}: File is still in use. Retrying in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to delete file after {max_retries} attempts: {file_path}")



