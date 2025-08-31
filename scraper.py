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
        chrome_options.add_argument("--headless")
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
        os.makedirs('data/scraped_data', exist_ok=True)

    def save_to_file(self, food_data_list, meal_type):
        """Save scraped food data to local JSON file"""
        try:
            file_path = f'data/scraped_data/food_items_{meal_type}.json'
            
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
            time.sleep(15)  # Wait longer for JS to load
            
            print(f"Page loaded: {self.driver.title}")
            
            # Find all tables with menu data
            tables = self.driver.find_elements(By.CSS_SELECTOR, 'table')
            print(f"Found {len(tables)} tables with menu data")
            
            all_food_items = []
            total_items = 0
            
            # Process each table (each table represents a menu section/station)
            for table_index, table in enumerate(tables, 1):
                try:
                    # Try to find station name near the table
                    station_name = f"Station {table_index}"
                    
                    # Look for station name in various locations around the table
                    parent = table
                    for _ in range(3):  # Go up 3 levels to find station name
                        parent = parent.find_element(By.XPATH, "..")
                        try:
                            # Look for headings near this table
                            headings = parent.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, .station-name, [class*='station'], [class*='title']")
                            for heading in headings:
                                text = heading.text.strip()
                                if text and len(text) > 2:  # Valid station name
                                    station_name = text
                                    break
                            if station_name != f"Station {table_index}":
                                break
                        except:
                            continue
                    
                    print(f"Found station: {station_name}")
                    
                    # Get all rows from this table
                    rows = table.find_elements(By.CSS_SELECTOR, 'tr')
                    
                    for row in rows:
                        try:
                            # Get all cells in this row
                            cells = row.find_elements(By.CSS_SELECTOR, 'td')
                            if len(cells) < 1:
                                continue
                            
                            # First cell should contain food name
                            first_cell = cells[0]
                            food_name = first_cell.text.strip()
                            
                            # Skip header rows or empty cells
                            if not food_name or food_name.lower() in ['portion', 'calories', '']:
                                continue
                            
                            print(f" -> Processing: {food_name}")
                            
                            # Try to click for nutrition info
                            nutrition_info = "Nutrition info not available"
                            
                            try:
                                # Look for clickable element in first cell
                                clickable_elements = first_cell.find_elements(By.CSS_SELECTOR, "button, [role='button'], span[class*='click'], div[class*='click']")
                                
                                if clickable_elements:
                                    clickable = clickable_elements[0]
                                    
                                    # Scroll into view and click
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable)
                                    time.sleep(1)
                                    
                                    try:
                                        clickable.click()
                                    except:
                                        self.driver.execute_script("arguments[0].click();", clickable)
                                    
                                    time.sleep(3)
                                    
                                    # Look for popup/modal with nutrition info
                                    modal_selectors = [
                                        "[role='dialog']", ".modal", ".popup", 
                                        "div[class*='modal']", "div[class*='popup']",
                                        "div[class*='nutrition']", "div[class*='detail']"
                                    ]
                                    
                                    for modal_sel in modal_selectors:
                                        try:
                                            wait = WebDriverWait(self.driver, 5)
                                            modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, modal_sel)))
                                            nutrition_info = modal.text
                                            break
                                        except:
                                            continue
                                    
                                    # Close modal
                                    close_selectors = [
                                        "button[aria-label*='close']", ".close", ".close-button",
                                        "button[class*='close']", "[data-dismiss]", "button:last-child"
                                    ]
                                    
                                    for close_sel in close_selectors:
                                        try:
                                            close_btn = self.driver.find_element(By.CSS_SELECTOR, close_sel)
                                            close_btn.click()
                                            break
                                        except:
                                            continue
                                    
                                    time.sleep(1)
                                    
                            except Exception as click_error:
                                print(f"Could not get detailed nutrition for {food_name}: {click_error}")
                            
                            # Create food data object
                            food_data = {
                                'station_name': station_name,
                                'food_name': food_name,
                                'nutritional_info': nutrition_info,
                            }
                            
                            all_food_items.append(food_data)
                            total_items += 1
                            
                        except Exception as e:
                            print(f"Error processing table row: {e}")
                            continue
                
                except Exception as e:
                    print(f"Error processing table {table_index}: {e}")
                    continue
            
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