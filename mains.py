import time
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
import pyautogui

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

def run_script(username):
    try:
        options = Options()
        options.headless = True  # Set to True for headless mode
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        credentials_list = read_credentials('names.txt')

        filtered_credentials = [creds for creds in credentials_list if creds['name'].lower() == username]

        if not filtered_credentials:
            print(f"Ingen credentials fundet for bruger '{username}'. Afslutter.")
            return

        def create_ics_file(login_credentials):
            try:
                login_url = "https://v2.flexybox.com/app/log-ind/app/beskeder"
                data_url = "https://v2.flexybox.com/app/oversigt/vagtliste"

                driver.get(login_url)
                print("Navigating to login page. Page title:", driver.title)

                email_field = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='UserName']"))
                )
                email_field.send_keys(login_credentials['mail'])

                password_field = driver.find_element(By.CSS_SELECTOR, "input[name='Password']")
                password_field.send_keys(login_credentials['password'])
                password_field.submit()
                pyautogui.press("enter")

                print("Logged in! Navigating to vagtliste...")
                time.sleep(2)  # Give some time for the login to process

                driver.get(data_url)
                print("Navigated to vagtliste. Page title:", driver.title)

                # Ensure the table is present before proceeding
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
                )
                time.sleep(1)  # Additional wait to ensure the table is fully loaded

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

            print("Extracted data:", data)

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

                calendar.events.add(event)

            file_name = username + '.ics'
            repo_dir = 'flexykalenderics'
            ics_file_path = os.path.join(repo_dir, file_name)
            with open(ics_file_path, 'w') as f:
                f.writelines(calendar)
            
            print(f"iCalendar file '{ics_file_path}' created successfully!")

        repo_url = 'https://github.com/TheTimeShare/flexykalenderics'

        try:
            repo_dir = 'flexykalenderics'

            if os.path.exists(repo_dir):
                repo = Repo(repo_dir)
                origin = repo.remote(name='origin')
                origin.pull()

                print(f"Repository '{repo_dir}' exists. Pulling latest changes...")
            else:
                Repo.clone_from(repo_url, repo_dir)
                print(f"Cloned repository '{repo_url}' to '{repo_dir}'")

            for credentials in filtered_credentials:
                create_ics_file(credentials)

            repo.git.add('.')
            repo.index.commit('Updated .ics files')

            origin.push()

            print("Updated .ics files pushed to GitHub repository!")

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    finally:
        driver.quit()