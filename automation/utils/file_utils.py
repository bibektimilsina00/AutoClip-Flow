import json
import os


class FileUtils:
    @staticmethod
    def get_project_root():
        # Get the directory of the current file (file_utils.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels to reach the project root
        return os.path.dirname(os.path.dirname(current_dir))

    @staticmethod
    def get_data_file_path(filename):
        project_root = FileUtils.get_project_root()
        return os.path.join(project_root, filename)

    @staticmethod
    def get_accounts_file_path():
        project_root = FileUtils.get_project_root()
        return os.path.join(project_root, "data", "accounts.json")

    @staticmethod
    def get_video_path(filename):
        project_root = FileUtils.get_project_root()
        return os.path.join(project_root, "video", filename)

    @staticmethod
    def save_json(data, filename):
        full_path = FileUtils.get_data_file_path(filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_json(filename):
        full_path = FileUtils.get_data_file_path(filename)
        with open(full_path, "r") as f:
            return json.load(f)
