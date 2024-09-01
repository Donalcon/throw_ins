from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
import time


def scrape_game_urls():
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

        # Navigate to the base URL
        base_url = "https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/8618/England-Premier-League"
        driver.get(base_url)

        # Allow time for the page to load
        time.sleep(5)

        # Accept Cookies
        try:
            accept_cookies_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/button[2]")
            accept_cookies_button.click()
            print("Cookies Accepted.")
        except NoSuchElementException:
            print("No 'Accept Cookies' button found, continuing.")

        # Close Promo Offer
        try:
            close_promo_button = driver.find_element(By.XPATH, "/html/body/div[8]/div/div[1]/button")
            close_promo_button.click()
            print("Closed the promo offer.")
        except NoSuchElementException:
            print("No promo offer found, continuing.")

        # Allow time for any animations or page changes
        time.sleep(2)

        all_game_urls = set()
        consecutive_no_new_urls = 0

        while consecutive_no_new_urls < 3:
            new_urls = 0

            # Iterate through each section (up to 7 sections)
            for section_index in range(1, 8):
                # Iterate through each link in the section (up to 20 links)
                for link_index in range(1, 21):
                    try:
                        game_link_xpath = f"/html/body/div[4]/div[3]/div[1]/div[3]/div[2]/div/div[4]/div[{section_index}]/div[2]/div/div[{link_index}]/div/div[2]/div[1]/a"
                        game_link = driver.find_element(By.XPATH, game_link_xpath)
                        url = game_link.get_attribute("href")
                        if url not in all_game_urls:
                            all_game_urls.add(url)
                            new_urls += 1
                            print(f"Found new game URL: {url}")
                    except NoSuchElementException:
                        # If the element isn't found, we might have reached the end of the links in this section.
                        break

            if new_urls == 0:
                consecutive_no_new_urls += 1
            else:
                consecutive_no_new_urls = 0

            # Attempt to click the "Next" button to load more games
            try:
                next_button = driver.find_element(By.XPATH, "/html/body/div[4]/div[3]/div[1]/div[3]/div[2]/div/div[2]/div/button[1]/div/img")
                next_button.click()
                print("Clicked the 'Next' button.")
                time.sleep(2)  # Allow time for new games to load
            except (NoSuchElementException, ElementClickInterceptedException):
                print("No 'Next' button found or unable to click, stopping.")
                break

        # Save the URLs to a text file
        with open("./prem/data/who_scored_urls/21-22_who_scored_urls.txt", "w") as file:
            for url in all_game_urls:
                file.write(url + "\n")

        print(f"Scraped {len(all_game_urls)} game URLs. Saved to '23-24_who_scored_urls.txt'.")

    finally:
        # Quit the driver
        driver.quit()

scrape_game_urls()
