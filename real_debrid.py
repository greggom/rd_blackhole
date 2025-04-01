import os
import time
from dotenv import load_dotenv
import requests
from arrs import search_and_mark_failed
from torrents import delete_file_with_retry

load_dotenv()
rd_api_token = os.getenv('RD_APITOKEN')
base_url = "https://api.real-debrid.com/rest/1.0"


# List of video file extensions
VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]

def get_torrent_info(torrent_id):
    """
    Get the filename and ID of the torrent.
    """
    torrent_info_url = f"{base_url}/torrents/info/{torrent_id}"
    headers = {"Authorization": f"Bearer {rd_api_token}"}
    response = requests.get(torrent_info_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get torrent info: {response.text}")

    torrent_info = response.json()
    return torrent_info

def remove_torrent(torrent_id):
    """
    Remove the torrent from Real-Debrid.
    """
    delete_url = f"{base_url}/torrents/delete/{torrent_id}"
    headers = {"Authorization": f"Bearer {rd_api_token}"}
    response = requests.delete(delete_url, headers=headers)

    if response.status_code != 204:
        raise Exception(f"Failed to remove torrent: {response.text}")

    print(f"Torrent {torrent_id} removed from Real-Debrid.")

def upload_magnet_to_realdebrid(magnet_link, magnet_file_path=None):
    """
    Upload a magnet link to Real-Debrid, select only video files for download,
    and handle cases where the torrent is not cached.
    """
    # Step 1: Add the magnet link
    add_magnet_url = f"{base_url}/torrents/addMagnet"
    headers = {"Authorization": f"Bearer {rd_api_token}"}
    data = {"magnet": magnet_link}
    response = requests.post(add_magnet_url, headers=headers, data=data)

    if response.status_code != 201:
        raise Exception(f"Failed to add magnet link: {response.text}")

    torrent_id = response.json()["id"]
    print(f"Magnet link added. Torrent ID: {torrent_id}")

    # Step 2: Get torrent info to list files
    torrent_info = get_torrent_info(torrent_id)
    print(f"Torrent status: {torrent_info['status']}")

    # Step 3: Filter video files
    video_files = []
    video_files_names = []
    if "files" in torrent_info and torrent_info["files"]:
        for file in torrent_info["files"]:
            file_name = file["path"].lower().lstrip('/')
            if any(file_name.endswith(ext) for ext in VIDEO_EXTENSIONS) and "sample" not in file_name:
                video_files.append(str(file["id"]))  # Convert ID to string
                video_files_names.append(file_name)
                print(f"Video file found: {file['path']}")
    else:
        print("No files found in the torrent or 'files' key is missing.")

    if not video_files:
        print("No video files found in the torrent.")
        return None

    # Step 4: Select only video files for download
    select_files_url = f"{base_url}/torrents/selectFiles/{torrent_id}"
    files_data = {"files": ",".join(video_files)}  # Select only video files
    response = requests.post(select_files_url, headers=headers, data=files_data)

    if response.status_code != 204:
        raise Exception(f"Failed to select files: {response.text}")

    print("Video files selected for download.")

    # Step 5: Check if the torrent is cached
    torrent_info = get_torrent_info(torrent_id)
    if torrent_info["status"] == "queued": # "waiting_files_selection":
        print("Torrent is not cached on Real-Debrid and needs to be downloaded.")
        remove_torrent(torrent_id)  # Remove the torrent if it needs to be downloaded
        # Mark the release as failed in Sonarr or Radarr
        if magnet_file_path:
            release_title = os.path.basename(magnet_file_path).replace(".magnet", "")
            search_and_mark_failed(release_title, magnet_file_path)
        return None


    # Step 6: Wait for the torrent to finish downloading
    while True:
        torrent_info = get_torrent_info(torrent_id)
        if torrent_info["status"] == "downloaded":
            break
        elif torrent_info["status"] == "error" or torrent_info["status"] == "dead":
            print("Torrent encountered an error or is dead.")
            remove_torrent(torrent_id)  # Remove the torrent if it encounters an error
            # Mark the release as failed in Sonarr or Radarr
            if magnet_file_path:
                release_title = os.path.basename(magnet_file_path).replace(".magnet", "")
                search_and_mark_failed(release_title, magnet_file_path)
            return None
        print("Torrent is still downloading. Waiting...")
        time.sleep(10)  # Wait 10 seconds before checking again


    # Step 7: Delete the .magnet file if the path is provided
    if magnet_file_path and os.path.exists(magnet_file_path):
        delete_file_with_retry(magnet_file_path)


    # Step 8: Return the filename and ID
    return {
        "id": torrent_info["id"],
        "filename": video_files_names
    }
# # Example usage
# magnet_link = 'magnet:?xt=urn:btih:E738C8D2BA12C9923847935976D52F49D51070BA&dn=Cobra+Kai+S06+2160p+NF+WEB-DL+DV+HDR+H+265&tr=http%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2ftracker.auctor.tv%3a6969%2fannounce&tr=udp%3a%2f%2fopentracker.i2p.rocks%3a6969%2fannounce&tr=https%3a%2f%2fopentracker.i2p.rocks%3a443%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=udp%3a%2f%2ftracker.openbittorrent.com%3a6969%2fannounce&tr=http%3a%2f%2ftracker.openbittorrent.com%3a80%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2ftracker.moeking.me%3a6969%2fannounce&tr=udp%3a%2f%2fexplodie.org%3a6969%2fannounce&tr=udp%3a%2f%2fexodus.desync.com%3a6969%2fannounce&tr=udp%3a%2f%2fuploads.gamecoast.net%3a6969%2fannounce&tr=udp%3a%2f%2ftracker1.bt.moack.co.kr%3a80%2fannounce&tr=udp%3a%2f%2ftracker.tiny-vps.com%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.theoks.net%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.skyts.net%3a6969%2fannounce&tr=udp%3a%2f%2ftracker-udp.gbitt.info%3a80%2fannounce&tr=udp%3a%2f%2fopen.tracker.ink%3a6969%2fannounce&tr=udp%3a%2f%2fmovies.zsw.ca%3a6969%2fannounce'
# result = upload_magnet_to_realdebrid(magnet_link)
# if result:
#     print(f"Torrent ID: {result['id']}")
#     print(f"Filename: {result['filename']}")
