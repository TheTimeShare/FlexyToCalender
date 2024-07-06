import time
import pyautogui
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from git import Repo
import os
import shutil
import requests

local_tz = pytz.timezone('Europe/Copenhagen')

def read_credentials(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        
    credentials = []
    current_user = {}
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            if current_user:
                credentials.append(current_user)
                current_user = {}
            current_user['name'] = line[2:]
        elif line.startswith('Mail:'):
            current_user['mail'] = line[6:]
        elif line.startswith('password:') or line.startswith('Password:'):
            current_user['password'] = line.split(':')[1].strip()
    
    if current_user:
        credentials.append(current_user)
    
    return credentials

# Prompt user to enter their name
username = input("Please enter your name (e.g., Emil, Malou): ").strip().lower()

# Initialize Selenium WebDriver after user input
options = Options()
options.headless = True  # Set to False for debugging (so you can see the browser)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Read credentials based on the provided names.txt file
    credentials_list = read_credentials('names.txt')

    # Filter credentials for the specified username
    filtered_credentials = [creds for creds in credentials_list if creds['name'].lower() == username]

    if not filtered_credentials:
        print(f"No credentials found for user '{username}'. Exiting.")
        exit()

    def create_ics_file(login_credentials):
        try:
            login_url = "https://v2.flexybox.com/app/log-ind/app/beskeder"
            data_url = "https://v2.flexybox.com/app/oversigt/vagtliste"

            driver.get(login_url)
            print("Page Title:", driver.title)
            print()

            email_field = driver.find_element(By.CSS_SELECTOR, "input[name='UserName']")
            email_field.send_keys(login_credentials['mail'])

            password_field = driver.find_element(By.CSS_SELECTOR, "input[name='Password']")
            password_field.send_keys(login_credentials['password'])
            password_field.submit()
            pyautogui.press("enter")

            print("Logged in! Navigating to duty list...")
            print()

            time.sleep(1)

            driver.get(data_url)

            print("Scraping data from the page")
            print()
            time.sleep(1)

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))  # Wait for the table to load

            soup = BeautifulSoup(driver.page_source, 'html.parser')

        finally:
            driver.quit()

        data = []
        for row in soup.select('table tr'):
            columns = row.find_all('td')
            if len(columns) > 1:
                datum = {
                    'Afdeling': columns[5].get_text(strip=True),
                    'Dato': columns[0].get_text(strip=True),
                    'Tidspunkt': columns[2].get_text(strip=True),
                    'Kommentar': columns[6].get_text(strip=True) if len(columns) > 3 else ''
                }
                data.append(datum)

        print("Scraped Data:", data)
        print()

        calendar = Calendar()

        def parse_time_range(date_str, time_range, tz):
            start_time_str, end_time_str = time_range.split(' – ')
            start = tz.localize(datetime.strptime(f"{date_str} {start_time_str}", '%d-%m-%Y %H:%M'))
            end = tz.localize(datetime.strptime(f"{date_str} {end_time_str}", '%d-%m-%Y %H:%M'))

            if end <= start:
                end += timedelta(days=1)

            return start, end

        for item in data:
            event = Event()
            event.name = f"Sport hos {item['Afdeling']}"

            start_date_str = item['Dato']

            start, end = parse_time_range(start_date_str, item['Tidspunkt'], local_tz)

            event.begin = start
            event.end = end
            event.description = item['Kommentar'] if item['Kommentar'] else ''

            print(f"Event: {event.name}")
            print(f"Start: {event.begin}")
            print(f"End: {event.end}")
            print(f"Description: {event.description}")
            print()

            calendar.events.add(event)

        file_name = username + '.ics'  # Use username provided at the start
        repo_dir = 'flexykalenderics'  # Name of the directory where the repository will be cloned
        ics_file_path = os.path.join(repo_dir, file_name)
        with open(ics_file_path, 'w') as f:
            f.writelines(calendar)
        
        print(f"iCalendar file '{ics_file_path}' is created!")
        print()

    # GitHub repository configuration
    repo_url = 'https://github.com/TheTimeShare/flexykalenderics'

    try:
        repo_dir = 'flexykalenderics'  # Name of the directory where the repository will be cloned

        # Clone the repository or pull latest changes if exists
        if os.path.exists(repo_dir):
            repo = Repo(repo_dir)
            origin = repo.remote(name='origin')
            origin.pull()

            print(f"Repository '{repo_dir}' exists. Pulling latest changes...")
        else:
            Repo.clone_from(repo_url, repo_dir)
            print(f"Cloned repository '{repo_url}' into '{repo_dir}'")

        for credentials in filtered_credentials:  # Loop through filtered credentials
            create_ics_file(credentials)

        # Stage all changes and commit
        repo.git.add('.')
        repo.index.commit('Updated .ics files')

        # Push changes to the remote repository
        origin.push()

        print("Updated .ics files pushed to GitHub repository!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

finally:
    driver.quit()
