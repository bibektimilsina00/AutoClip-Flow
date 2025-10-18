import io
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from automation.config.config import Config
from automation.manager.video_manager import VideoManager
from automation.utils.file_utils import FileUtils


class GoogleDriveService:
    def __init__(self, credentials_path: str | None = None):
        config: Config = Config()
        video_manager = VideoManager()
        # Allow a per-user credentials file to be provided; otherwise use global config
        creds = credentials_path or config.GOOGLE_APPLICATION_CREDENTIALS
        if not creds or not os.path.exists(creds):
            raise FileNotFoundError(f"Google credentials file not found: {creds}")

        credentials = service_account.Credentials.from_service_account_file(
            creds,
        )
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.video_status_file = config.VIDEOS_STATUS_FILE

    def list_videos(self, folder_id):
        query = f"'{folder_id}' in parents and mimeType contains 'video/'"
        results = (
            self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        )
        files = results.get("files", [])

        videos_status = []
        for file in files:
            video_info = {
                "id": file["id"],
                "name": file["name"],
                "is_uploaded": False,
            }
            videos_status.append(video_info)

        return videos_status

    def download_video(self, file_id, output_path):
        request = self.drive_service.files().get_media(fileId=file_id)
        with open(output_path, "wb") as f:
            request = self.drive_service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            # Save the video to a local file

            with open(output_path, "wb") as f:
                f.write(file.getvalue())

            return output_path
