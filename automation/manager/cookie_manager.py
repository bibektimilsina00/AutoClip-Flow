import os
import pickle

from automation.utils.file_utils import FileUtils


class CookieManager:
    def __init__(self, email, user_id):
        self.email = email
        self.user_id = user_id

    def get_cookies(self, domain):
        cookies_path = os.path.join(
            FileUtils.get_project_root(),
            "cookies",
            self.user_id,
            self.email,
            f"{domain}_cookies.pkl",
        )
        if os.path.exists(cookies_path):
            with open(cookies_path, "rb") as f:
                return pickle.load(f)
        return []

    def save_cookies(self, domain, cookies):
        cookies_path = os.path.join(
            FileUtils.get_project_root(),
            "cookies",
            self.user_id,
            self.email,
            f"{domain}_cookies.pkl",
        )
        os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
        with open(cookies_path, "wb") as f:
            pickle.dump(cookies, f)
