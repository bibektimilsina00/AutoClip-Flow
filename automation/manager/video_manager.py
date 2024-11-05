import os

from automation.utils.file_utils import FileUtils


class VideoManager:
    def __init__(self):
        self.video_data = []

    def load_video_data(self, folder_id, user_id):
        file_path = f"data/{user_id}/{folder_id}/video_data.json"
        if os.path.exists(file_path):
            self.video_data = FileUtils.load_json(file_path)

    def save_video_data(self, folder_id, user_id):
        FileUtils.save_json(
            self.video_data, f"data/{user_id}/{folder_id}/video_data.json"
        )

    def update_video_data(self, new_videos, folder_id, user_id):
        self.video_data = new_videos
        self.save_video_data(folder_id, user_id)

    def get_next_unuploaded_video(self):
        for video in self.video_data:
            if not video.get("is_uploaded"):
                return video
        return None

    def mark_as_uploaded(self, video_id, folder_id, user_id):
        for video in self.video_data:
            if video["id"] == video_id:
                video["is_uploaded"] = True

        self.save_video_data(folder_id, user_id)

    def deleted_video(self, video_path):
        os.remove(video_path)
