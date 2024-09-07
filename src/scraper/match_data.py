import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pandas as pd
import concurrent.futures


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


def std_single_match(driver, url):
    print(f'Scraping URL: {url}')
    try:
        driver.get(url + ':tab=stats')
        wait = WebDriverWait(driver, 5)
        try:
            consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'fc-cta-consent')]")))
            consent_button.click()
        except Exception:
            pass
        # # Check for extra time or penalties
        # try:
        #     ET_pens_xpath = '/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[2]/span'
        #     ET_pens = wait.until(EC.visibility_of_element_located((By.XPATH, ET_pens_xpath))).text
        #     if 'extra' in ET_pens.lower() or 'pen' in ET_pens.lower():
        #         print(f"Extra time match: {url}, skipping.")
        #         return None  # Indicate to skip this URL
        # except Exception:
        #     pass

        try:
            team1_xpath = "/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[1]/a/div/span/span[2]"
            team2_xpath = "/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[3]/a/div/span/span[2]"
            team1_name = wait.until(EC.visibility_of_element_located((By.XPATH, team1_xpath))).text
            team2_name = wait.until(EC.visibility_of_element_located((By.XPATH, team2_xpath))).text
        except TimeoutException:
            print(f"Team names not found for URL: {url}")
            return pd.DataFrame()

        # team1_ranking, team2_ranking = None, None
        # try:
        #     team1_ranking_xpath = "//*[@id='__next']/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[1]/a/div/span/span[3]"
        #     team2_ranking_xpath = "//*[@id='__next']/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[3]/a/div/span/span[3]"
        #     team1_ranking = wait.until(EC.visibility_of_element_located((By.XPATH, team1_ranking_xpath))).text.split('#')[-1].strip()
        #     team2_ranking = wait.until(EC.visibility_of_element_located((By.XPATH, team2_ranking_xpath))).text.split('#')[-1].strip()
        # except TimeoutException:
        #     print(f"FIFA rankings not found for URL: {url}")

        try:
            score_xpath = '/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[2]/span[1]'
            score_text = wait.until(EC.visibility_of_element_located((By.XPATH, score_xpath))).text
            try:
                home_goals, away_goals = map(int, score_text.split(' - '))
            except ValueError:
                score_xpath2 = '/html/body/div[1]/main/main/div[2]/div/div[1]/div[1]/div/section/div/section/header/div[2]/div/span'
                score_text2 = wait.until(EC.visibility_of_element_located((By.XPATH, score_xpath2))).text
                home_goals, away_goals = map(int, score_text2.split(' - '))
        except TimeoutException:
            print(f"Score not found for URL: {url}")
            return pd.DataFrame()

        match_datetime = None
        venue = None
        venue_href = None
        competition = None
        possession_t1 = None
        possession_t2 = None

        try:
            datetime_xpath = "//*[@id='__next']/main/main/div[2]/div/div[1]/div[1]/div/section/div/div[2]/section/ul/li[1]/div/time"
            match_datetime = wait.until(EC.visibility_of_element_located((By.XPATH, datetime_xpath))).get_attribute('datetime')
        except TimeoutException:
            print(f"Datetime not found for URL: {url}")

        try:
            competition_xpath = "//*[@id='__next']/main/main/div[2]/div/div[1]/div[1]/div/section/div/div[1]/div/div[2]/a/span"
            competition = wait.until(EC.visibility_of_element_located((By.XPATH, competition_xpath))).text
        except TimeoutException:
            print(f"Competition not found for URL: {url}")

        # Extract attendance
        attendance = extract_attribute_data(driver, "Attendance")

        # Extract referee
        referee = extract_attribute_data(driver, "Reveree")
        if not referee:
            referee = extract_attribute_data(driver, "Referee")

        # Extract venue
        venue_data = extract_attribute_data(driver, "Venue")
        if venue_data:
            venue, venue_href = venue_data

        possession_xpaths_t1 = [
            '//*[@id="__next"]/main/main/div[2]/div/div[1]/div[2]/section/section/div[1]/ul/div/div[1]/span',
            '/html/body/div[1]/main/main/div[2]/div/div[1]/div[2]/section/section/div[1]/ul/div/div[1]/span',
            '/html/body/div[1]/main/main/div[2]/div/div[1]/div[2]/section/section/div[2]/ul/div/div[1]/span',
            '/html/body/div[1]/main/main/div[2]/div/div[1]/div[3]/section/section/div[2]/ul/div/div[1]/span',
        ]
        possession_xpaths_t2 = [
            '//*[@id="__next"]/main/main/div[2]/div/div[1]/div[2]/section/section/div[1]/ul/div/div[2]/span',
            '/html/body/div[1]/main/main/div[2]/div/div[1]/div[2]/section/section/div[1]/ul/div/div[2]/span',
            '/html/body/div[1]/main/main/div[2]/div/div[1]/div[2]/section/section/div[2]/ul/div/div[2]/span',
            '/html/body/div[1]/main/main/div[2]/div/div[1]/div[3]/section/section/div[2]/ul/div/div[2]/span',
        ]

        for xpath in possession_xpaths_t1:
            try:
                possession_t1 = wait.until(EC.visibility_of_element_located((By.XPATH, xpath))).text
                break
            except TimeoutException:
                continue

        for xpath in possession_xpaths_t2:
            try:
                possession_t2 = wait.until(EC.visibility_of_element_located((By.XPATH, xpath))).text
                break
            except TimeoutException:
                continue

        try:
            stats_containers = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//ul[contains(@class, 'StatGroupContainer')]")))
        except TimeoutException:
            print(f"Stats containers not found for URL: {url}")
            return pd.DataFrame()

        team1_data = { # 'team_ranking': team1_ranking, 'opp_ranking': team2_ranking,
            'url': url, 'team': team1_name,  'opp': team2_name, 'team_goals': home_goals, 'opp_goals': away_goals,
            'datetime': match_datetime, 'stadium': venue, 'referee': referee, 'attendance': attendance,
            'competition': competition, 'possession': possession_t1, 'opp_possession': possession_t2,
            'venue_href': venue_href
        }
        team2_data = { # 'opp_ranking': team1_ranking, 'ranking': team2_ranking
            'url': url, 'team': team2_name, 'opp': team1_name, 'team_goals': away_goals, 'opp_goals': home_goals,
            'datetime': match_datetime, 'stadium': venue, 'referee': referee, 'attendance': attendance,
            'competition': competition, 'possession': possession_t2, 'opp_possession': possession_t1,
            'venue_href': venue_href
        }

        team1_stats = {}
        team2_stats = {}

        for container in stats_containers:
            soup = BeautifulSoup(container.get_attribute('outerHTML'), 'html.parser')
            for li in soup.find_all("li", class_=re.compile(".*Stat.*")):
                title_element = li.find("span", class_=re.compile(".*StatTitle.*"))
                if title_element:
                    stat_name = title_element.text.strip()
                    values = [span.text.strip() for span in li.find_all("span", class_=re.compile(".*StatValue.*"))]
                    if len(values) == 2:
                        team1_stats[stat_name], team1_stats[stat_name + '_pc'] = values[0].split(' (') if '(' in values[
                            0] else (values[0], '')
                        team2_stats[stat_name], team2_stats[stat_name + '_pc'] = values[1].split(' (') if '(' in values[
                            1] else (values[1], '')

        df_team1 = pd.DataFrame([team1_stats])
        df_team2 = pd.DataFrame([team2_stats])

        df_team2_conceded = df_team2.rename(columns=lambda x: f'conc_{x}')
        df_team1_combined = pd.concat([df_team1, df_team2_conceded], axis=1)

        df_team1_conceded = df_team1.rename(columns=lambda x: f'conc_{x}')
        df_team2_combined = pd.concat([df_team2, df_team1_conceded], axis=1)

        df_team1_combined = pd.concat([pd.DataFrame([team1_data]), df_team1_combined], axis=1)
        df_team2_combined = pd.concat([pd.DataFrame([team2_data]), df_team2_combined], axis=1)
        df = pd.concat([df_team1_combined, df_team2_combined]).reset_index(drop=True)

        df = df.replace({'\(': '', '\)': ''}, regex=True)
        df = df.replace({'%': ''}, regex=True)
        df = df.replace({'#': ''}, regex=True)
        df = df.replace('', pd.NA)

        cols_to_drop = [col for col in df.columns if '_pc' in col and df[col].isna().all()]
        df = df.drop(columns=cols_to_drop)

        df.columns = df.columns.str.lower().str.replace(' ', '_')
        return df
    except Exception as e:
        print(f"Error while scraping URL: {url} - {e}")
        return pd.DataFrame()


def scrape_urls(urls):
    options = webdriver.ChromeOptions()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    results = []
    for url in urls:
        df = std_single_match(driver, url)
        if df is None:
            continue
        if not df.empty:
            results.append(df)

    driver.quit()
    return results


def parallel_scrape(all_urls, max_workers=4):
    chunks = [all_urls[i::max_workers] for i in range(max_workers)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scrape_urls, chunk) for chunk in chunks]
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
    return results
