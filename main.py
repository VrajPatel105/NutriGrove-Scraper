from scraper import Scraper
from datetime import datetime
from data.clean_data import FoodDataCleaner
from ai_food_recommendation import FoodRecommender
import json
# Use today's date
today_date = datetime.today().strftime('%Y-%m-%d')
scraper = Scraper(today_date)

try:
    # # Scrape data directly to database
    scraper.fetch_breakfast()
    scraper.fetch_lunch()
    scraper.fetch_dinner()
    print("All data scraped and saved to database!")
finally:
    scraper.close()
