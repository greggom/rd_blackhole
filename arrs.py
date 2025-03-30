import os
from traceback import print_tb
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


load_dotenv()
sonarr_enabled = bool(os.getenv('SONARR'))
radarr_enabled = bool(os.getenv('RADARR'))
radarr_folder = os.path.join(os.getenv('ARR_TORRENTS_PATH'), 'radarr')
sonarr_folder = os.path.join(os.getenv('ARR_TORRENTS_PATH'), 'sonarr')
torrent_path = os.getenv('ARR_TORRENTS_PATH')
download_path = os.getenv('ARR_DOWNLOAD_PATH')

def arrs_folders():
    enabled = {
        'sonarr' : sonarr_enabled,
        'radarr' : radarr_enabled
    }
    for key, value in enabled.items():
        torrent_folder = os.path.join(torrent_path, key)
        download_folder = os.path.join(download_path, key)
        if value:
            os.makedirs(torrent_folder, exist_ok=True)
            os.makedirs(download_folder, exist_ok=True)
        else:
            pass


def monitored_folders():
    enabled = {
        'sonarr' : sonarr_enabled,
        'radarr' : radarr_enabled
    }
    monitored = []
    for key, value in enabled.items():
        if value:
            monitored.append(os.path.join(torrent_path, key))
    return monitored

def get_arr_folder(file_path):
    """
    Determine if a .magnet file is in the Radarr or Sonarr folder.
    """
    # Normalize the file path for comparison
    file_path = os.path.normpath(file_path)

    # Check if the file is in the Radarr folder
    if file_path.startswith(os.path.normpath(radarr_folder)):
        radarr_downloads = os.path.join(download_path, 'radarr')
        return radarr_downloads
    # Check if the file is in the Sonarr folder
    elif file_path.startswith(os.path.normpath(sonarr_folder)):
        sonarr_downloads = os.path.join(download_path, 'sonarr')
        return sonarr_downloads
    else:
        return None
