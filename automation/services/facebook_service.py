import os

from selenium.common.exceptions import TimeoutException, WebDriverException
from seleniumbase import BaseCase

from automation.enums.platform import Platform
from automation.manager.cookie_manager import CookieManager
from automation.utils.cookies_utils import has_expired_cookie
from automation.utils.logging_utils import logger
from automation.utils.sb_utils import sb_utils


class FacebookService:
    def __init__(self, email, password, user_id):
        self.platform = Platform.FACEBOOK
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
        logger.info(f"Logging on {self.platform.name} with {self.email}")
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
            sb.refresh()
            return True

        except Exception as e:
            logger.error(f"Error loading cookies for {self.platform.name}: {str(e)}")
            return False

    def _email_login(self, sb: BaseCase):
        try:
            sb.open(self.platform.get_login_url())
            # Basic email/password login flow; selectors may need tuning per account
            sb_utils.human_like_type(sb, 'input[name="email"]', self.email)
            sb_utils.human_like_type(sb, 'input[name="pass"]', self.password)
            sb_utils.human_like_click(sb, 'button[name="login"]')
            sb.sleep(2)
            # Save cookies after login
            if self._verify_login(sb):
                self._save_cookies(sb)
                return True
        except Exception as e:
            logger.error(f"Error during email login for Facebook: {str(e)}")
        return False

    def _verify_login(self, sb: BaseCase):
        try:
            # Quick heuristic: look for the profile nav or post composer
            return sb.is_element_present(
                'div[role="navigation"]'
            ) or sb.is_element_present('div[aria-label="Create"]')
        except Exception:
            return False

    def _save_cookies(self, sb: BaseCase):
        try:
            cookies = sb.driver.get_cookies()
            self.cookie_manager.save_cookies(self.platform.name, cookies)
            logger.info(f"Saved cookies for {self.email}")
        except Exception as e:
            logger.warning(f"Error saving cookies FACEBOOK: {str(e)}")

    def upload_to_page(
        self,
        sb: BaseCase,
        video_path: str,
        message: str = "",
        page_id: str | None = None,
    ) -> bool:
        if not self.is_logged_in:
            if not self.login(sb):
                logger.error(
                    f"Failed to log in. Cannot upload to Facebook page for: {self.email}"
                )
                return False

        try:
            # Navigate to the page publishing UI if page_id provided, otherwise open generic composer
            if page_id:
                sb.open(f"https://www.facebook.com/pages/{page_id}/publish")
            else:
                sb.open(self.platform.get_url_prefix())

            # Try to open post composer
            sb.sleep(2)
            # Choose file input if present
            if sb.is_element_present('input[type="file"]'):
                sb.choose_file('input[type="file"]', video_path)
            else:
                # Fallback: try to click create post then upload
                try:
                    sb_utils.human_like_click(sb, 'div[aria-label="Create a post"]')
                    sb.sleep(1)
                    sb.choose_file('input[type="file"]', video_path)
                except Exception:
                    logger.warning("Could not find upload input for Facebook page")

            sb.sleep(2)
            # Enter message if possible
            try:
                if message:
                    sb_utils.human_like_type(sb, 'div[role="textbox"]', message)
            except Exception:
                pass

            # Click Post/Share button
            possible_selectors = [
                'div[aria-label="Post"] button',
                'div[aria-label="Publish"] button',
                'button:contains("Post")',
                'button:contains("Share")',
            ]
            for sel in possible_selectors:
                try:
                    if sb.is_element_present(sel):
                        sb_utils.human_like_click(sb, sel)
                        break
                except Exception:
                    continue

            sb.sleep(3)
            logger.info(f"Attempted upload to Facebook Page for {self.email}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to Facebook Page: {str(e)}")
            return False

    def upload_to_group(
        self,
        sb: BaseCase,
        video_path: str,
        message: str = "",
        group_id: str | None = None,
    ) -> bool:
        if not self.is_logged_in:
            if not self.login(sb):
                logger.error(
                    f"Failed to log in. Cannot upload to Facebook group for: {self.email}"
                )
                return False

        try:
            # Navigate to group post composer
            if group_id:
                sb.open(f"https://www.facebook.com/groups/{group_id}")
            else:
                sb.open(self.platform.get_url_prefix())

            sb.sleep(2)
            # Try to click on create post in group
            try:
                sb_utils.human_like_click(sb, 'div[aria-label="Create a public post"]')
            except Exception:
                # Fallback selectors
                try:
                    sb_utils.human_like_click(sb, 'div[aria-label="Create a post"]')
                except Exception:
                    pass

            sb.sleep(1)
            if sb.is_element_present('input[type="file"]'):
                sb.choose_file('input[type="file"]', video_path)

            if message:
                try:
                    sb_utils.human_like_type(sb, 'div[role="textbox"]', message)
                except Exception:
                    pass

            # Click Post button
            if sb.is_element_present('button:contains("Post")'):
                sb_utils.human_like_click(sb, 'button:contains("Post")')

            sb.sleep(3)
            logger.info(f"Attempted upload to Facebook Group for {self.email}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to Facebook Group: {str(e)}")
            return False
