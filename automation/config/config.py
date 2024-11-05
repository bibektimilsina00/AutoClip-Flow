import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()
        self.GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.VIDEOS_STATUS_FILE = os.getenv("VIDEOS_STATUS_FILE")

        self.YOUTUBE_EMAIL = os.getenv("YOUTUBE_EMAIL")
        self.YOUTUBE_PASSWORD = os.getenv("YOUTUBE_PASSWORD")
        self.INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
        self.INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
        self.TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME")
        self.TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")
        self.YOUTUBE_COOKIE_FILE = os.getenv("YOUTUBE_COOKIE_FILE")
        self.INSTAGRAM_COOKIE_FILE = os.getenv("INSTAGRAM_COOKIE_FILE")
        self.TIKTOK_COOKIE_FILE = os.getenv("TIKTOK_COOKIE_FILE")
        self.GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
