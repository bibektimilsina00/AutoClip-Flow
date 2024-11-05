from enum import Enum, auto


class Platform(Enum):
    TIKTOK = auto()
    INSTAGRAM = auto()
    FACEBOOK = auto()
    YOUTUBE = auto()

    def get_url_prefix(self):
        prefixes = {
            Platform.TIKTOK: "https://tiktok.com/",
            Platform.INSTAGRAM: "https://instagram.com/",
            Platform.FACEBOOK: "https://facebook.com/",
            Platform.YOUTUBE: "https://studio.youtube.com/",
        }
        return prefixes[self]

    def get_login_url(self):
        login_urls = {
            Platform.TIKTOK: "https://www.tiktok.com/login/phone-or-email/email",
            Platform.INSTAGRAM: "https://www.instagram.com/accounts/login/",
            Platform.FACEBOOK: "https://www.facebook.com/login/",
            Platform.YOUTUBE: "https://studio.youtube.com/",
        }
        return login_urls[self]

    def get_upload_url(self):
        upload_urls = {
            Platform.TIKTOK: "https://www.tiktok.com/upload",
            Platform.INSTAGRAM: "https://instagram.com/",
            Platform.FACEBOOK: "https://www.facebook.com/upload/",
            Platform.YOUTUBE: "https://studio.youtube.com/",
        }
        return upload_urls[self]
