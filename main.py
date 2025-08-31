from scraper import Scraper
from datetime import datetime
from clean_data import FoodDataCleaner

# Use today's date
today = datetime.today()
today_date = today.strftime('%Y-%m-%d')
is_weekend = today.weekday() >= 5  # Saturday=5, Sunday=6

scraper = Scraper(today_date)

try:
    if is_weekend:
        # On weekends, breakfast and lunch are the same (brunch), so only scrape one
        print("Weekend detected - scraping brunch (breakfast) and dinner only")
        scraper.fetch_breakfast()  # This will contain brunch items
        scraper.fetch_dinner()
    else:
        # On weekdays, scrape all three meals
        print("Weekday detected - scraping breakfast, lunch, and dinner")
        scraper.fetch_breakfast()
        scraper.fetch_lunch()
        scraper.fetch_dinner()
finally:
    scraper.close()

# once the scraping is done, now we need to clean the scraped data.
cleaner = FoodDataCleaner()
cleaner.clean_food_data()

# now tht we have stored the cleaned data to our dir, now we can finally go ahead and upload all the cleaned data to the db.