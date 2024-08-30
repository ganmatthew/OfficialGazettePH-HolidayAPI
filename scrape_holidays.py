# Based on https://github.com/surelle-ha/OfficialGazettePH-HolidayAPI

from seleniumbase import Driver
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

# Returns the date string in YYYY-MM-DD format
def parse_date_format(date_str: str, year: int) -> str:
    date_str = date_str.split('(')[0].strip()
    return datetime.strptime(f'{date_str} {year}', '%B %d %Y').strftime('%Y-%m-%d')

def get_holidays(year: int = datetime.now().year) -> list:
    start_time = time.time()

    url = f'https://www.officialgazette.gov.ph/nationwide-holidays/{year}/'

    try:
        driver = Driver(uc=True) # Use `uc=True` to bypass Cloudflare
        driver.get(url)
        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')
        holidays = []

        tables = soup.find_all("table")
        for i, table in enumerate(tables):
            holiday_type = "Regular Holidays" if i == 0 else "Special (Non-Working) Holidays"
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                event = cols[0].get_text(strip=True)
                date = cols[1].get_text(strip=True)
                formatted_date = parse_date_format(date, year)
                holidays.append({'event': event, 'date': formatted_date, 'type': holiday_type})

    except Exception as e:
        return f'Error processing HTML content: {e}' 

    response_time = time.time() - start_time
    print(f"{len(holidays)} holiday(s) found in {year}. Request processed in {round(response_time, 2)} second(s)")
    
    return holidays

if __name__ == '__main__':
    print(get_holidays(2024))