from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from scraper.common_functions import handle_cookies

seasons = ['2024', '2023', '2018-2019', '2019']
urls = []  # List to store all extracted URLs
page = 0

# Set up WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()

# Wait initialization
wait = WebDriverWait(driver, 5)

for season in seasons:
    more_pages = True
    while more_pages:
        base_url = f"https://www.fotmob.com/en-GB/leagues/10607/matches/euro-qualification/by-date?season={season}&page={page}"
        driver.get(base_url)
        handle_cookies(wait)

        link_index = 1
        section_found = False
        new_links_found = False

        # Try to find links assuming single section first
        while True:
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

        # Handling multiple sections after single section fails
        if section_found:
            while True:
                try:
                    link_xpath = f"//*[@id='__next']/main/main/section/div[3]/section/section[{section_index}]/a[{link_index}]"
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
                    if section_index > 4:  # Reasonable section limit
                        print("No more sections to check, changing page.")
                        break

        page += 1  # Increment the page number to fetch more results
        if new_links_found:
            page += 1  # Move to the next page if links were found
        else:
            more_pages = False

# Close the WebDriver
driver.quit()

# Output collected URLs
print("Collected URLs:", urls)
# save urls
with open('data/euro_qual_urls.txt', 'w') as f:
    for url in urls:
        f.write(f"{url}\n")