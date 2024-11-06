import random
import time

from fake_useragent import UserAgent
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import BaseCase


def random_delay(min_delay=1, max_delay=3):
    """Introduce a random delay to mimic human interaction."""
    time.sleep(random.uniform(min_delay, max_delay))


def get_undetectable_options():
    """Set Chrome options to make Selenium undetectable."""
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-setuid-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Random window size
    resolutions = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (1600, 900),
    ]
    random_resolution = random.choice(resolutions)
    options.add_argument(f"--window-size={random_resolution[0]},{random_resolution[1]}")

    return options


def get_random_user_agent():
    """Generate a random user agent."""
    ua = UserAgent()
    return ua.random


def setup_undetectable_driver(sb: BaseCase):
    """Set up the driver with undetectable settings."""
    sb.driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
        },
    )
    sb.driver.execute_cdp_cmd("Network.enable", {})
    sb.driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": get_random_user_agent()},
    )

    options = get_undetectable_options()
    for option in options.arguments:
        sb.driver.add_argument(option)


def human_like_click(sb: BaseCase, selector):
    print(f"Clicking on {selector}")
    """Simulate human-like clicking behavior with slight randomness."""
    element = sb.find_element(selector)
    actions = ActionChains(sb.driver)

    # Randomize initial mouse movement
    actions.move_by_offset(random.randint(-5, 5), random.randint(-5, 5))
    actions.move_to_element(element)
    ## awit the element to be clickable
    sb.wait_for_element_clickable(selector)
    actions.pause(random.uniform(0.1, 0.3))
    actions.click()
    actions.perform()
    print(f"Clicked on {selector}")
    # Add a random delay after clicking
    random_delay(0.5, 1.5)


def human_like_type(sb: BaseCase, selector, text, error_rate=0.05):
    """Simulate human-like typing, with an optional error rate for typos."""
    element = sb.find_element(selector)
    for char in text:
        # Introduce typing errors occasionally
        if random.random() < error_rate:
            # Simulate a typo with backspace and retype
            typo_char = random.choice("abcdefghijklmnopqrstuvwxyz")
            element.send_keys(typo_char)
            time.sleep(random.uniform(0.05, 0.15))
            element.send_keys("\b")  # Press backspace
            time.sleep(random.uniform(0.1, 0.2))

        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))  # Delay between keypresses


def set_random_user_agent(sb: BaseCase):
    """Set a random user agent using Chrome DevTools Protocol."""
    user_agent = get_random_user_agent()
    sb.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
