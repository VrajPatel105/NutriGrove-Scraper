from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import datetime

class Scraper:
    def __init__(self, date):
        # Configure Chrome options for headless operation
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Added for GitHub Actions
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize Chrome driver with options
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.date = date
        
        # Creating the directory for scraped data
        os.makedirs('backend/app/data/scraped_data', exist_ok=True)

    def save_to_file(self, food_data_list, meal_type):
        """Save scraped food data to local JSON file"""
        try:
            file_path = f'backend/app/data/scraped_data/food_items_{meal_type}.json'
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(food_data_list, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(food_data_list)} {meal_type} items to {file_path}")
            return True
            
        except Exception as e:
            print(f"error saving {meal_type} data: {e}")
            return False

    def scrape_meal(self, meal_type):
        """Generic method to scrape any meal type"""
        print(f"\n🔍 Scraping {meal_type} data for {self.date}...")
        url = f"https://new.dineoncampus.com/umassd/whats-on-the-menu/the-grove/{self.date}/{meal_type}"
        
        try:
            self.driver.get(url)
            time.sleep(10)  # Wait for page to load
            
            all_food_items = []
            total_items = 0
            counter = 1
            
            while True:
                try:
                    # Find table
                    table = self.driver.find_element(By.XPATH, f"/html/body/div[1]/div/div/main/div[1]/div[4]/div/div[2]/div[{counter}]/div[2]/div[2]/table")
                    
                    # Get station name
                    try:
                        station_name_element = self.driver.find_element(By.XPATH, f"/html/body/div/div/div/main/div[1]/div[3]/div/div[2]/div[{counter}]/div[1]/div[2]/div")
                        station_name = station_name_element.text.strip()
                        print(f"Found station: {station_name}")
                    except Exception:
                        station_name = f"Station {counter}"
                    
                    # Get table rows
                    rows = table.find_elements(By.CSS_SELECTOR, 'tr')
                    if not rows:
                        break
                    
                    for i, row in enumerate(rows, 1): 
                        try:
                            button_click = row.find_element(By.CSS_SELECTOR, 'td:first-child div span')
                            food_name = button_click.text.strip()
                            
                            if not food_name:  # Skip empty rows
                                continue
                            
                            print(f" -> Processing: {food_name}")
                            
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
                            
                            # Close popup
                            close_button = self.driver.find_element(By.XPATH, "/html/body/div/div/div/main/div[2]/div/button[1]")
                            close_button.click()
                            time.sleep(2)
                            
                        except Exception as e:
                            print(f"Error processing item {i}: {e}")
                            continue
                    
                    counter += 1
                    
                except Exception as e:
                    print(f" Finished processing stations for {meal_type}")
                    break
            
            # Save all items to file
            if all_food_items:
                success = self.save_to_file(all_food_items, meal_type)
                print(f"📊 Total {meal_type} items scraped: {total_items}")
                return success
            else:
                print(f"No {meal_type} items found")
                return False
                
        except Exception as e:
            print(f"Error scraping {meal_type}: {e}")
            return False

    def fetch_breakfast(self):
        """Scrape breakfast data"""
        return self.scrape_meal('breakfast')

    def fetch_lunch(self):
        """Scrape lunch data"""
        return self.scrape_meal('lunch')

    def fetch_dinner(self):
        """Scrape dinner data"""
        return self.scrape_meal('dinner')

    def close(self):
        """Close the browser"""
        self.driver.quit()