from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import pandas as pd


def future_match_scraper(test_url):
    # Set up WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    # Navigate to the page
    driver.get(test_url)

    # Wait up to 10 seconds for the necessary elements to be ready
    wait = WebDriverWait(driver, 10)

    # Cookies consent
    try:
        consent_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'fc-cta-consent')]")))
        consent_button.click()
    except Exception as e:
        print("Consent button not found or not clickable.", e)

    # Scrape team names
    try:
        team1_xpath = "/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[1]/a/div/span/span[2]"
        team2_xpath = "/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[3]/a/div/span/span[2]"
        team1_name = wait.until(EC.visibility_of_element_located((By.XPATH, team1_xpath))).text
        team2_name = wait.until(EC.visibility_of_element_located((By.XPATH, team2_xpath))).text
        print(team1_name)
        print(team2_name)
    except TimeoutException:
        print(f"Team names not found for URL: {test_url}")
        driver.quit()
        return pd.DataFrame()

    # Scrape datetime, stadium, attendance, and competition
    match_datetime, stadium, competition, venue, referee, venue_href = (
        None, None, None, None, None, None)

    try:
        datetime_xpath = "//*[@id='__next']/main/main/div[2]/div/div[1]/div[1]/div/section/div/div[2]/section/ul/li[1]/div/time"
        match_datetime = wait.until(EC.visibility_of_element_located((By.XPATH, datetime_xpath))).get_attribute('datetime')
    except TimeoutException:
        print(f"Datetime not found for URL: {test_url}")

    # Extract referee
    referee = extract_attribute_data(driver, "Reveree")
    if not referee:
        referee = extract_attribute_data(driver, "Referee")

    # Extract venue
    venue_data = extract_attribute_data(driver, "Venue")
    if venue_data:
        venue, venue_href = venue_data

    try:
        competition_xpath = "//*[@id='__next']/main/main/div[2]/div/div[1]/div[1]/div/section/div/div[1]/div/div[2]/a/span"
        competition = wait.until(EC.visibility_of_element_located((By.XPATH, competition_xpath))).text
    except TimeoutException:
        print(f"Competition not found for URL: {test_url}")


    team1_data = {
        'team': team1_name, 'opp': team2_name,
        'datetime': match_datetime, 'stadium': venue, 'referee': referee,
        'competition': competition,'venue_href': venue_href
    }
    team2_data = {
        'team': team2_name, 'opp': team1_name,
        'datetime': match_datetime, 'stadium': venue, 'referee': referee,
        'competition': competition, 'venue_href': venue_href
    }

    # Create DataFrames
    df_team1 = pd.DataFrame([team1_data])
    df_team2 = pd.DataFrame([team2_data])
    # Combine both teams into a single DataFrame for comparison or output
    df = pd.concat([df_team1, df_team2]).reset_index(drop=True)

    # Close the WebDriver
    driver.quit()

    # DATA CLEANING
    # remove any brackets from df
    df = df.replace({'\(': '', '\)': ''}, regex=True)
    # remove any % from df
    df = df.replace({'%': ''}, regex=True)
    # fill any empty cells with nan
    df = df.replace('', pd.NA)

    # make all column names lowercase and replace spaces with underscores
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df


def extract_attribute_data(driver, class_name_keyword):
    try:
        # Find the element using XPath with contains() to match partial class names
        element = driver.find_element(By.XPATH, f"//*[contains(@class, '{class_name_keyword}')]")
        text = element.find_element(By.TAG_NAME, 'span').text
        if 'Venue' in class_name_keyword:
            href = element.get_attribute('href')
            return text, href
        return text
    except Exception as e:
        print(f"Failed to extract data for {class_name_keyword}: {e}")