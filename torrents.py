from dotenv import load_dotenv
import os.path
import bencodepy
import hashlib
import base64

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
    return magnet_link

def read_magnet_file(file_path):
    """
    Read a .magnet file and extract the magnet link.
    """
    try:
        with open(file_path, 'r') as file:
            magnet_link = file.read().strip()  # Read the file and remove any extra whitespace
            return magnet_link
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

def delete_magnet(magnet):
    print(f'Deleting magnet {magnet}')
    os.remove(magnet)
