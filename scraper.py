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
import random
import requests

class Scraper:
    def __init__(self, date, university_key='umassd'):
        from university_config import UniversityConfig

        self.university_key = university_key
        self.university_config = UniversityConfig.get_university_config(university_key)

        if not self.university_config:
            raise ValueError(f"Unknown university: {university_key}")

        print(f"Initializing scraper for {self.university_config['name']} ({university_key})")

        # Get a realistic user agent
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

        # Configure Chrome options for stealth operation
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-default-apps")
        options.add_argument("--silent")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Set a random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"--user-agent={user_agent}")

        # Initialize Chrome driver with stealth options
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        # Execute stealth scripts after driver initialization
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "acceptLanguage": "en-US,en;q=0.9",
            "platform": "Win32"
        })

        self.date = date

        # Creating the directory for scraped data
        os.makedirs(f'data/scraped_data/{self.university_key}', exist_ok=True)

    def human_delay(self, min_delay=1, max_delay=3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def check_cloudflare_protection(self):
        """Check if page is showing Cloudflare protection"""
        title = self.driver.title.lower()
        page_source = self.driver.page_source.lower()

        cloudflare_indicators = [
            "attention required",
            "cloudflare",
            "checking your browser",
            "security check",
            "ddos protection",
            "ray id"
        ]

        for indicator in cloudflare_indicators:
            if indicator in title or indicator in page_source:
                return True
        return False

    def wait_for_cloudflare(self, max_wait=60):
        """Wait for Cloudflare protection to complete"""
        print("Detected Cloudflare protection, waiting for bypass...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if not self.check_cloudflare_protection():
                print("Cloudflare protection bypassed successfully!")
                return True
            self.human_delay(2, 5)

        print("Failed to bypass Cloudflare protection within timeout")
        return False

    def save_to_file(self, food_data_list, meal_type):
        """Save scraped food data to local JSON file"""
        try:
            file_path = f'data/scraped_data/{self.university_key}/food_items_{meal_type}.json'

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(food_data_list, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(food_data_list)} {meal_type} items to {file_path}")
            return True

        except Exception as e:
            print(f"error saving {meal_type} data: {e}")
            return False

    def scrape_meal(self, meal_type):
        """Generic method to scrape any meal type"""
        from university_config import UniversityConfig

        print(f"\nScraping {meal_type} data for {self.university_config['name']} on {self.date}...")
        url = UniversityConfig.build_url(self.university_key, self.date, meal_type)
        
        try:
            self.driver.get(url)

            # Random delay to appear more human-like
            self.human_delay(8, 18)

            # Check if Cloudflare protection is active
            if self.check_cloudflare_protection():
                if not self.wait_for_cloudflare():
                    print("Failed to bypass Cloudflare protection, aborting scrape")
                    return False

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
                                    self.human_delay(0.5, 1.5)

                                    try:
                                        clickable.click()
                                    except:
                                        self.driver.execute_script("arguments[0].click();", clickable)

                                    self.human_delay(2, 4)
                                    
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

                                    self.human_delay(0.5, 1.5)
                                    
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
                print(f"Total {meal_type} items scraped: {total_items}")
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