import pandas as pd
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz

local_tz = pytz.timezone('Europe/Copenhagen')

df = pd.read_excel('input.xlsx')

print("Kolonne navne i excel dokumentet:", df.columns)

df.columns = df.columns.str.strip()

print("Kolonne navne efter stripping:", df.columns)

print(df.head())

calendar = Calendar()

def parse_time_range(date_str, time_range, tz):
    start_time_str, end_time_str = time_range.split(' – ')
    start = tz.localize(datetime.strptime(f"{date_str} {start_time_str}", '%Y-%m-%d %H:%M'))
    end = tz.localize(datetime.strptime(f"{date_str} {end_time_str}", '%Y-%m-%d %H:%M'))
    
    if end <= start:
        end += timedelta(days=1)
    
    return start, end

for index, row in df.iterrows():
    event = Event()
    event.name = f"Sport hos {row['Afdeling']}"
    
    start_date_str = row['Dato'].strftime('%Y-%m-%d')
    
    start, end = parse_time_range(start_date_str, row['Tidspunkt'], local_tz)
    
    event.begin = start
    event.end = end
    event.description = row['Kommentar'] if pd.notna(row['Kommentar']) else ''
    
    print(f"Event: {event.name}")
    print(f"Start: {event.begin}")
    print(f"End: {event.end}")
    print(f"Description: {event.description}")
    
    calendar.events.add(event)

with open('events.ics', 'w') as f:
    f.writelines(calendar)

print("iCalendar fil 'events.ics' oprettet!.")
