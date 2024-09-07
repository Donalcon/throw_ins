import datetime
from datetime import datetime
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys


def driver_code():
    # Set Chrome options
    options = ChromeOptions()

    useragentarray = [
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.76 Mobile Safari/537.36"
    ]

    # Add various options to the Chrome instance
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("disable-infobars")
    options.add_argument("disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Set page load strategy directly in the options
    options.page_load_strategy = 'normal'

    # Use ChromeDriverManager to automatically download and set up the driver
    service = Service(ChromeDriverManager().install())

    # Initialize the Chrome driver with options
    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    # Modify the WebDriver properties to avoid detection
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    # Override the user agent
    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride", {"userAgent": useragentarray[0]}
    )

    # Add more options if necessary
    options.add_argument("--disable-popup-blocking")

    # Navigate to the desired website
    driver.get("https://www.bet365.com/#/AC/B1/C1/D1002/E91422157/G40/H^1/")

    # Set the window size to simulate a mobile device
    driver.set_window_size(390, 844)

    # Allow time for the page to load
    time.sleep(1)

    return driver


# Remove Loader
def remove_Loader(driver):
    driver.execute_script("document.querySelector('.bl-Preloader').remove();")


def accept_cookies(driver):
    cookies = driver.find_elements(By.CSS_SELECTOR, ".ccm-CookieConsentPopup_Accept ")
    if len(cookies) > 0:
        cookies[0].click()


def open_tab(driver,link):
    driver.execute_script(f"""window.open('{link}', "_blank");""")
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])


# Sorry No Markets Error
def no_markets(driver):
    markets = driver.find_elements(By.CSS_SELECTOR, ".sm-NoAvailableMarkets_Header ")
    if len(markets) > 0:
        open_tab(driver)


def sort_string(string):
    string = ''.join(e for e in string if e.isalnum())
    string = string.lower()
    return string


def get_odds_from_market_name(driver, market_type_element, market_names, market_odds, market_type, home_teams,
                              home_team, away_teams, away_team, match_date_and_time, match_datetime, match_ids,
                              time_scraped):
    if market_type_element[0].text == "Goals Over/Under":
        market_line = test[i].find_elements(
            By.CSS_SELECTOR, ".srb-ParticipantLabelCentered.gl-Market_General-cn1 "
        )
        market_name = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-MarketColumnHeader "
        )
        odds = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-ParticipantOddsOnly_Odds"
        )
        url = driver.current_url
        url = url.split("/")
        match_ids.append(url[8])
        match_ids.append(url[8])
        current_time = datetime.now()
        time_scraped.append(current_time)
        time_scraped.append(current_time)
        home_teams.append(home_team)
        home_teams.append(home_team)
        away_teams.append(away_team)
        away_teams.append(away_team)
        match_date_and_time.append(match_datetime)
        match_date_and_time.append(match_datetime)
        market_type.append(market_type_element[0].text + " " + market_line[0].text)
        market_type.append(market_type_element[0].text + " " + market_line[0].text)
        market_odds.append(odds[0].text)
        market_odds.append(odds[1].text)
        market_names.append(market_name[1].text)
        market_names.append(market_name[2].text)
    elif (market_type_element[0].text == "Both Teams to Score"):
        market_name = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-ParticipantBorderless_Name"
        )
        odds = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-ParticipantBorderless_Odds"
        )
        home_teams.append(home_team)
        home_teams.append(home_team)
        away_teams.append(away_team)
        away_teams.append(away_team)
        url = driver.current_url
        url = url.split("/")
        match_ids.append(url[8])
        match_ids.append(url[8])
        current_time = datetime.now()
        time_scraped.append(current_time)
        time_scraped.append(current_time)
        match_date_and_time.append(match_datetime)
        match_date_and_time.append(match_datetime)
        market_type.append(market_type_element[0].text)
        market_type.append(market_type_element[0].text)
        market_odds.append(odds[0].text)
        market_odds.append(odds[1].text)
        market_names.append(market_name[0].text)
        market_names.append(market_name[1].text)
    elif market_type_element[0].text == "Full Time Result":
        market_name = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-Participant_Name"
        )
        odds = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-Participant_Odds"
        )
        home_teams.append(home_team)
        home_teams.append(home_team)
        home_teams.append(home_team)
        away_teams.append(away_team)
        away_teams.append(away_team)
        away_teams.append(away_team)
        url = driver.current_url
        url = url.split("/")
        match_ids.append(url[8])
        match_ids.append(url[8])
        match_ids.append(url[8])
        current_time = datetime.now()
        time_scraped.append(current_time)
        time_scraped.append(current_time)
        time_scraped.append(current_time)
        match_date_and_time.append(match_datetime)
        match_date_and_time.append(match_datetime)
        match_date_and_time.append(match_datetime)
        market_type.append(market_type_element[0].text)
        market_type.append(market_type_element[0].text)
        market_type.append(market_type_element[0].text)
        market_odds.append(odds[0].text)
        market_odds.append(odds[1].text)
        market_odds.append(odds[2].text)
        market_names.append(market_name[0].text)
        market_names.append(market_name[1].text)
        market_names.append(market_name[2].text)

    else:
        print("Issue With Market Name")


