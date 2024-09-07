from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time


def read_urls_from_file(file_path):
    """Reads URLs from a text file and returns them as a list."""
    with open(file_path, 'r') as file:
        urls = file.read().splitlines()
    return urls


def combine_urls(file_paths):
    """Combines URLs from multiple files into a single list, removing duplicates."""
    combined_urls = set()
    for file_path in file_paths:
        urls = read_urls_from_file(file_path)
        combined_urls.update(urls)
    return list(combined_urls)


def capture_pitch_screenshot(url, filepath, hmap_filepath):
    # Set Chrome options
    options = ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Use ChromeDriverManager to automatically download and set up the driver
    service = Service(ChromeDriverManager().install())

    # Initialize the Chrome driver with options
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Maximize the window
        driver.maximize_window()

        # Navigate to the webpage
        driver.get(url)

        # Allow time for the page to load
        time.sleep(5)

        # Accept Cookies
        try:
            accept_cookies_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/button[2]")
            accept_cookies_button.click()
            print("Clicked on the 'Accept Cookies' button.")
        except NoSuchElementException:
            print("No 'Accept Cookies' button found, continuing.")

        # Close Promo Offer
        try:
            close_promo_button = driver.find_element(By.XPATH, "/html/body/div[7]/div/div[1]/button")
            close_promo_button.click()
            print("Closed the promo offer.")
        except NoSuchElementException:
            print("No promo offer found, continuing.")

        # Allow time for any animations or page changes
        time.sleep(2)

        # Click the additional button
        try:
            additional_button = driver.find_element(By.XPATH, "/html/body/div[4]/div[4]/ul/li[3]/a/span")
            additional_button.click()
            print("Clicked the additional button.")
            time.sleep(3)
        except NoSuchElementException:
            print("No additional button found, continuing.")

        # Allow time for the page to update
        time.sleep(2)

        # Get the home team name
        home_team = driver.find_element(By.XPATH, "/html/body/div[4]/div[3]/div[1]/div[2]/table/tbody/tr[1]/td[1]/a").text

        # Get the away team name
        away_team = driver.find_element(By.XPATH, "/html/body/div[4]/div[3]/div[1]/div[2]/table/tbody/tr[1]/td[3]/a").text

        # Get the date and time, strip whitespace after the comma
        date_text = driver.find_element(By.XPATH, "/html/body/div[4]/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]/div[3]/dl/dd[2]").text
        date_time = date_text.split(',')[1].strip()

        # Define the actions and their corresponding li index
        actions = {
            "dribbles": 3,
            "tackles_attempted": 4,
            "clearances": 6,
            "blocks": 7,
            "fouls": 9,
            "aerial_duels": 10,
            "loss_of_possession": 12
        }

        for action_name, li_index in actions.items():
            # Click the corresponding button
            try:
                action_button_xpath = f"/html/body/div[4]/div[5]/div[4]/ul/li[{li_index}]"
                action_button = driver.find_element(By.XPATH, action_button_xpath)
                action_button.click()
                print(f"Clicked the {action_name} button.")

                # Allow time for the page to update
                time.sleep(3)

                # Extract data for the home team using XPath
                try:
                    home_data_xpath = f"/html/body/div[4]/div[5]/div[4]/ul/li[{li_index}]/a/div/span[1]"
                    home_data_element = driver.find_element(By.XPATH, home_data_xpath)
                    home_data = home_data_element.text
                    print(f"{home_team} {action_name} data: {home_data}")
                except NoSuchElementException:
                    home_data = "N/A"
                    print(f"No data found for {home_team} {action_name}.")

                # Extract data for the away team using XPath
                try:
                    away_data_xpath = f"/html/body/div[4]/div[5]/div[4]/ul/li[{li_index}]/a/div/span[3]"
                    away_data_element = driver.find_element(By.XPATH, away_data_xpath)
                    away_data = away_data_element.text
                    print(f"{away_team} {action_name} data: {away_data}")
                except NoSuchElementException:
                    away_data = "N/A"
                    print(f"No data found for {away_team} {action_name}.")

                # Find the element containing the pitch
                pitch_element = driver.find_element(By.CSS_SELECTOR, ".pitch-stats-container")

                # Create the filename
                filename = f"{home_team}_{away_team}_{date_time.replace(' ', '_').replace(':', '-')}_{action_name}_{home_data}_{away_data}.png"
                # Take a screenshot of the specific element and save it with the constructed filename
                pitch_element.screenshot(filepath + filename)
                print(f"Screenshot saved as {filename}")

            except NoSuchElementException:
                print(f"Could not find the {action_name} button.")

        # Click into Heatmaps section
        try:
            heatmap_button = driver.find_element(By.CSS_SELECTOR, "#live-match-options > li:nth-child(4) > a")
            heatmap_button.click()
            print("Clicked into Heatmaps section.")
        except NoSuchElementException:
            print("No 'Heatmaps' button found, continuing.")

        # Allow time for the page to update
        time.sleep(2)

        # Extract touches data for home team
        try:
            home_touches = driver.find_element(By.CSS_SELECTOR, "#heatmap-pitches > div:nth-child(1) > div.heatmap-info-for-team > span").text
            print(f"{home_team} touches: {home_touches}")
        except NoSuchElementException:
            home_touches = "N/A"
            print(f"No touches data found for {home_team}.")

        # Extract touches data for away team
        try:
            away_touches = driver.find_element(By.CSS_SELECTOR, "#heatmap-pitches > div:nth-child(3) > div.heatmap-info-for-team > span").text
            print(f"{away_team} touches: {away_touches}")
        except NoSuchElementException:
            away_touches = "N/A"
            print(f"No touches data found for {away_team}.")

        # Save home team's heatmap
        try:
            home_heatmap = driver.find_element(By.CSS_SELECTOR, "#heatmap-pitches > div:nth-child(2) > div")
            filename = f"{home_team}_{date_time.replace(' ', '_').replace(':', '-')}_heatmap_{home_touches}.png"
            home_heatmap.screenshot(hmap_filepath + filename)
            print(f"Home team heatmap screenshot saved as {filename}")
        except NoSuchElementException:
            print("No heatmap found for the home team.")

        # Save away team's heatmap
        try:
            away_heatmap = driver.find_element(By.CSS_SELECTOR, "#heatmap-pitches > div:nth-child(4) > div")
            filename = f"{away_team}_{date_time.replace(' ', '_').replace(':', '-')}_heatmap_{away_touches}.png"
            away_heatmap.screenshot(hmap_filepath + filename)
            print(f"Away team heatmap screenshot saved as {filename}")
        except NoSuchElementException:
            print("No heatmap found for the away team.")

    finally:
        # Quit the driver
        driver.quit()


def parallel_scrape(urls, filepath, hmap_filepath, max_workers=4):
    """Parallelize the scraping process using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Pass the file paths as arguments to the capture_pitch_screenshot function
        future_to_url = {executor.submit(capture_pitch_screenshot, url, filepath, hmap_filepath): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()  # Get the result to raise any exceptions that occurred
            except Exception as exc:
                print(f"{url} generated an exception: {exc}")
