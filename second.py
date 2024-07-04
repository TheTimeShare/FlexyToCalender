import pandas as pd
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
from ftplib import FTP

local_tz = pytz.timezone('Europe/Copenhagen')

options = Options()
options.headless = True  # Set to False for debugging (so you can see the browser)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    login_url = "https://v2.flexybox.com/app/log-ind/app/beskeder"
    data_url = "https://v2.flexybox.com/app/oversigt/vagtliste"

    driver.get(login_url)
    print("Page Title:", driver.title)
    print()
    
    login_credentials = {
        "mail": "emiljohansen27@gmail.com",
        "password": "4012"
    }
    
    email_field = driver.find_element(By.CSS_SELECTOR, "input[name='UserName']")
    email_field.send_keys(login_credentials['mail'])

    password_field = driver.find_element(By.CSS_SELECTOR, "input[name='Password']")
    password_field.send_keys(login_credentials['password'])
    password_field.submit()
    pyautogui.press("enter")

    print("Logget ind! Navigere til vagtlise...")
    print()
    
    time.sleep(1)
    
    driver.get(data_url)
    
    print("Scarper data fra side")
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

ics_file_path = 'flexyvagter.ics'
with open(ics_file_path, 'w') as f:
    f.writelines(calendar)

print("iCalendar fil 'flexyvagter.ics' er oprettet!")
print()