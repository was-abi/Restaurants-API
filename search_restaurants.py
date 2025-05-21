import googlemaps
from typing import List, Dict
import time
import csv
from datetime import datetime

def get_api_key() -> str:
    # Replace with your Google Cloud API key
    return "AIzaSyCBaGYJsxA3ESVEP9fDxKkkdkrqzHBNQtI"

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
        
        restaurants = []
        
        result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            type='restaurant'
        )
        
        restaurants.extend(result.get('results', []))
        
        # Get next page only if we need more results to reach 50
        while 'next_page_token' in result and len(restaurants) < 50:
            time.sleep(2)
            result = gmaps.places_nearby(
                location=(lat, lng),
                radius=radius,
                type='restaurant',
                page_token=result['next_page_token']
            )
            restaurants.extend(result.get('results', []))
        
        # Limit to 50 results
        return restaurants[:50]
    except Exception as e:
        print(f"Error getting restaurants: {e}")
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
    print(f"\nSearching for restaurants near {selected_location}...")
    restaurants = get_restaurants(gmaps, selected_location, radius_meters)

    # Display and save results
    if restaurants:
        print(f"\nFound {len(restaurants)} restaurants:")
        
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