import requests
import re

def normalize_name(name):
    return re.sub(r'\W+', '', name).lower()

#fetching data from own finn.no API
def fetch_finn_data():
    finn_url = 'http://127.0.0.1:8080/api/finn_website_search'
    try:
        response = requests.get(finn_url)
        response.raise_for_status()
        data = response.json()
        props = data.get('props', {})
        page_props = props.get('pageProps', {})
        search_data = page_props.get('search', {}).get('docs', [])
        return search_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Finn API: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON from Finn API: {e}")
        return []

#fetching from olx (several pages of JSON)
def fetch_olx_data(max_pages=60):
    olx_url = 'https://olx.ba/api/search'
    params = {
        'attr': '372844697a656c29',
        'attr_encoded': '1',
        'category_id': '18',
        'page': 1,
        'per_page': 100  
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
    finn_name = normalize_name(finn_car.get('heading', ''))
    olx_name = normalize_name(olx_car.get('title', ''))
    if finn_name in olx_name or olx_name in finn_name:
        finn_year = finn_car.get('year', 0)
        olx_year = olx_car.get('special_labels', [])
        olx_year = next((int(label.get('value')) for label in olx_year if label.get('label') == 'Godište'), 0)
        return abs(finn_year - olx_year) <= 2
    return False

# Function to pair and organize the data
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
        if car_name and car_price is not None:
            if car_name not in car_pairs:
                car_pairs[car_name] = {
                    'finn_price': car_price,
                    'olx_prices': [],
                    'year': car_year,
                    'link': car_link
                }

    #pairing with corresponding olx cars and their prices
    for car in olx_data:
        if isinstance(car, dict):  # Ensure car is a dictionary
            olx_name = normalize_name(car.get('title', ''))
            olx_price = car.get('price')
            if olx_name and olx_price is not None:
                for finn_name, data in car_pairs.items():
                    if match_car({'heading': finn_name, 'year': data['year']}, car):
                        car_pairs[finn_name]['olx_prices'].append(olx_price)
                        break

    return car_pairs

finn_data = fetch_finn_data()
olx_data = fetch_olx_data()

paired_data = pair_car_data(finn_data, olx_data)

#Display organized data, only if there are olx prices associated with a finn price car: 
#For debug purpouses, this has to be made into JSON format and hten made into its own API to finally have proper data to send to frontend.
for car_name, data in paired_data.items():
    olx_prices = data['olx_prices']
    if olx_prices:
        finn_price = data['finn_price']
        year = data['year']
        link = data['link']
        print(f"Car: {car_name} (Year: {year})")
        print(f"  Finn price: {finn_price} NOK")
        print(f"  Finn link: {link}")
        print(f"  OLX prices: {', '.join(map(str, olx_prices))} KM")
        print()