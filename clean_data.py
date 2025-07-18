import json
import re
import os
from dotenv import load_dotenv
from supabase import create_client
from database import SupabaseUploader

class FoodDataCleaner:
    
    def __init__(self):
        """Initialize Supabase connection"""
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials in .env file")
        
        self.supabase = create_client(url, key)
    
    @staticmethod
    def extract_nutrition_info(text):
        """Extract structured nutrition information from messy text"""
        
        # Initialize nutrition dictionary
        nutrition = {}
        
        # Clean the text first
        text = text.replace('\n', ' ').replace('Close', '').strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        
        # Extract serving information
        serving_match = re.search(r'Serving size:\s*([^%\n]+?)(?=Calories|$)', text, re.IGNORECASE)
        if serving_match:
            nutrition['serving_size'] = serving_match.group(1).strip()
        
        # Extract calories
        calories_match = re.search(r'Calories\s+(\d+)', text)
        if calories_match:
            nutrition['calories'] = int(calories_match.group(1))
        
        # Define nutrient patterns with their units
        nutrient_patterns = {
            'protein_g': r'Protein \(g\)\s+([\d.]+|less than \d+ gram)',
            'carbs_g': r'Total Carbohydrates \(g\)\s+([\d.]+|less than \d+ gram)', 
            'sugar_g': r'Sugar \(g\)\s+([\d.]+|less than \d+ gram|\d+)',
            'total_fat_g': r'Total Fat \(g\)\s+([\d.]+)',
            'saturated_fat_g': r'Saturated Fat \(g\)\s+([\d.]+)',
            'trans_fat_g': r'Trans Fat \(g\)\s+([\d.]+|-)',
            'cholesterol_mg': r'Cholesterol \(mg\)\s+([\d.]+|less than \d+ milligrams)',
            'dietary_fiber_g': r'Dietary Fiber \(g\)\s+([\d.]+|less than \d+ gram)',
            'sodium_mg': r'Sodium \(mg\)\s+([\d.]+)',
            'potassium_mg': r'Potassium \(mg\)\s+([\d.]+|-)',
            'calcium_mg': r'Calcium \(mg\)\s+([\d.]+)',
            'iron_mg': r'Iron \(mg\)\s+([\d.]+)',
            'vitamin_d_iu': r'Vitamin D \(IU\)\s+([\d.]+\+?|0\+?|-)',
            'vitamin_c_mg': r'Vitamin C \(mg\)\s+([\d.]+\+?|0\+?|-)',
            'vitamin_a_re': r'Vitamin A \(RE\)\s+([\d.]+|-)'
        }
        
        # Extract each nutrient
        for nutrient, pattern in nutrient_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                # Clean up the value
                if value == '-':
                    nutrition[nutrient] = 0
                elif 'less than' in value.lower():
                    # Extract number from "less than X gram/milligrams"
                    num_match = re.search(r'(\d+)', value)
                    if num_match:
                        nutrition[nutrient] = f"<{num_match.group(1)}"
                    else:
                        nutrition[nutrient] = "<1"
                elif '+' in value:
                    nutrition[nutrient] = float(value.replace('+', ''))
                else:
                    try:
                        nutrition[nutrient] = float(value)
                    except ValueError:
                        nutrition[nutrient] = value
        
        # Extract allergens
        allergen_match = re.search(r'Allergens:\s*([^*\n]+?)(?=Ingredients|$)', text, re.IGNORECASE)
        if allergen_match:
            allergens_text = allergen_match.group(1).strip()
            if allergens_text and allergens_text != '':
                nutrition['allergens'] = [allergen.strip() for allergen in allergens_text.split(',') if allergen.strip()]
            else:
                nutrition['allergens'] = []
        else:
            nutrition['allergens'] = []
        
        # Extract ingredients
        ingredients_match = re.search(r'Ingredients:\s*([^*\n]+?)(?=\*|$)', text, re.IGNORECASE)
        if ingredients_match:
            ingredients_text = ingredients_match.group(1).strip()
            # Remove the ^ symbol that appears after ingredients
            ingredients_text = re.sub(r'\^', '', ingredients_text)
            nutrition['ingredients'] = ingredients_text
        else:
            nutrition['ingredients'] = ""
        
        return nutrition
    
    @staticmethod
    def clean_food_data():
        """ Main function to clean all food data files (currently active method)"""

        # Create output directory
        os.makedirs('data/cleaned_data', exist_ok=True)
        
        # File paths with meal types
        file_configs = [
            {"path": "data/scraped_data/food_items_breakfast.json", "meal_type": "breakfast"},
            {"path": "data/scraped_data/food_items_lunch.json", "meal_type": "lunch"}, 
            {"path": "data/scraped_data/food_items_dinner.json", "meal_type": "dinner"}
        ]
        
        all_cleaned_data = []
        
        for config in file_configs:
            file_path = config["path"]
            meal_type = config["meal_type"]
            
            try:
                # Load the JSON data
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                cleaned_items = []
                
                for item in data:
                    # Extract structured nutrition info
                    nutrition_info = FoodDataCleaner.extract_nutrition_info(item['nutritional_info'])
                    
                    # Create cleaned item with meal type
                    cleaned_item = {
                        'meal_type': meal_type,
                        'station_name': item['station_name'],
                        'food_name': item['food_name'],
                        'nutrition': nutrition_info
                    }
                    
                    cleaned_items.append(cleaned_item)
                    all_cleaned_data.append(cleaned_item)
                
                # Save individual cleaned file
                filename = os.path.basename(file_path)
                output_path = f'data/cleaned_data/{filename}'
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_items, f, indent=2, ensure_ascii=False)
                
                print(f"Cleaned and saved: {output_path}")
                print(f"Processed {len(cleaned_items)} {meal_type} items")
                
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
        
        """Remember that I am not deleting all the data from the db cuz there's already a cron job at the db side (supabase) """

        # Save combined cleaned data
        combined_output_path = 'data/cleaned_data/all_food_items_cleaned.json'
        with open(combined_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_cleaned_data, f, indent=2, ensure_ascii=False)
        
        # Upload to database
        uploader = SupabaseUploader()
        uploader.upload_json_file(combined_output_path)
        
        return all_cleaned_data