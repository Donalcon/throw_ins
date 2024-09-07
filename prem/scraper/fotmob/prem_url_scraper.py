import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.scraper.common_functions import handle_cookies


def prem_url_scraper(season_1, season_2, new_url_scrape_page):
    urls = []  # List to store all extracted URLs
    # Set up WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    # Wait initialization
    wait = WebDriverWait(driver, 5)
    max_link_index = 22  # Maximum number of links to check
    max_attempts = 8  # Maximum attempts to find new links

    while 2024 <= season_1 <= 2025:
        # while 38 >= page >= 0: ** only use for full season scrape
        page = new_url_scrape_page
        base_url = f"https://www.fotmob.com/en-GB/leagues/47/matches/premier-league?season={season_1}-{season_2}&page={page}"
        driver.get(base_url)
        handle_cookies(wait)

        link_index = 1
        section_found = False
        new_links_found = False  # This flag will determine if we found new links on the current page

        # Try to find links assuming single section first
        attempts = 0
        while link_index <= max_link_index:
            try:
                link_xpath = f"//*[@id='__next']/main/main/section/div[3]/section/section/a[{link_index}]"
                link_element = wait.until(EC.presence_of_element_located((By.XPATH, link_xpath)))
                link_url = link_element.get_attribute('href')
                if link_url and link_url not in urls:
                    urls.append(link_url)
                    print("Added URL from single section:", link_url)
                    new_links_found = True
                link_index += 1
            except TimeoutException:
                if not section_found:
                    section_found = True
                    section_index = 1
                    link_index = 1
                    continue  # Try to check for multiple sections
                else:
                    break  # No more links in both single and multiple sections

        if section_found:
            while True:
                try:
                    link_xpath = f'//*[@id="__next"]/main/main/section/div/div[2]/section/section[{section_index}]/a[{link_index}]'
                    link_element = wait.until(EC.presence_of_element_located((By.XPATH, link_xpath)))
                    link_url = link_element.get_attribute('href')
                    if link_url and link_url not in urls:
                        urls.append(link_url)
                        print("Added URL from multiple sections:", link_url)
                        new_links_found = True
                    link_index += 1
                except TimeoutException:
                    section_index += 1
                    link_index = 1
                    attempts += 1
                    if section_index > 8 or attempts >= max_attempts:  # Reasonable section limit
                        break

        # page += 1  # Move to the next page if any links were found
        if not new_links_found:
            break  # Stop pagination

    # Close the WebDriver
    driver.quit()

    # Read the master_url.txt and remove any duplicates from the newly scraped URLs
    master_url_file = './prem/data/new_urls/master_urls.txt'
    if os.path.exists(master_url_file):
        with open(master_url_file, 'r') as f:
            master_urls = set(f.read().splitlines())  # Read existing URLs and convert them to a set for faster lookup
        # Remove any new URLs that are already present in the master URL file
        new_urls = [url for url in urls if url not in master_urls]
    else:
        new_urls = urls  # If the master_url.txt file does not exist, use all scraped URLs

    # Save the new URLs that are not present in the master_url.txt file to a new file
    gameweek = new_url_scrape_page + 1
    new_urls_file = f'./prem/data/new_urls/prem_GW{gameweek}.txt'
    with open(new_urls_file, 'w') as f:
        for url in new_urls:
            f.write(f"{url}\n")

    # Return the file path to the new URLs file and the updated list of new URLs
    return new_urls
