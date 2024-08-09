from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.scraper.common_functions import handle_cookies

urls = []  # List to store all extracted URLs
page = 2

# Set up WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()

# Wait initialization
wait = WebDriverWait(driver, 5)
more_pages = True

while more_pages:  # This loop handles the pagination
    print(page)
    base_url = f"https://www.fotmob.com/en-GB/leagues/44/matches/copa-america?page={page}"
    driver.get(base_url)
    handle_cookies(wait)

    link_index = 1
    section_found = False
    new_links_found = False  # This flag will determine if we found new links on the current page

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
                if section_index > 8:  # Reasonable section limit
                    break

    page -= 1  # Move to the next page if any links were found
    if not new_links_found:
        more_pages = False  # No new links found on the last page, stop pagination

# Close the WebDriver
driver.quit()

# Output collected URLs
print("Collected URLs:", urls)
# Save urls
with open('data/new_urls/new_copa_2024_urls.txt', 'w') as f:
    for url in urls:
        f.write(f"{url}\n")
