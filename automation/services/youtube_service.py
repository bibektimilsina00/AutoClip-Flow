import os
import re

from selenium.common.exceptions import (
    InvalidCookieDomainException,
    TimeoutException,
    WebDriverException,
)
from seleniumbase import BaseCase

from automation.enums.platform import Platform
from automation.manager.cookie_manager import CookieManager
from automation.utils.cookies_utils import has_expired_cookie
from automation.utils.logging_utils import logger
from automation.utils.sb_utils import sb_utils


class YouTubeService:
    def __init__(self, email, password, user_id):
        self.platform = Platform.YOUTUBE
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

    def _verify_login(self, sb: BaseCase):
        try:
            return sb.is_element_present('button[aria-label="Create"]')
        except TimeoutException:
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
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
        sb.open("https://youtube.com/")
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
            # Open YouTube Studio
            sb.open(self.platform.get_login_url())

            # Wait for and enter email
            sb.wait_for_element_present("#identifierId", timeout=10)
            sb_utils.human_like_type(sb, "#identifierId", self.email)

            # Click Next
            self.click_next_button_for_login(sb)

            # Wait for and enter password
            sb.wait_for_element_present('input[type="password"]', timeout=10)
            sb_utils.human_like_type(sb, 'input[type="password"]', self.password)

            # Click Next to submit password
            self.click_next_button_for_login(sb)

            # Wait for login to complete
            sb.wait_for_element_present('button[aria-label="Create"]', timeout=20)

            logger.info("Login successful")
            self.save_cookies(sb)
            return True

        except Exception as e:
            logger.error(f"Error during login process: {str(e)}")
            logger.warning("Login failed")
            return False

    def save_cookies(self, sb: BaseCase):
        cookies = sb.driver.get_cookies()
        self.cookie_manager.save_cookies(self.platform.name, cookies)

    def refactor_content(self, content, is_title=False):
        # Remove file extensions
        content = re.sub(
            r"\.(mp4|avi|mov|flv|wmv|mkv)$", "", content, flags=re.IGNORECASE
        )

        # Remove extra spaces
        content = " ".join(content.split())

        # Capitalize first letter of each sentence
        content = ". ".join(s.capitalize() for s in content.split(". "))

        if is_title:
            # Ensure title is not longer than 100 characters
            if len(content) > 100:
                content = content[:97] + "..."

            # Capitalize words in title (except for small words)
            small_words = {
                "a",
                "an",
                "and",
                "as",
                "at",
                "but",
                "by",
                "for",
                "in",
                "of",
                "on",
                "or",
                "the",
                "to",
                "with",
            }
            content = " ".join(
                word.capitalize() if word.lower() not in small_words else word
                for word in content.split()
            )

        return content.strip()

    def upload_video(self, sb: BaseCase, file_path, title, description):
        if not self.is_logged_in:
            logger.error("User cannot log in to YouTube. Check your login credentials.")
            return False

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        refined_title = self.refactor_content(title, is_title=True)
        refined_description = self.refactor_content(description)

        logger.info(f"Refined title: {refined_title}")
        logger.info(f"Refined description: {refined_description}")

        try:
            sb.open(self.platform.get_url_prefix())
            sb.wait_for_element_clickable("#create-icon", timeout=20)
            sb_utils.human_like_click(sb, "#create-icon")
            sb.wait_for_element_clickable(
                "tp-yt-paper-item[test-id='upload-beta']", timeout=10
            )
            sb_utils.human_like_click(sb, "tp-yt-paper-item[test-id='upload-beta']")

            sb.wait_for_element_present("input[type='file']", timeout=10)
            sb.choose_file("input[type='file']", file_path)

            # # Wait for the title field to be editable
            # sb.wait_for_element_present("#title-textarea", timeout=30)

            # # Retrieve the current title by using text content instead of value
            # current_title = sb.get_text(
            #     "#title-textarea"
            # ).strip()  # Adjusted to get the text directly

            # # Only set the title if the current title does not match the refined title
            # if current_title == "":
            #     sb.type("#title-textarea", refined_title)
            # else:
            #     logger.warning("Current title is not empty, skipping title input.")

            # # Wait for the description field to be editable
            # sb.wait_for_element_present("#description-textarea", timeout=30)
            # sb.type("#description-textarea", refined_description)
            sb_utils.random_delay(1, 3)
            # Wait a moment to ensure the text is input

            # Wait for the "No, it's not 'Made for Kids'" option to be present
            sb.wait_for_element_present(
                'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]',
                timeout=10,
            )
            sb_utils.human_like_click(
                sb, 'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]'
            )

            for _ in range(3):  # Click "Next" three times
                sb.wait_for_element_clickable('button[aria-label="Next"]', timeout=10)
                sb_utils.human_like_click(sb, 'button[aria-label="Next"]')

            # Select the "Public" option
            sb.wait_for_element_clickable("[name='PUBLIC']", timeout=10)
            sb_utils.human_like_click(sb, "[name='PUBLIC']")

            # Click the "Publish" button
            sb.wait_for_element_clickable('button[aria-label="Publish"]', timeout=10)
            sb_utils.human_like_click(sb, 'button[aria-label="Publish"]')

            # Wait for the confirmation dialog with "Video published" to appear
            # sb.wait_for_element_present(
            #     'tp-yt-paper-dialog[aria-labelledby="dialog-title"]', timeout=30
            # )

            # if sb.is_element_visible(
            #     "h1#dialog-title"
            # ) and "Video published" in sb.get_text("h1#dialog-title"):
            #     print("Video successfully published!")

            # sb.click('ytcp-icon-button[aria-label="Close"]')

            return True

        except Exception as e:
            logger.error(f"Error during video upload: {str(e)}")
            return False

    def click_next_button_for_login(self, sb: BaseCase):
        max_retries = 3
        retry_delay = 2
        button_selectors = [
            'button[jsname="LgbsSe"]',
            'button:contains("Next")',
            'button[type="button"]:contains("Next")',
            "#identifierNext button",
            "#passwordNext button",
            "button.VfPpkd-LgbsSe-OWXEXe-k8QpJ",
            "button.nCP5yc",
            'button span:contains("Next")',  # New selector targeting the span inside the button
        ]

        for attempt in range(max_retries):
            try:
                for selector in button_selectors:
                    try:
                        if sb.is_element_visible(selector):
                            # If the selector is for the span, we need to click its parent button
                            if 'span:contains("Next")' in selector:
                                sb.execute_script(
                                    "arguments[0].click();",
                                    sb.find_element(selector).find_element_by_xpath(
                                        ".."
                                    ),
                                )
                            else:
                                sb.click(selector)
                            logger.info(
                                f"Successfully clicked button with selector: {selector}"
                            )
                            return
                    except Exception as e:
                        logger.debug(f"Failed to click selector {selector}: {str(e)}")
                        continue
                raise Exception("No clickable Next button found")
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to click Next button (attempt {attempt + 1}). Retrying..."
                    )
                    sb.sleep(retry_delay)
                else:
                    logger.error(
                        f"Failed to click Next button after {max_retries} attempts."
                    )
                    sb.save_screenshot("failed_login_screenshot.png")
                    sb.save_page_source("failed_login_page_source.html")
                    raise e
