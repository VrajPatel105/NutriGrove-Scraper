import requests
import json
import os
from datetime import datetime
from database import SupabaseUploader

class HarvardAPIScraper:
    def __init__(self, date=None):
        self.base_url = "https://api.cs50.io/dining"
        self.annenberg_id = 30  # Main undergraduate dining hall
        self.date = date or datetime.today().strftime('%Y-%m-%d')
        self.meal_types = {
            0: 'breakfast',
            1: 'lunch',
            2: 'dinner'
        }

        # Create directories
        os.makedirs('data/scraped_data/harvard', exist_ok=True)
        os.makedirs('data/cleaned_data/harvard', exist_ok=True)

    def get_menu_for_meal(self, meal_id):
        """Get menu data for specific meal at Annenberg Hall"""
        try:
            # Get menu items for this meal and location
            menu_url = f"{self.base_url}/menus?location={self.annenberg_id}&meal={meal_id}&date={self.date}"
            response = requests.get(menu_url, timeout=30)
            response.raise_for_status()

            menu_items = response.json()
            meal_name = self.meal_types[meal_id]

            print(f"Found {len(menu_items)} menu items for {meal_name}")

            if not menu_items:
                print(f"No menu items found for {meal_name}")
                return []

            # Get detailed recipe information for each menu item
            detailed_items = []
            recipe_ids = list(set(item.get('recipe') for item in menu_items if item.get('recipe')))

            print(f"Fetching detailed nutrition data for {len(recipe_ids)} unique recipes...")

            for recipe_id in recipe_ids:
                try:
                    recipe_url = f"{self.base_url}/recipes/{recipe_id}"
                    recipe_response = requests.get(recipe_url, timeout=30)
                    recipe_response.raise_for_status()

                    recipe_data = recipe_response.json()

                    # Convert Harvard API format to our standard format
                    formatted_item = {
                        'station_name': 'Annenberg Hall',
                        'food_name': recipe_data.get('name', 'Unknown Item'),
                        'nutritional_info': self.format_nutrition_info(recipe_data),
                        'ingredients': recipe_data.get('ingredients', ''),
                        'allergens': recipe_data.get('allergens', []),
                        'vegan': recipe_data.get('vegan', False),
                        'vegetarian': recipe_data.get('vegetarian', False),
                        'recipe_id': recipe_id,
                        'meal_type': meal_name,
                        'date': self.date,
                        'university': 'harvard'
                    }

                    detailed_items.append(formatted_item)
                    print(f"  -> Processed: {formatted_item['food_name']}")

                except Exception as e:
                    print(f"Error fetching recipe {recipe_id}: {str(e)}")
                    continue

            return detailed_items

        except Exception as e:
            print(f"Error fetching menu for {self.meal_types.get(meal_id, 'unknown meal')}: {str(e)}")
            return []

    def format_nutrition_info(self, recipe_data):
        """Format nutrition information from Harvard API to readable text"""
        nutrition_parts = []

        # Add serving size
        serving_size = recipe_data.get('serving_size', '')
        if serving_size:
            nutrition_parts.append(f"Serving size: {serving_size}")

        # Add calories
        calories = recipe_data.get('calories')
        if calories:
            nutrition_parts.append(f"Calories {calories}")

        # Add macronutrients
        protein = recipe_data.get('protein', {})
        if isinstance(protein, dict) and protein.get('amount'):
            amount = str(protein['amount']).replace('g', '') if isinstance(protein['amount'], str) else protein['amount']
            nutrition_parts.append(f"Protein (g) {amount}")

        total_carbs = recipe_data.get('total_carbohydrates', {})
        if isinstance(total_carbs, dict) and total_carbs.get('amount'):
            amount = str(total_carbs['amount']).replace('g', '') if isinstance(total_carbs['amount'], str) else total_carbs['amount']
            nutrition_parts.append(f"Total Carbohydrates (g) {amount}")

        sugars = recipe_data.get('sugars')
        if sugars:
            amount = str(sugars).replace('g', '') if isinstance(sugars, str) and 'g' in str(sugars) else sugars
            nutrition_parts.append(f"Sugar (g) {amount}")

        total_fat = recipe_data.get('total_fat', {})
        if isinstance(total_fat, dict) and total_fat.get('amount'):
            amount = str(total_fat['amount']).replace('g', '') if isinstance(total_fat['amount'], str) else total_fat['amount']
            nutrition_parts.append(f"Total Fat (g) {amount}")

        sat_fat = recipe_data.get('saturated_fat', {})
        if isinstance(sat_fat, dict) and sat_fat.get('amount'):
            amount = str(sat_fat['amount']).replace('g', '') if isinstance(sat_fat['amount'], str) else sat_fat['amount']
            nutrition_parts.append(f"Saturated Fat (g) {amount}")

        trans_fat = recipe_data.get('trans_fat')
        if trans_fat:
            amount = str(trans_fat).replace('g', '') if isinstance(trans_fat, str) and 'g' in str(trans_fat) else trans_fat
            nutrition_parts.append(f"Trans Fat (g) {amount}")

        cholesterol = recipe_data.get('cholesterol', {})
        if isinstance(cholesterol, dict) and cholesterol.get('amount'):
            amount = str(cholesterol['amount']).replace('mg', '') if isinstance(cholesterol['amount'], str) else cholesterol['amount']
            nutrition_parts.append(f"Cholesterol (mg) {amount}")

        sodium = recipe_data.get('sodium', {})
        if isinstance(sodium, dict) and sodium.get('amount'):
            amount = str(sodium['amount']).replace('mg', '') if isinstance(sodium['amount'], str) else sodium['amount']
            nutrition_parts.append(f"Sodium (mg) {amount}")

        fiber = recipe_data.get('dietary_fiber', {})
        if isinstance(fiber, dict) and fiber.get('amount'):
            amount = str(fiber['amount']).replace('g', '') if isinstance(fiber['amount'], str) else fiber['amount']
            nutrition_parts.append(f"Fiber (g) {amount}")

        # Add ingredients if available
        ingredients = recipe_data.get('ingredients', '')
        if ingredients:
            nutrition_parts.append(f"Ingredients: {ingredients}")

        return " ".join(nutrition_parts) if nutrition_parts else "Nutrition info not available"

    def save_to_file(self, food_data_list, meal_type):
        """Save Harvard API data to local JSON file"""
        try:
            file_path = f'data/scraped_data/harvard/food_items_{meal_type}.json'

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(food_data_list, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(food_data_list)} {meal_type} items to {file_path}")
            return True

        except Exception as e:
            print(f"Error saving {meal_type} data: {e}")
            return False

    def scrape_all_meals(self):
        """Scrape all meals for Harvard Annenberg Hall"""
        print(f"Starting Harvard API scraping for {self.date}")
        print(f"Location: Annenberg Hall (Main Undergraduate Dining)")

        all_items = []
        is_weekend = datetime.strptime(self.date, '%Y-%m-%d').weekday() >= 5

        try:
            if is_weekend:
                print("Weekend detected - scraping brunch and dinner only")
                # On weekends, breakfast/lunch combined as brunch
                brunch_items = self.get_menu_for_meal(0)  # Use breakfast endpoint for brunch
                dinner_items = self.get_menu_for_meal(2)

                if brunch_items:
                    self.save_to_file(brunch_items, 'breakfast')
                    all_items.extend(brunch_items)

                if dinner_items:
                    self.save_to_file(dinner_items, 'dinner')
                    all_items.extend(dinner_items)

            else:
                print("Weekday detected - scraping all three meals")
                for meal_id, meal_name in self.meal_types.items():
                    meal_items = self.get_menu_for_meal(meal_id)
                    if meal_items:
                        self.save_to_file(meal_items, meal_name)
                        all_items.extend(meal_items)

            # Save combined data
            if all_items:
                combined_path = f'data/cleaned_data/harvard/all_food_items_cleaned.json'
                with open(combined_path, 'w', encoding='utf-8') as f:
                    json.dump(all_items, f, indent=2, ensure_ascii=False)
                print(f"Saved combined Harvard data: {combined_path}")

                # Upload to database
                print("Uploading Harvard data to database...")
                uploader = SupabaseUploader('harvard_cleaned_data')
                uploader.upload_json_file(combined_path)

                print(f"Successfully scraped and uploaded {len(all_items)} Harvard items")
                return True
            else:
                print("No Harvard data found to process")
                return False

        except Exception as e:
            print(f"Error in Harvard scraping: {str(e)}")
            return False

def scrape_harvard(date=None):
    """Standalone function to scrape Harvard dining data"""
    scraper = HarvardAPIScraper(date)
    return scraper.scrape_all_meals()

if __name__ == "__main__":
    # Test the Harvard scraper
    success = scrape_harvard()
    print(f"Harvard scraping completed: {'Success' if success else 'Failed'}")