import os
import requests
from dotenv import load_dotenv

load_dotenv()
sonarr_enabled = bool(os.getenv('SONARR'))
radarr_enabled = bool(os.getenv('RADARR'))
radarr_folder = os.path.join(os.getenv('ARR_TORRENTS_PATH'), 'radarr')
sonarr_folder = os.path.join(os.getenv('ARR_TORRENTS_PATH'), 'sonarr')
SONARR_API_KEY = os.getenv('SONARR_API')
SONARR_BASE_URL = os.getenv('SONARR_BASE_URL')
RADARR_API_KEY = os.getenv('RADARR_API')
RADARR_BASE_URL = os.getenv('RADARR_BASE_URL')
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



def search_and_mark_failed(release_title, file_path):
    """
    Search for a release in Sonarr or Radarr's history and mark it as failed.
    """
    # Determine if the release is from Sonarr or Radarr
    if file_path.startswith(os.path.normpath(os.path.join(os.getenv('ARR_TORRENTS_PATH'), 'sonarr'))):
        print("Release is from Sonarr.")
        return search_and_mark_failed_in_sonarr(release_title)
    elif file_path.startswith(os.path.normpath(os.path.join(os.getenv('ARR_TORRENTS_PATH'), 'radarr'))):
        print("Release is from Radarr.")
        return search_and_mark_failed_in_radarr(release_title)
    else:
        print("Release is not from Sonarr or Radarr.")
        return False

def search_and_mark_failed_in_sonarr(release_title):
    """
    Search for a release in Sonarr's history and mark it as failed.
    """
    if not SONARR_API_KEY or not SONARR_BASE_URL:
        raise ValueError("Sonarr API key or base URL is not set in the environment variables.")

    # Step 1: Search for the release in Sonarr's history
    history_url = f"{SONARR_BASE_URL}/api/v3/history"
    headers = {"X-Api-Key": SONARR_API_KEY}
    params = {"page": 1, "pageSize": 100, "sortKey": "date", "sortDirection": "descending", "eventType": 1}

    try:
        response = requests.get(history_url, headers=headers, params=params)
        response.raise_for_status()
        history = response.json()

        # Step 2: Find the release in the history
        release_found = None
        for record in history["records"]:
            if record["sourceTitle"] == release_title:
                release_found = record
                break

        if not release_found:
            print(f"Release '{release_title}' not found in Sonarr history.")
            return False

        # Step 3: Mark the release as failed
        mark_failed_url = f"{SONARR_BASE_URL}/api/v3/history/failed/{release_found['id']}"
        data = {
            "id": release_found["id"],
            "seriesId": release_found["seriesId"],
            "sourceTitle": release_found["sourceTitle"],
            "quality": release_found["quality"],
            "customFormatScore": release_found["customFormatScore"],
            "reason": "ManualFailure",  # Reason for marking as failed
            "type": "manual"  # Type of failure
        }

        # Add episodeIds if the release has episodes
        if "episodes" in release_found:
            data["episodeIds"] = [episode["id"] for episode in release_found["episodes"]]

        response = requests.post(mark_failed_url, headers=headers, json=data)
        response.raise_for_status()

        print(f"Release '{release_title}' marked as failed in Sonarr.")

        # Step 4: Trigger a new search for the item if it has episodes
        if "episodes" in release_found:
            search_url = f"{SONARR_BASE_URL}/api/v3/command"
            search_data = {
                "name": "EpisodeSearch",
                "episodeIds": [episode["id"] for episode in release_found["episodes"]]
            }

            response = requests.post(search_url, headers=headers, json=search_data)
            response.raise_for_status()

            print(f"New search triggered for '{release_title}' in Sonarr.")
        else:
            print(f"No episodes found for release '{release_title}'. Skipping search trigger.")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Error interacting with Sonarr API: {e}")
        return False

def search_and_mark_failed_in_radarr(release_title):
    """
    Search for a release in Radarr's history and mark it as failed.
    """
    if not RADARR_API_KEY or not RADARR_BASE_URL:
        raise ValueError("Radarr API key or base URL is not set in the environment variables.")

    # Step 1: Search for the release in Radarr's history
    history_url = f"{RADARR_BASE_URL}/api/v3/history"
    headers = {"X-Api-Key": RADARR_API_KEY}
    params = {"page": 1, "pageSize": 100, "sortKey": "date", "sortDirection": "descending", "eventType": 1}

    try:
        response = requests.get(history_url, headers=headers, params=params)
        response.raise_for_status()
        history = response.json()

        # Step 2: Find the release in the history
        release_found = None
        for record in history["records"]:
            if record["sourceTitle"] == release_title:
                release_found = record
                break

        if not release_found:
            print(f"Release '{release_title}' not found in Radarr history.")
            return False

        # Step 3: Mark the release as failed
        mark_failed_url = f"{RADARR_BASE_URL}/api/v3/history/failed/{release_found['id']}"
        data = {
            "movieId": release_found["movieId"],
            "sourceTitle": release_found["sourceTitle"],
            "quality": release_found["quality"],
            "customFormatScore": release_found["customFormatScore"],
            "reason": "ManualFailure",  # Reason for marking as failed
            "type": "manual"  # Type of failure
        }

        response = requests.post(mark_failed_url, headers=headers, json=data)
        response.raise_for_status()

        print(f"Release '{release_title}' marked as failed in Radarr.")

        search_url = f"{RADARR_BASE_URL}/api/v3/command"
        search_data = {
            "name": "MoviesSearch",
            "movieIds": [release_found["movieId"]]
        }

        response = requests.post(search_url, headers=headers, json=search_data)
        response.raise_for_status()

        print(f"New search triggered for '{release_found['movieId']}' in Radarr.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error interacting with Radarr API: {e}")
        return False

def create_locked_mkv_file(file_path):
    """
    Create a blank locked .mkv file at the specified path.
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Create a blank .mkv file
        f = open(file_path, 'wb')
        f.write(b'')  # Write an empty byte string to create the file

        # Lock the file (platform-specific)
        if os.name == 'posix':  # Linux/macOS
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif os.name == 'nt':  # Windows
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)

        print(f"Created and locked blank .mkv file: {file_path}")
    except Exception as e:
        print(f"Failed to create or lock .mkv file: {e}")
    finally:
        # Close the file after locking
        if 'f' in locals():
            f.close()

def delete_blank_mkv_file(file_path):
    """
    Delete the blank locked .mkv file at the specified path.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted blank .mkv file: {file_path}")
        else:
            print(f"Blank .mkv file not found: {file_path}")
    except Exception as e:
        print(f"Failed to delete blank .mkv file: {e}")


