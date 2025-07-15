from scraper import Scraper
from datetime import datetime
from data.clean_data import FoodDataCleaner
from ai_food_recommendation import FoodRecommender
import json
# Use today's date
today_date = datetime.today().strftime('%Y-%m-%d')
today_date = "2025-07-16" # since today's sunday, i just manually changed this (temp)
scraper = Scraper(today_date)

try:
    # # Scrape data directly to database
    scraper.fetch_breakfast()
    scraper.fetch_lunch()
    scraper.fetch_dinner()
    print("All data scraped and saved to database!")
finally:
    scraper.close()    

# Clean the scraped data from database
cleaner = FoodDataCleaner()
cleaned_data = cleaner.clean_food_data()

if cleaned_data:
    print(f"Data cleaned and uploaded! Total items: {len(cleaned_data)}")
else:
    print("Data cleaning failed!")

recommender = FoodRecommender()
    
# testing this with user preferences manually
user_preferences = {
    "dietary_restrictions": ["vegetarian"],
    "allergies": ["nuts"],
    "calorie_target": 2500,
    "protein_target": 120,
    "weight_kg": 64 ,
    "height_cm": 177,
    "age": 20,
    "comments":"I dont want fried food today. ALso today i am really craving for some good salad :) . also, i am indian vegeterian meaning that i dont eat eggs too. so no eggs please"
}
schedule = recommender.get_daily_meal_schedule(user_preferences)

if "error" in schedule:
    print(f"Error: {schedule['error']}")
else:
    print("Stored daily meal schedule succesfully!!")