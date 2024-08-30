# Based on https://github.com/surelle-ha/OfficialGazettePH-HolidayAPI

from seleniumbase import Driver
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time


def parse_date_format(date_str: str, year: int) -> str:
    """
    Returns the date string in YYYY-MM-DD format
    """
    date_str = date_str.split('(')[0].strip()
    return datetime.strptime(f'{date_str} {year}', '%B %d %Y').strftime('%Y-%m-%d')


def parse_holiday_type(holiday_type: str) -> str:
    """
    Returns the holiday type string in an standardized format
    """
    match holiday_type:
        case 'Regular Holidays':
            return 'regular_holiday'
        case 'Special (Non-Working) Holidays':
            return 'special_non_working_holiday'
        case _:
            return ''

def get_holiday_data(year: int = datetime.now().year, get_holiday_name: bool = False, log_time: bool = True) -> list:
    """
    Scrapes holidays from the Official Gazette. If `year` is not provided, the current year is used as a default value. Takes approximately 10-20 seconds per request.
    """
    start_time = time.time()

    url = f'https://www.officialgazette.gov.ph/nationwide-holidays/{year}/'

    try:
        driver = Driver(uc=True) # Use `uc=True` to bypass Cloudflare
        driver.get(url)
        page_source = driver.page_source
        title = driver.get_title().lower()
        driver.quit()

        holidays = []

        # Attempt to check if the page returns a 404 code
        if not "page not found" in title:
            soup = BeautifulSoup(page_source, 'html.parser')

            tables = soup.find_all("table")
            for i, table in enumerate(tables):
                holiday_type = "Regular Holidays" if i == 0 else "Special (Non-Working) Holidays"
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    event = cols[0].get_text(strip=True)
                    date = cols[1].get_text(strip=True)
                    formatted_date = parse_date_format(date, year)
                    formatted_type = parse_holiday_type(holiday_type)
                    if get_holiday_name:
                        holidays.append({'event': event, 'date': formatted_date, 'holiday_type': formatted_type})
                    else:
                        holidays.append({'date': formatted_date, 'holiday_type': formatted_type})

    except Exception as e:
        return f'Error processing HTML content: {e}' 

    response_time = time.time() - start_time

    if log_time:
        print(f"{len(holidays)} holiday(s) found in {year}. Request processed in {round(response_time, 2)} second(s)")

    return holidays


if __name__ == '__main__':
    try:
        input_path = "data.csv"
        output_path = "new_data.csv"
        
        print(f"Reading data from {input_path}")
        data_df = pd.read_csv(input_path)
        data_df['date'] = pd.to_datetime(data_df['date'])

        # Generate the year range in the data to determine which years' holidays should be obtained
        years = data_df['date'].dt.year.unique().tolist()

        # Create a dict for the holiday data that will be retrieved
        holidays = {}

        # Obtain the holiday data for each year and store them in a dict
        for year in years:
            holidays[str(year)] = get_holiday_data(year)

        # Match the holiday data to the list of dicts containing the dates in the input data
        holidays_list = [item for sublist in holidays.values() for item in sublist]
        holidays_df = pd.DataFrame(holidays_list)
        holidays_df['date'] = pd.to_datetime(holidays_df['date'])

        # Add a column indicating if the date is a holiday or not
        holidays_df['is_holiday'] = 'True'

        # Put the holiday_type column at the end
        holidays_df['holiday_type'] = holidays_df.pop('holiday_type')

        # Merge the two dataframes together based on the date column
        merged_df = pd.merge(data_df, holidays_df, on='date', how='left')

        # Save modified data to CSV file
        print(f"Saving modified data to {output_path}")
        merged_df.to_csv(output_path)

    except Exception as e:
        print(e)