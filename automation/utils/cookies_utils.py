import pickle
from datetime import datetime


def has_expired_cookie(cookie_file_path):
    try:
        with open(cookie_file_path, "rb") as file:
            cookies = pickle.load(file)
        current_time = datetime.now().timestamp()

        for cookie in cookies:
            if "expiry" in cookie and cookie["expiry"] < current_time:
                return True

        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
