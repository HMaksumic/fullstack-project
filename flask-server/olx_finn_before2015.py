import requests
import re
import json

def normalize_name(name):
    name = re.sub(r'(?i)\b(4matic|masse|utstyr|eu|ny|kontroll|service|oljeskift|cdi|tdi|dci|mpi|gdi|tdci|tfsi|tsi|td|cd|thp|blueefficiency|novi|model|triptonic|stanje|top|gtd|god|2008|2009|2010|2011|2012|2013|2014|2015|2016|2017|2018|2019|2020|2021|2022|2023|2024|quattro|facelift|motion|tek|uvezana|uvoz|limited|edition|luxury|premium|base|sport|advanced|line|drive|paket|paket|edition|automatic|manual|diesel|sedan|hatchback|coupe|convertible|wagon|suv|compact|electric|hybrid|awd|fwd|rwd|l|xl|xxl|plus|pro|classic|comfort|executive|elegance|exclusive|design|performance|dynamic|style|active|emotion|innovation|limited|classic|supreme|highline|comfortline|trendline|elite|cosmo|prestige|cross|drive|line|connect|base|executive|essential|value|p|performance|track|trail|sportback|touring|all4|countryman|clubman|john|cooper|works|crosstrek|outback|forester|brz|wrx|sti|limited|touring|premium|black|edition|signature|select|preferred|standard|touring|cx|forester|sport|special|series|2dr|4dr|5dr|7dr|12dr|15dr|21dr|23dr|32dr|40dr|45dr|5seater|7seater|compact|mpv|minivan|roadster|crossover|gtline|cabrio|cabriolet|estate|estate|saloon|super|base|lifestyle|lux|xdrive|xdrive20d|d|rline|spaceback|vision|entry|entryline|life|light|ultimate|evo|ambiente|sve|sve|emotion|dynamic|action|line|tek|tronic|select|stand|entry|vtx|ls|dl|sx|hx|xe|xt|kt|xt|tm|hk|tl)\b', '', name)

    name = re.sub(r'\W+', ' ', name)
    name = re.sub(r'\b\d+hk\b', '', name, flags=re.IGNORECASE)
    return ' '.join(sorted(name.lower().split()))

#fetching data directly from file
def fetch_finn_data():
    json_file_path = 'data/finn_search_before2015.json'
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("Error: The JSON file was not found.")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

#fetching from olx (several pages of JSON)
def fetch_olx_data(max_pages=60):
    olx_url = 'https://olx.ba/api/search'
    params = {
        'attr': '3228323030382d32303134293a372844697a656c29',
        'attr_encoded': '1',
        'category_id': '18',
        'page': 1,
        'per_page': 175  
    }
    
    olx_data = []
    
    while params['page'] <= max_pages:
        try:
            response = requests.get(olx_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            #car entries are under data in the olx api
            page_data = data.get('data', [])
            olx_data.extend(page_data)
            print(f"Page {params['page']} fetched, {len(page_data)} items.")
            params['page'] += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from OLX API: {e}")
            break
        except ValueError as e:
            print(f"Error parsing JSON from OLX API: {e}")
            break
    
    return olx_data

#car matching logic
def match_car(finn_car, olx_car):
    # Extracting year information
    finn_year = finn_car.get('year', 0)
    olx_labels = olx_car.get('special_labels', [])
    olx_year = next((int(label.get('value')) for label in olx_labels if label.get('label') == 'Godište'), 0)
    
    # First check if the years match closely
    if abs(finn_year - olx_year) <= 1:
        # Normalize and compare names if years are close
        finn_name = normalize_name(finn_car.get('heading', ''))
        olx_name = normalize_name(olx_car.get('title', ''))
        print(f"Matching {finn_name} and {olx_name}")
        return finn_name in olx_name or olx_name in finn_name
    return False

def pair_car_data(finn_data, olx_data):
    car_pairs = {}

    if not isinstance(finn_data, list) or not isinstance(olx_data, list):
        print("Error: Expected list format for API data")
        return car_pairs

    #creating dictionaries with normalized names for finn api
    for car in finn_data:
        car_name = normalize_name(car.get('heading', ''))
        car_price = car.get('price', {}).get('amount')
        car_link = car.get('canonical_url', '')
        car_year = car.get('year', 0)
        car_original_name = car.get('heading', '')
        car_image_url = car.get('image', {}).get('url', '')
        car_regno = car.get('regno', '')
        if car_name and car_price is not None:
            if car_name not in car_pairs:
                car_pairs[car_name] = {
                    'finn_price': car_price,
                    'olx_prices': [],
                    'year': car_year,
                    'link': car_link,
                    'original_name': car_original_name,
                    'image_url': car_image_url,
                    'regno': car_regno,
                    'olx_ids' : []
                }

    #pairing with corresponding olx cars and their prices
    for car in olx_data:
        if isinstance(car, dict):  # Ensure car is a dictionary
            olx_name = normalize_name(car.get('title', ''))
            olx_price = car.get('price')
            olx_id = car.get('id')

            if olx_name and olx_price is not None:

                for finn_name, data in car_pairs.items():
                    if match_car({'heading': finn_name, 'year': data['year']}, car):
                        car_pairs[finn_name]['olx_prices'].append(olx_price)
                        car_pairs[finn_name]['olx_ids'].append(olx_id)
                        break

    return car_pairs

finn_data = fetch_finn_data()
olx_data = fetch_olx_data()

paired_data = pair_car_data(finn_data, olx_data)

olx_finn_output = []
for car_name, data in paired_data.items():
    olx_prices = data['olx_prices']
    if olx_prices:
        finn_price = data['finn_price']
        year = data['year']
        link = data['link']
        original_name = data['original_name']
        image_url = data['image_url']
        regno = data['regno']
        olx_ids = data['olx_ids']

        #creating json entry for each car
        car_entry = {
            'car_name': original_name,
            'normalized_name': car_name,
            'year': year,
            'finn_price': finn_price,
            'finn_link': link,
            'image_url': image_url,
            'regno': regno,
            'olx_prices': olx_prices,
            'olx_ids' : olx_ids
        }
        olx_finn_output.append(car_entry)

with open('data/olx_finn_before2015.json', 'w', encoding='utf-8') as json_file:
    json.dump(olx_finn_output, json_file, ensure_ascii=False, indent=4)

import datetime
with open('__LOG__.txt', 'a', encoding='utf-8') as file:
    file.write(f"{datetime.datetime.now()} - olx_finn_before2015.py ran\n")