# Body
new_driver = driver_code()
open_tab(new_driver, 'https://www.bet365.com/#/AC/B1/C1/D1002/E91422157/G40/H^1/')
accept_cookies(new_driver)
time.sleep(1)
open_tab(new_driver, 'https://www.bet365.com/#/AC/B1/C1/D1002/E91422157/G40/H^1/')
accept_cookies(new_driver)
teams_ = new_driver.find_elements(
    By.CSS_SELECTOR, ".rcl-ParticipantFixtureDetails_LhsContainerInner "
)
market_names = []
market_odds = []
market_type = []
home_teams = []
away_teams = []
match_date_and_time = []
match_ids = []
time_scraped = []
num_matches = len(teams_)
for i in range(num_matches):
    elements_to_click = new_driver.find_elements(
        By.CSS_SELECTOR, ".rcl-ParticipantFixtureDetails_LhsContainerInner "
    )
    elements_to_click[i].click()
    time.sleep(1)
    team_names = new_driver.find_elements(
        By.CSS_SELECTOR, ".sph-FixturePodHeader_TeamName "
    )
    date_and_time = new_driver.find_elements(
        By.CSS_SELECTOR, ".sph-ExtraData_TimeStamp "
    )
    test = new_driver.find_elements(
        By.CSS_SELECTOR, ".gl-MarketGroupPod.gl-MarketGroup"
    )
    home_team = team_names[0].text
    away_team = team_names[1].text
    match_datetime = date_and_time[0].text
    for i in range(len(test)):
        market_type_element = test[i].find_elements(
            By.CSS_SELECTOR, ".gl-MarketGroupButton_Text "
        )
        if (len(market_type_element) > 0):
            get_odds_from_market_name(new_driver, market_type_element, market_names, market_odds, market_type,
                                      home_teams, home_team, away_teams, away_team, match_date_and_time, match_datetime,
                                      match_ids, time_scraped)
    time.sleep(3)
    open_tab(new_driver, 'https://www.bet365.com/#/AC/B1/C1/D1002/E91422157/G40/H^1/')
    main_tab = new_driver.current_window_handle
    # Perform actions that open a new tab (e.g., clicking a link with target="_blank")
    # Get all window handles
    all_tabs = new_driver.window_handles
    # Find the index of the tab you want to close
    tab_to_close_index = 0  # Replace with the index of the tab you want to close
    # Switch to the tab you want to close
    new_driver.switch_to.window(all_tabs[tab_to_close_index])
    # Close the tab
    new_driver.close()
    # Switch back to the main tab
    new_driver.switch_to.window(main_tab)

new_driver.quit()
columns = ['Match ID', 'Home Team', 'Away Team', "Match Time and Date", "Market Type", "Market Name", "Market Odds",
           "Time Scraped"]

# Initialize a new DataFrame with columns
new_dataframe = pd.DataFrame(columns=columns)

# Add arrays to columns
new_dataframe['Match ID'] = match_ids
new_dataframe['Home Team'] = home_teams
new_dataframe['Away Team'] = away_teams
new_dataframe['Match Time and Date'] = match_date_and_time
new_dataframe['Market Type'] = market_type
new_dataframe['Market Name'] = market_names
new_dataframe['Market Odds'] = market_odds
new_dataframe['Time Scraped'] = time_scraped

new_dataframe.to_csv('bet365.csv', index=False)