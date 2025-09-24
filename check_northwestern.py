import json

files = ['breakfast', 'lunch', 'dinner']
total_items = 0

for meal in files:
    data = json.load(open(f'C:/My Projects/NutriGrove/NutriGrove-Scraper/data/scraped_data/northwestern/food_items_{meal}.json'))
    stations = set([item['station_name'] for item in data])
    print(f'{meal.title()}: {len(data)} items across {len(stations)} stations')
    total_items += len(data)

print(f'Northwestern Total Items: {total_items}')

# Let's compare with other universities
print("\n" + "="*50)
print("COMPARISON WITH OTHER UNIVERSITIES:")
print("="*50)

import os
universities = ['umassd', 'wpi', 'northeastern', 'babson', 'fitchburg', 'lasell']

for uni in universities:
    uni_path = f'C:/My Projects/NutriGrove/NutriGrove-Scraper/data/scraped_data/{uni}'
    if os.path.exists(uni_path):
        uni_total = 0
        for meal in files:
            file_path = f'{uni_path}/food_items_{meal}.json'
            if os.path.exists(file_path):
                data = json.load(open(file_path))
                uni_total += len(data)
        print(f'{uni}: {uni_total} total items')
    else:
        print(f'{uni}: No data found')

# Check Harvard
harvard_path = 'C:/My Projects/NutriGrove/NutriGrove-Scraper/data/scraped_data/harvard'
if os.path.exists(harvard_path):
    harvard_total = 0
    for meal in files:
        file_path = f'{harvard_path}/food_items_{meal}.json'
        if os.path.exists(file_path):
            data = json.load(open(file_path))
            harvard_total += len(data)
    print(f'harvard: {harvard_total} total items')