import os
import time

from seleniumbase import BaseCase

from automation.manager.video_manager import VideoManager
from automation.services.google_drive_service import GoogleDriveService
from automation.services.instagram_service import InstagramService
from automation.services.tiktok_service import TikTokService
from automation.services.youtube_service import YouTubeService
from automation.utils.file_utils import FileUtils
from automation.utils.logging_utils import LoggingUtils, logger


class MainApp(BaseCase):
    def __init__(self, user_id):
        super().__init__()
        self.google_drive = GoogleDriveService()
        self.video_manager = VideoManager()
        self.user_id = str(user_id)

    def setUp(self):
        super().setUp()

    def run_for_account(
        self, sb: BaseCase, drive_folder_id, email, password, platforms
    ):
        logger.info(f"Processing account for: {email}")
        try:
            video = self.get_video_to_upload(drive_folder_id)
            if video is None:
                logger.info("No new videos to upload. Exiting.")
                return

            video_path = self.download_video(video)
            if not video_path:
                return

            self.upload_to_platforms(sb, video, email, password, video_path, platforms)

            logger.info(f"Finished processing video: {video['name']}")
            self.video_manager.mark_as_uploaded(
                video["id"], folder_id=drive_folder_id, user_id=self.user_id
            ),
            # self.video_manager.save_video_data()
        except Exception as e:
            logger.error(
                f"An error occurred while processing account {email}: {str(e)}"
            )
        finally:
            logger.info(f"Closing browser session for account: {email}")
            sb.driver.quit()

        # Remove video after uploaded
        self.video_manager.deleted_video(video_path)
        logger.info(f"Deleted video: {video['name']}")

    def get_video_to_upload(self, drive_folder_id):
        self.video_manager.load_video_data(drive_folder_id, self.user_id)
        video = self.video_manager.get_next_unuploaded_video()
        if video is None:
            logger.info("Fetching new videos from Google Drive")
            new_videos = self.google_drive.list_videos(drive_folder_id)
            self.video_manager.update_video_data(
                new_videos, drive_folder_id, self.user_id
            )
            video = self.video_manager.get_next_unuploaded_video()
        return video

    def download_video(self, video):
        video_path = FileUtils.get_video_path(video["name"])
        download_video_path = self.google_drive.download_video(video["id"], video_path)
        if os.path.exists(download_video_path):
            logger.info(f"Downloaded video: {video['name']}")
            return download_video_path
        else:
            logger.error(f"Failed to download video: {video['name']}")
            return None

    def upload_to_platforms(self, sb, video, email, password, video_path, platforms):
        for platform in platforms:
            upload_success = False
            max_retries = 3
            retry_count = 0

            while not upload_success and retry_count < max_retries:
                try:
                    if platform == "youtube":
                        # upload_success = True
                        # continue
                        upload_success = self.upload_to_youtube(
                            sb, video, email, password, video_path
                        )

                    elif platform == "tiktok":
                        # upload_success = True
                        # continue
                        upload_success = self.upload_to_tiktok(
                            sb, video, email, password, video_path
                        )
                    elif platform == "instagram":
                        # upload_success = True
                        # continue
                        upload_success = self.upload_to_instagram(
                            sb, video, email, password, video_path
                        )

                    if upload_success:
                        logger.info(f"Uploaded to {platform.capitalize()}")
                        break
                    else:
                        logger.warning(
                            f"Failed to upload to {platform.capitalize()}. Retrying..."
                        )
                        retry_count += 1
                        time.sleep(30)  # Wait for 30 seconds before retrying

                except Exception as e:
                    logger.error(
                        f"Error uploading to {platform.capitalize()}: {str(e)}"
                    )
                    retry_count += 1
                    time.sleep(30)  # Wait for 30 seconds before retrying

            if not upload_success:
                logger.error(
                    f"Failed to upload to {platform.capitalize()} after {max_retries} attempts"
                )

    def upload_to_youtube(self, sb, video, email, password, video_path) -> bool:
        youtube = YouTubeService(email, password, user_id=self.user_id)
        youtube.visit_page(sb)
        youtube.login(sb)
        return youtube.upload_video(
            sb, video_path, video["name"], "Uploaded from Google Drive"
        )

    def upload_to_instagram(self, sb, video, email, password, video_path) -> bool:
        instagram = InstagramService(email, password, user_id=self.user_id)
        instagram.visit_page(sb)
        instagram.login(sb)
        return instagram.upload_reel(sb, video_path, "Check out this cool video!")

    def upload_to_tiktok(self, sb, video, email, password, video_path) -> bool:
        tiktok = TikTokService(email, password, user_id=self.user_id)
        tiktok.visit_page(sb)
        tiktok.login(sb)
        return tiktok.upload_video(sb, video_path, "Amazing video, check it out!")
