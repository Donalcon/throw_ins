from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time
import pandas as pd


def handle_cookies(wait):
    try:
        consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
        consent_button.click()
        print("Cookies consent handled.")
    except TimeoutException:
        print("Consent button not found or not needed.")
    except Exception as e:
        print(f"Unexpected error when handling consent button: {str(e)}")


def click_load_more(wait, driver):
    while True:
        try:
            load_more_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="content"]/main/div[2]/section/div/div/div[6]/button/div[2]')))
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            load_more_button.click()
            print("Load more button clicked.")
            time.sleep(5)  # Wait for new data to load
            break
        except TimeoutException:
            print("Load more button not found, retrying...")
            time.sleep(2)
        except ElementClickInterceptedException:
            print("Load more button not clickable yet, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"Unexpected error when clicking load more button: {str(e)}")
            break


def slow_scroll(driver, increment=300, delay=1):
    last_height = driver.execute_script("return document.body.scrollHeight")
    new_height = 0
    while new_height < last_height:
        driver.execute_script(f"window.scrollBy(0, {increment});")
        time.sleep(delay)  # Wait for new content to load
        new_height += increment
        last_height = driver.execute_script("return document.body.scrollHeight")


def get_toggle_options(wait, driver, toggle_button_xpath, options_xpath):
    try:
        toggle_button = wait.until(EC.element_to_be_clickable((By.XPATH, toggle_button_xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", toggle_button)  # Scroll into view
        toggle_button.click()
        print(f"Clicked toggle button with XPath: {toggle_button_xpath}")
        time.sleep(2)  # Wait for the options to load

        options = driver.find_elements(By.XPATH, options_xpath)
        option_values = [option.text for option in options]
        print(f"Found options: {option_values}")

        # Close the dropdown menu by clicking the toggle button again
        toggle_button.click()
        time.sleep(1)  # Wait for the menu to close

        return option_values
    except TimeoutException:
        print(f"Toggle button not found with XPath: {toggle_button_xpath}")
        return []
    except Exception as e:
        print(f"Unexpected error when getting toggle options: {str(e)}")
        return []


# Set up WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()

# Wait initialization
wait = WebDriverWait(driver, 10)

# Open the URL
base_url = "https://inside.fifa.com/fifa-world-ranking/men?dateId=id13407"
driver.get(base_url)
handle_cookies(wait)

# Collect data for each combination of date and year
all_data = []


# Scroll to the "Load more" button and click it
click_load_more(wait, driver)

# Scroll slowly through the page to load all data
slow_scroll(driver, increment=300, delay=1)

# Collect data from all rows
data = []
row_index = 1
while True:
    try:
        country_xpath = f'//*[@id="content"]/main/div[2]/section/div/div/div[5]/table/tbody/tr[{row_index}]/td[2]/div/a[1]'
        points_xpath = f'//*[@id="content"]/main/div[2]/section/div/div/div[5]/table/tbody/tr[{row_index}]/td[3]/span'

        country_element = driver.find_element(By.XPATH, country_xpath)
        points_element = driver.find_element(By.XPATH, points_xpath)

        country = country_element.text
        points = points_element.text

        data.append({
            'country': country,
            'points': points
        })
        row_index += 1
    except Exception as e:
        print(f"No more rows found after index {row_index - 1}. Stopping the scraping process.")
        break

all_data.extend(data)

# Close the WebDriver
driver.quit()

# Convert the data to a DataFrame and save it
df = pd.DataFrame(all_data)
df['date'] = pd.to_datetime('2021-09-16')
df.to_csv('data/fifa_rankings/23_09_16.csv', index=False)
print("Data saved to fifa_world_ranking.csv")
