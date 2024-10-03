# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 12:15:05 2024

@author: Lorena Carpes
"""
#source: ChatGPT 4.0

import pandas as pd
import googlemaps
import time
import os

# Initialize Google Maps Client
API_KEY = "YOUR_GOOGLE_API_KEY"
gmaps = googlemaps.Client(key=API_KEY)

#Load your data
file_path = 'path/to/your/input_file.csv' 
geocoded_data = pd.read_csv(file_path)


# Check for existing geocoded cache file
cache_file = 'path/to/your/geocode_cache.csv'
if os.path.exists(cache_file):
    geocode_cache = pd.read_csv(cache_file).set_index('city').to_dict(orient='index')
else:
    geocode_cache = {}

# Function to save cache incrementally
def save_cache():
    """
    Saves the current state of the geocoded data cache incrementally to a CSV file.
    The cache stores previously geocoded city data (city name, coordinates, and country).
    """
    cache_df = pd.DataFrame.from_dict(geocode_cache, orient='index')
    cache_df.reset_index(inplace=True)
    cache_df.columns = ['city', 'coordinates', 'country', 'country_code']
    cache_df.to_csv(cache_file, index=False)

# List of country codes for Americas and Oceania
americas_oceania_countries = [
    'US', 'CA', 'MX', 'GT', 'BZ', 'SV', 'HN', 'NI', 'CR', 'PA',  # North America & Central America
    'CO', 'VE', 'GY', 'SR', 'BR', 'PE', 'BO', 'CL', 'AR', 'UY', 'PY', 'EC',  # South America
    'CU', 'HT', 'DO', 'JM', 'BS', 'TT', 'BB', 'AG', 'DM', 'GD', 'LC', 'VC', 'KN',  # Caribbean
    'AU', 'NZ', 'FJ', 'PG', 'SB', 'VU', 'WS', 'TO', 'KI', 'TV', 'NR', 'PW', 'FM', 'MH'  # Oceania
]

# List of country codes for Europe
european_countries = [
    'AL', 'AD', 'AM', 'AT', 'BY', 'BE', 'BA', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'GE',
    'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'KZ', 'XK', 'LV', 'LI', 'LT', 'LU', 'MT', 'MD', 'MC', 'ME',
    'NL', 'MK', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB'
]

# Function to geocode with Europe constraint for cities before 1500
def geocode_city(city_name, year):
    """
    Geocodes a city name using the Google Maps API, prioritizing locations in Europe if the year is <= 1500.
    
    Args:
        city_name (str): The name of the city to geocode.
        year (int): The year of relevance (e.g., birth year or death year).
    
    Returns:
        tuple: Contains the city name, coordinates (latitude, longitude), country name, and country code.
    """
    time.sleep(1)  # Rate limiting
    
    # Geocode the city
    geocode_result = gmaps.geocode(city_name)
    
    if geocode_result:
        europe_location = None
        country_name = None
        country_code = None # Get country code for more precise identification

        for result in geocode_result:
            address_components = result['address_components']
            for component in address_components:
                # Extract the country name and country code from the address components
                if 'country' in component['types']:
                    country_name = component['long_name']
                    country_code = component['short_name']
                
                # Check if location is in Europe (using country codes for Europe)
                if country_code in european_countries:
                    europe_location = result['geometry']['location']
                    break  # Prioritize European location if found

        # If European location is found and year <= 1500, use European location
        if year <= 1500 and europe_location:
            return city_name, (europe_location['lat'], europe_location['lng']), country_name, country_code
        
        # Otherwise, use the first result
        location = geocode_result[0]['geometry']['location']
        return city_name, (location['lat'], location['lng']), country_name, country_code
    
    # Return None if no result found
    return city_name, (None, None), None, None

# Step 1: Identify unique city names across columns for geocoding
city_columns = ['borncity', 'deathcity', 'activecity']

# Step 2: Create new columns to track incorrect geocodes in the Americas or Oceania before 1500 for each location type
geocoded_data['borncity_americas_or_oceania_before_1500'] = ""
geocoded_data['deathcity_americas_or_oceania_before_1500'] = ""
geocoded_data['activecity_americas_or_oceania_before_1500'] = ""

# Step 3: Go through each city in each column and build the geocoding cache
for _, row in geocoded_data.iterrows():
    for city_col, flag_col in [('borncity', 'borncity_americas_or_oceania_before_1500'), 
                               ('deathcity', 'deathcity_americas_or_oceania_before_1500'), 
                               ('activecity', 'activecity_americas_or_oceania_before_1500')]:
        
        city = row[city_col]
        # Prioritize deathyear, and if not available, use birthyear + 60 as an estimate
        year = row['deathyear'] if pd.notna(row['deathyear']) else (row['birthyear'] + 60 if pd.notna(row['birthyear']) else None)
        
        if pd.notna(city):  # If city is not missing
            if city not in geocode_cache:
                # Geocode city with constraints if not cached
                city_name, coordinates, country, country_code = geocode_city(city, year)
                if coordinates != (None, None):  # Save successful geocoding
                    geocode_cache[city] = {'coordinates': coordinates, 'country': country, 'country_code': country_code}
                    save_cache()  # Save incrementally after each city
                else:
                    # If geocoding failed, set placeholder value
                    print(f"Geocoding failed for city: {city}")
                    geocode_cache[city] = {'coordinates': (None, None), 'country': None, 'country_code': None}
            
            # Now safely access the cached city data
            cached_city = geocode_cache.get(city, {})
            
            # Check if 'country_code' exists in the cache, if not skip or handle it
            country_code = cached_city.get('country_code', None)
            if country_code is None:
                print(f"Missing country code for city: {city}")
                continue  # Skip this city if country code is missing
            
            # Check if the city is in Americas/Oceania and the year is before 1500
            is_in_americas_or_oceania = country_code in americas_oceania_countries
            before_1500 = year <= 1500 if year else False
            
            # Set the flag dynamically
            if before_1500 and is_in_americas_or_oceania:
                geocoded_data.at[_, flag_col] = "yes"
            else:
                geocoded_data.at[_, flag_col] = "no"

# Step 4: Map the geocoded coordinates and country back to the DataFrame
def map_coordinates(df, city_col):
    """
    Maps the geocoded coordinates and country information back to the DataFrame 
    based on previously cached geocode results.
    
    Args:
        df (pd.DataFrame): The DataFrame containing the city data.
        city_col (str): The column name for the city (e.g., 'borncity', 'deathcity', or 'activecity').
    
    Returns:
        pd.DataFrame: Updated DataFrame with the coordinates and country mapped.
    """
   
    df[f'{city_col}_coordinates'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('coordinates', ""))
    df[f'{city_col}_country'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('country', ""))
    
    return df

# Apply mapping to all city columns (borncity, deathcity, activecity)
for city_col in city_columns:
    geocoded_data = map_coordinates(geocoded_data, city_col)

# Step 5: Reorder the columns to place americas_or_oceania_before_1500 after the country columns
cols = ['borncity_coordinates', 'borncity_country', 'borncity_americas_or_oceania_before_1500', 
        'deathcity_coordinates', 'deathcity_country', 'deathcity_americas_or_oceania_before_1500', 
        'activecity_coordinates', 'activecity_country', 'activecity_americas_or_oceania_before_1500']

# Reorder DataFrame columns
geocoded_data = geocoded_data[['indexauthor', 'starturl', 'birthyear', 'deathyear', 'nameandbirthdeathyear', 
                               'georeferenceurl', 'borncity', 'deathcity', 'activecity'] + cols]


# Step 4: Save the DataFrame with the geocoded results
output_file_csv = 'path/to/your/output_file.csv'  # Save CSV
output_file_excel = 'path/to/your/output_file.xlsx'  # Save Excel

geocoded_data.to_csv(output_file_csv, index=False)
geocoded_data.to_excel(output_file_excel, index=False)

print("Geocoding completed and files saved.")