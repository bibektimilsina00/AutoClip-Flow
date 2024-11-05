import json
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import io
from automation.config.config import Config
from automation.utils.file_utils import FileUtils
from automation.manager.video_manager import VideoManager


class GoogleDriveService:
    def __init__(self):
        config: Config = Config()
        video_manager = VideoManager()
        credentials = service_account.Credentials.from_service_account_file(
            config.GOOGLE_APPLICATION_CREDENTIALS,
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
