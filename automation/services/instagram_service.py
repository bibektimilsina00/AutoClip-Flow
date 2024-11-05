import os

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    InvalidCookieDomainException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from seleniumbase import BaseCase

from automation.config.config import Config
from automation.enums.platform import Platform
from automation.manager.cookie_manager import CookieManager
from automation.utils.cookies_utils import has_expired_cookie
from automation.utils.logging_utils import logger
from automation.utils.sb_utils import sb_utils


class InstagramService:
    def __init__(self, email, password, user_id):
        self.platform = Platform.INSTAGRAM
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
        try:
            sb.open(self.platform.get_login_url())

            # Use explicit waits for better reliability
            sb.wait_for_element_visible('input[name="username"]', timeout=10)
            sb_utils.human_like_type(sb, 'input[name="username"]', self.email)

            sb.wait_for_element_visible('input[name="password"]', timeout=10)
            sb_utils.human_like_type(sb, 'input[name="password"]', self.password)

            sb.wait_for_element_clickable('button[type="submit"]', timeout=10)
            sb_utils.human_like_click(sb, 'button[type="submit"]')

            # Wait for either successful login or potential errors
            sb.wait_for_element_present(
                'svg[aria-label="New post"]',  # Success indicator
                timeout=15,
            )

            sb_utils.random_delay(3, 5)
            if sb.is_element_present('button[aria-label="Save Info"]'):
                if self._handle_save_info_prompt(sb):
                    logger.info("Handled 'Save Info' prompt")
                    return True
            else:
                logger.info("No 'Save Info' prompt appeared")
                self._save_cookies(sb)
                return True

            if self._verify_login(sb):
                logger.info(f"Login successful for {self.email}")
                sb.open(self.platform.get_url_prefix())
                sb_utils.random_delay(1, 3)
                self._save_cookies(sb)
                return True
            else:
                logger.warning(f"Login failed for {self.email}")
                error_message = sb.find_element('div[role="alert"]', timeout=5).text
                logger.error(f"Login error: {error_message}")
                return False

        except TimeoutException as e:
            logger.error(f"Timeout during login for {self.email}: {str(e)}")
        except NoSuchElementException as e:
            logger.error(f"Element not found during login for {self.email}: {str(e)}")
        except ElementClickInterceptedException as e:
            logger.error(
                f"Element click intercepted during login for {self.email}: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during login for {self.email}: {str(e)}")

        return False

    def _handle_save_info_prompt(self, sb: BaseCase):
        try:
            save_info_button = sb.find_element(
                'button[aria-label="Save Info"]', timeout=5
            )
            if save_info_button:
                sb_utils.human_like_click(sb, save_info_button)
                sb_utils.random_delay(4, 6)  # Wait for save info process
                return True
        except (TimeoutException, NoSuchElementException):
            logger.info("No 'Save Info' prompt appeared")
        except Exception as e:
            logger.warning(f"Error handling 'Save Info' prompt: {str(e)}")
        return False

    def _verify_login(self, sb: BaseCase):
        try:
            sb_utils.random_delay(4, 6)
            return sb.is_element_visible('svg[aria-label="New post"]')
        except Exception as e:
            logger.warning(f"Error checking login status: {str(e)}")
            return False

    def _save_cookies(self, sb: BaseCase):
        try:
            cookies = sb.driver.get_cookies()
            self.cookie_manager.save_cookies(self.platform.name, cookies)
            logger.info(f"Saved cookies for {self.email}")
        except Exception as e:
            logger.warning(f"Error saving cookies INSTAGRAM: {str(e)}")

    def upload_reel(self, sb: BaseCase, video_path, caption) -> bool:
        try:
            sb.open(self.platform.get_upload_url())
            sb_utils.human_like_click(sb, 'a[role="link"]:contains("Create")')
            sb.sleep(2)

            sb.choose_file('input[type="file"]', video_path)
            sb.sleep(2)

            if self._is_share_as_reel_apper(sb):
                sb.sleep(2)
                ok_button_selector = "button[type='button']:contains('OK')"
                if sb.is_element_visible(ok_button_selector):
                    sb_utils.human_like_click(sb, ok_button_selector)
                    print("Clicked OK button.")
                else:
                    print("OK button is not visible.")

            # Press Next
            sb_utils.human_like_click(sb, "div[role='button']:contains('Next')")
            sb.sleep(2)
            # Press Next again
            sb_utils.human_like_click(sb, "div[role='button']:contains('Next')")
            sb.sleep(2)

            # Write caption
            sb_utils.human_like_type(
                sb, "div[aria-label='Write a caption...']", caption
            )
            sb_utils.random_delay(4, 6)

            # sb.wait_for_element_clickable("div[role='button']:contains('Share')")
            # sb.sleep(2)
            # sb.click("div[role='button']:contains('Share')")

            # Press Share button
            max_retries = 5
            share_button_selector = (
                "div[aria-label='Create new post'] div[role='button']:contains('Share')"
            )
            for attempt in range(max_retries):
                try:
                    # Wait for the element to be present and visible
                    sb.wait_for_element_visible(share_button_selector, timeout=10)
                    logger.info("Found Share button")
                    sb_utils.human_like_click(sb, share_button_selector)

                    logger.info("Successfully clicked Share button")
                    break
                except Exception as e:
                    logger.warning(
                        f"Error while clicking Share button (attempt {attempt + 1}): {str(e)}"
                    )
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed to click Share button after all retries: {str(e)}"
                        )
                        return False
                    sb.sleep(2)  # Reduced sleep time to 2 seconds

            try:
                # Wait for the success message to appear
                success_message_selector = "span:contains('Your reel has been shared.')"
                if sb.wait_for_element_visible(
                    success_message_selector, timeout=180
                ):  # Increased timeout to 3 minutes
                    logger.info("Reel upload success message appeared")
                    return True
                else:
                    logger.error("Success message not visible")
                    return False
            except Exception as e:
                logger.error(
                    f"Error while waiting for success message or return to home page: {e}"
                )
                return False

        except Exception as e:
            logger.error(f"Error during reel upload: {str(e)}")
            return False

    def _is_share_as_reel_apper(self, sb: BaseCase):
        try:
            # Use a CSS selector to locate the message element
            message_selector = "span:contains('Video posts are now shared as reels')"
            return sb.is_element_visible(message_selector)
        except Exception as e:
            print(f"Error occurred: {e}")
            return False
