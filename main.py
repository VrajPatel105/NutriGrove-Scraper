from scraper import Scraper
from datetime import datetime
from clean_data import FoodDataCleaner
import json
# Use today's date
today_date = datetime.today().strftime('%Y-%m-%d')
scraper = Scraper(today_date)

try:
    scraper.fetch_breakfast()
    # scraper.fetch_lunch()
    # scraper.fetch_dinner()
finally:
    scraper.close()

# once the scraping is done, now we need to clean the scraped data.
cleaner = FoodDataCleaner()
cleaner.clean_food_data()

# now tht we have stored the cleaned data to our dir, now we can finally go ahead and upload all the cleaned data to the db.