from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os


def handle_cookies(wait):
    try:
        # Attempt to find and click the consent button
        consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'fc-cta-consent')]")))
        consent_button.click()
        print("Cookies consent handled.")
    except TimeoutException:
        # If the button isn't found within the timeout, assume it's not needed this time
        print("Consent button not found or not needed.")
    except Exception as e:
        # Catch any other exceptions and log them
        print(f"Unexpected error when handling consent button: {str(e)}")


def count_urls_in_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            url_count = len(lines)
            return url_count
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        return 0


def count_urls_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        url_counts = {}
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path) and file_path.endswith('.txt'):
                url_count = count_urls_in_file(file_path)
                url_counts[file_name] = url_count
        return url_counts
    except FileNotFoundError:
        print(f"The directory {directory_path} does not exist.")
        return {}
