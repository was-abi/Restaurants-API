import googlemaps
from typing import List, Dict
import time
import csv
from datetime import datetime
from math import cos, radians

def get_api_key() -> str:
    # Replace with your Google Cloud API key
    return "AIzaSyBfbFOPk9gTu1-wQyxRfqoBZB5kLXRdHu0"

def get_location_suggestions(gmaps: googlemaps.Client, input_text: str) -> List[Dict]:
    try:
        autocomplete_results = gmaps.places_autocomplete(
            input_text,
            types=['geocode']  # This restricts results to geographical locations
        )
        return autocomplete_results
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return []

def get_restaurants(gmaps: googlemaps.Client, location: str, radius: int) -> List[Dict]:
    try:
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return []
        
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        
        all_places = []
        
        # Extended place types with more specific categories
        place_types = [
            'restaurant',
            'cafe',
            'food_court',
            'bar',
            'bakery',
            # Additional specific restaurant types
            'indian_restaurant',
            'chinese_restaurant',
            'fast_food_restaurant',
            'italian_restaurant',
            'vegetarian_restaurant'
        ]
        
        # Create a grid of points to search from
        grid_size = 2  # This will create a 2x2 grid
        lat_step = (radius * 2 / 111000) / grid_size  # Convert meters to degrees
        lng_step = (radius * 2 / (111000 * cos(radians(lat)))) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                search_lat = lat + (i - grid_size/2) * lat_step
                search_lng = lng + (j - grid_size/2) * lng_step
                
                for place_type in place_types:
                    result = gmaps.places_nearby(
                        location=(search_lat, search_lng),
                        radius=radius // grid_size,
                        type=place_type
                    )
                    
                    all_places.extend(result.get('results', []))
                    
                    while 'next_page_token' in result:
                        time.sleep(2)
                        result = gmaps.places_nearby(
                            location=(search_lat, search_lng),
                            radius=radius // grid_size,
                            type=place_type,
                            page_token=result['next_page_token']
                        )
                        all_places.extend(result.get('results', []))
        
        # Remove duplicates based on place_id
        unique_places = {place['place_id']: place for place in all_places}.values()
        
        # Limit to 1000 results
        return list(unique_places)[:1000]
    except Exception as e:
        print(f"Error getting places: {e}")
        return []

def save_to_csv(restaurants_data: List[Dict], location: str, gmaps: googlemaps.Client):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"restaurants_{location.replace(' ', '_')}_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(['Name', 'Address', 'Website', 'Phone'])
        
        # Write restaurant data
        for restaurant in restaurants_data:
            name = restaurant.get('name', 'N/A')
            address = restaurant.get('vicinity', 'N/A')
            
            # Get additional details
            place_details = gmaps.place(restaurant['place_id'], fields=['website', 'formatted_phone_number'])
            details = place_details.get('result', {})
            
            website = details.get('website', 'N/A')
            phone = details.get('formatted_phone_number', 'N/A')
            
            writer.writerow([name, address, website, phone])
    
    print(f"\nResults saved to {filename}")

def main():
    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=get_api_key())
    
    # Get location input with suggestions
    location_input = input("Start typing location: ")
    while True:
        suggestions = get_location_suggestions(gmaps, location_input)
        
        if not suggestions:
            print("No suggestions found.")
            break
            
        print("\nLocation suggestions:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"{i}. {suggestion['description']}")
            
        choice = input("\nSelect a number (or press Enter to type again): ")
        if choice.isdigit() and 1 <= int(choice) <= len(suggestions[:5]):
            selected_location = suggestions[int(choice)-1]['description']
            break
        location_input = input("Start typing location: ")

    # Get radius input
    radius_km = float(input("Enter search radius in km (e.g., 5): "))
    radius_meters = int(radius_km * 1000)  # Convert km to meters

    # Get restaurants
    print(f"\nSearching for restaurants and cafes near {selected_location}...")
    restaurants = get_restaurants(gmaps, selected_location, radius_meters)

    # Display and save results
    if restaurants:
        print(f"\nFound {len(restaurants)} food businesses:")
        
        # Create a list to store processed restaurant data
        restaurant_data = []
        
        for i, restaurant in enumerate(restaurants, 1):
            # Get additional details
            place_details = gmaps.place(restaurant['place_id'], fields=['website', 'formatted_phone_number'])
            details = place_details.get('result', {})
            # Add to restaurant data
            restaurant_data.append({
                'name': restaurant.get('name', 'N/A'),
                'vicinity': restaurant.get('vicinity', 'N/A'),
                'place_id': restaurant['place_id']
            })
        
        # Save results to CSV
        # Update the save_to_csv call to include gmaps
        save_to_csv(restaurant_data, selected_location, gmaps)
    else:
        print("No restaurants found in the specified area.")

if __name__ == "__main__":
    main()