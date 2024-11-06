import os

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    InvalidCookieDomainException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumbase import BaseCase

from automation.enums.platform import Platform
from automation.manager.cookie_manager import CookieManager
from automation.utils.cookies_utils import has_expired_cookie
from automation.utils.logging_utils import logger
from automation.utils.sb_utils import sb_utils


class TikTokService:
    def __init__(self, email, password, user_id):
        self.platform = Platform.TIKTOK
        self.email = email
        self.password = password
        self.cookie_manager = CookieManager(email, user_id)
        self.is_logged_in = False
        self.login_attempts = 0
        self.max_login_attempts = 3

    def visit_page(self, sb: BaseCase):
        logger.info(f"visiting {self.platform.name}")
        sb.open(self.platform.get_url_prefix())

    def login(self, sb: BaseCase):
        logger.info(f"Loging on {self.platform.name} with {self.email}")
        while self.login_attempts < self.max_login_attempts:
            try:
                if self._check_cookies():
                    if self._cookie_login(sb):
                        self.is_logged_in = True
                        logger.info(f"Successfully logged in with cookies {self.email}")
                    else:
                        self._email_login(sb)
                else:
                    self._email_login(sb)

                if self._verify_login(sb):
                    self.is_logged_in = True
                    logger.info(f"Successfully logged in for {self.email}")
                    return True
                else:
                    logger.warning(
                        f"Login attempt {self.login_attempts + 1} failed for {self.email}"
                    )
                    self.login_attempts += 1
            except Exception as e:
                logger.error(
                    f"Error during login attempt {self.login_attempts + 1} for {self.email}: {str(e)}"
                )
                self.login_attempts += 1

        logger.error(
            f"Failed to log in after {self.max_login_attempts} attempts for {self.email}"
        )
        return False

    def _check_cookies(self):
        cookies = self.cookie_manager.get_cookies(self.platform.name)

        if cookies and not has_expired_cookie(cookies):
            logger.info(f"Valid cookie found for {self.platform.name}: {self.email}")
            return True
        else:
            logger.info(f"No valid cookie found for {self.platform.name}: {self.email}")
            return False

    def _cookie_login(self, sb: BaseCase):
        logger.info(f"Loading cookies for {self.platform.name}: {self.email}")
        try:
            cookies = self.cookie_manager.get_cookies(self.platform.name)
            for cookie in cookies:
                sb.driver.add_cookie(cookie)
            print("Cookies loaded successfully!")
            sb.refresh()
            return True

        except Exception as e:
            logger.error(f"Error loading cookies for {self.platform.name}: {str(e)}")
            return False

    def _email_login(self, sb: BaseCase):
        logger.info(f"Logging in with email for {self.platform.name}: {self.email}")
        try:
            sb.open(self.platform.get_login_url())
            sb_utils.human_like_type(sb, 'input[name="username"]', self.email)
            sb_utils.human_like_type(sb, 'input[type="password"]', self.password)
            sb_utils.human_like_click(sb, 'button[type="submit"]')

            WebDriverWait(sb.driver, 10).until(
                EC.url_changes(self.platform.get_login_url())
            )
        except Exception as e:
            logger.error(
                f"Error logging in with email for {self.platform.name}: {str(e)}"
            )
            raise

    def _verify_login(self, sb: BaseCase):
        try:
            if sb.wait_for_element_present('div[data-e2e="upload-icon"]', timeout=10):
                logger.info(f"Login verified for {self.email}")
                self._save_cookies(sb)
                return True
            else:
                logger.warning(f"Login verification failed for {self.email}")
                return False
        except Exception as e:
            logger.error(f"Error verifying login status for {self.email}: {str(e)}")
            return False

    def _save_cookies(self, sb: BaseCase):
        try:
            cookies = sb.driver.get_cookies()
            self.cookie_manager.save_cookies(self.platform.name, cookies)
            logger.info(f"Saved cookies for {self.email}")
        except Exception as e:
            logger.warning(f"Error saving cookies INSTAGRAM: {str(e)}")

    def upload_video(self, sb: BaseCase, video_path, description):
        if not self.is_logged_in:
            if not self.login(sb):
                logger.error(f"Failed to log in. Cannot upload video for: {self.email}")
                return False

        try:
            logger.info(f"Opening {self.platform.name} Upload page for: {self.email}")
            sb.open(self.platform.get_upload_url())

            sb.choose_file('input[type="file"]', video_path)

            # logger.info(f"Typing description: {description}")
            # sb_utils.human_like_type("#caption", description)

            # logger.info("Adding hashtags")
            # self.add_hashtags(sb, ["#YourHashtags"])
            # sb.wait(2)
            sb.scroll_to('button:contains("Post")')
            sb.wait_for_element_clickable('button:contains("Post")', timeout=30)

            sb_utils.human_like_click(sb, 'button:contains("Post")')

            logger.info("Waiting for upload confirmation")

            confirmation_modal_selector = (
                '.TUXModal[title="Your video has been uploaded"]'
            )
            if sb.wait_for_element_present(confirmation_modal_selector, timeout=60):
                logger.info(f"Video uploaded to {self.platform.name} {self.email}")
            return True

        except TimeoutException as e:
            logger.error(f"Timeout error for {self.email}: {str(e)}")

        except WebDriverException as e:
            logger.error(f"WebDriver error for {self.email}: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error for {self.email}: {str(e)}")

        return False

    def add_hashtags(self, sb: BaseCase, hashtags):
        logger.info("Adding hashtags")
        pass
        for hashtag in hashtags:
            sb_utils.human_like_click(sb, 'button[aria-label="Add hashtag"]')
            sb_utils.human_like_type(sb, 'input[aria-label="Add hashtag"]', hashtag)
            sb.press("Enter")
