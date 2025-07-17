from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client
from dotenv import load_dotenv
import time
import json
import os
import datetime
import time
# from dotenv import load_dotenv
# from supabase import create_client, Client

class Scraper:
    def __init__(self, date):
        # Initialize Chrome driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.date = date
        
        # creating the directory for scraped data
        os.makedirs('backend/app/data/scraped_data', exist_ok=True)
        
        """I dont need this db connection either.. 
        Story: I initially thought that i will push the individual scraped files to db because i will need to deploy it someday.
        But then i came to know about github Actions. I came to know that it creates the directory and will get the file locally (form the running server).. 
        So, when running the code, it will make the directory and store the file locally. 
        So, instead of pushing everything on db, i thought to keep it on local machine (github actions's machine) and it will create it during the workflow.
        Good thing is that it will delete all of this temp created directories, once the code is executed.
        """
        # Initialize Supabase connection (just keeping it still in the code)
        # load_dotenv()
        # url = os.getenv("SUPABASE_URL")
        # key = os.getenv("SUPABASE_ANON_KEY")
        
        # if not url or not key:
        #     raise ValueError("Missing Supabase credentials in .env file")
        
        # self.supabase = create_client(url, key)
        # print("Connected to Supabase!")

    def save_to_file(self, food_data_list, meal_type):
        """Save scraped food data to local JSON file"""
        try:
            file_path = f'backend/app/data/scraped_data/food_items_{meal_type}.json'
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(food_data_list, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            return False

    # def save_to_database(self, food_data, meal_type):
    #     """Save scraped food data directly to database"""
    #     try:
    #         # Add meal type and scrape date to the data
    #         db_record = {
    #             'meal_type': meal_type,
    #             'station_name': food_data['station_name'],
    #             'food_name': food_data['food_name'],
    #             'nutritional_info': food_data['nutritional_info'],
    #             'scrape_date': self.date
    #         }
    #         
    #         result = self.supabase.table('scraped_food_data').insert(db_record).execute()
    #         print(f"Saved to DB: {food_data['food_name']} (ID: {result.data[0]['id']})")
    #         return True
    #         
    #     except Exception as e:
    #         print(f"Error saving to DB: {food_data['food_name']} - {e}")
    #         return False

    def scrape_meal(self, meal_type):
        """Generic method to scrape any meal type"""
        url = f"https://new.dineoncampus.com/umassd/whats-on-the-menu/the-grove/{self.date}/{meal_type}"
        self.driver.get(url)
        time.sleep(10)
        
        all_food_items = []  # Store all items for this meal
        total_items = 0
        counter = 1
        
        while True:
            try:
                # Find table
                table = self.driver.find_element(By.XPATH, f"/html/body/div/div/div/main/div[1]/div[3]/div/div[2]/div[{counter}]/div[2]/div[2]/table/tbody")
                
                # Get station name
                try:
                    station_name_element = self.driver.find_element(By.XPATH, f"/html/body/div/div/div/main/div[1]/div[3]/div/div[2]/div[{counter}]/div[1]/div[2]/div")
                    station_name = station_name_element.text.strip()
                    print(f"\nStation: {station_name}")
                except Exception as e:
                    station_name = f"Station {counter}"
                
                # Get table rows
                rows = table.find_elements(By.CSS_SELECTOR, 'tr')
                if not rows:
                    break
                
                # Process each food item
                for row in enumerate(rows, 1):
                    try:
                        button_click = row.find_element(By.CSS_SELECTOR, 'td:first-child div span')
                        food_name = button_click.text.strip()
                        
                        # Click to open nutrition popup
                        button_click.click()
                        time.sleep(3)
                        
                        # Wait for popup and get nutrition info
                        wait = WebDriverWait(self.driver, 10)
                        popup = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/main/div[2]/div")))
                        popup_text = popup.text
                        
                        # Create food data object
                        food_data = {
                            'station_name': station_name,
                            'food_name': food_name,
                            'nutritional_info': popup_text,
                        }
                        
                        # Add to list for file saving
                        all_food_items.append(food_data)
                        total_items += 1
                        
                        # # Save directly to database
                        # if self.save_to_database(food_data, meal_type):
                        #     successful_saves += 1
                        
                        # Close popup
                        close_button = self.driver.find_element(By.XPATH, "/html/body/div/div/div/main/div[2]/div/button[1]")
                        close_button.click()
                        time.sleep(2)
                        
                    except Exception as e:
                        continue
                counter += 1
                
            except Exception as e:
                break
        
        # Save all items to file
        if all_food_items:
            self.save_to_file(all_food_items, meal_type)
        return total_items > 0

    def fetch_breakfast(self):
        """Scrape breakfast data"""
        return self.scrape_meal('breakfast')

    def fetch_lunch(self):
        """Scrape lunch data"""
        return self.scrape_meal('lunch')

    def fetch_dinner(self):
        """Scrape dinner data"""
        return self.scrape_meal('dinner')

    # def fetch_brunch(self):
    #     """Scrape brunch data"""
    #     return self.scrape_meal('brunch')

 # i dont neeed to fetch all meals. because when i will pull all the data from db, i will pull all available at once.. so i dont need all meals func.. still keeping it.. (commenting it out)
    # def fetch_all_meals(self):
    #     """Scrape all available meals for the date"""
    #     meals = ['breakfast', 'lunch', 'dinner']
    #     results = {}
        
    #     for meal in meals:
    #         try:
    #             results[meal] = self.scrape_meal(meal)
    #         except Exception as e:
    #             results[meal] = False
        
    #     return results

    # def clear_todays_data(self):
    #     """Clear existing data for today's date (useful for re-scraping)"""
    #     try:
    #         result = self.supabase.table('scraped_food_data').delete().eq('scrape_date', self.date).execute()
    #         print(f"Cleared {len(result.data)} existing records for {self.date}")
    #     except Exception as e:
    #         print(f"Error clearing data: {e}")

    def close(self):
        """Close the browser"""
        self.driver.quit()
        print("Browser closed")

def main():
    today_date = datetime.datetime.today().strftime('%Y-%m-%d')
    scraper = Scraper(today_date)
    scraper.fetch_breakfast()


if __name__ == "__main__":
    main()
