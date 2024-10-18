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
author_data = pd.read_excel(file_path)


# Check for existing geocoded cache file
cache_file = 'path/to/your/geocode_cache.csv'
if os.path.exists(cache_file):
    geocode_cache = pd.read_csv(cache_file).set_index('city').to_dict(orient='index')
else:
    geocode_cache = {}

# Function to save cache incrementally
def save_cache():
    """
    Saves the current geocode cache to a CSV file incrementally.
    Converts the cache dictionary to a DataFrame and writes it to a CSV file.

    Args:
        None
    
    Returns:
        None
    """
    cache_df = pd.DataFrame.from_dict(geocode_cache, orient='index')
    cache_df.reset_index(inplace=True)
    cache_df.columns = ['city', 'coordinates', 'country', 'city_id']
    cache_df.to_csv(cache_file, index=False)

americas_or_oceania_countries = [
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

year_discovery = {
    # North America & Central America 
    'BZ': 1502, 'CA': 1497, 'CR': 1502, 'GT': 1523, 'HN': 1502, 'MX': 1519, 'NI': 1524, 'PA': 1501, 'SV': 1524, 'US': 1492,  # (Belize, Canada, Costa Rica, Guatemala, Honduras, Mexico, Nicaragua, Panama, El Salvador, United States)
    # South America
    'AR': 1516, 'BO': 1535, 'BR': 1500, 'CL': 1520, 'CO': 1499, 'EC': 1531, 'GY': 1498, 'PE': 1526, 'PY': 1537, 'SR': 1593, 'UY': 1516, 'VE': 1498, # (Argentina, Bolivia, Brazil, Chile, Colombia, Ecuador, Guyana, Peru, Paraguay, Suriname, Uruguay, Venezuela)
    # Caribbean 
    'AG': 1493, 'BB': 1492, 'BS': 1492, 'CU': 1492, 'DM': 1493, 'DO': 1492, 'GD': 1498, 'HT': 1492, 'JM': 1494, 'KN': 1493, 'LC': 1502, 'TT': 1498, 'VC': 1498,  # (Antigua and Barbuda, Barbados, Bahamas, Cuba, Dominica, Dominican Republic, Grenada, Haiti, Jamaica, Saint Kitts and Nevis, Saint Lucia, Trinidad and Tobago, Saint Vincent and the Grenadines)
    # Oceania
    'AU': 1606, 'FM': 1529, 'FJ': 1643, 'KI': 1528, 'MH': 1529, 'NR': 1798, 'NZ': 1642, 'PW': 1543, 'PG': 1526, 'SB': 1568, 'TO': 1616, 'TV': 1568, 'VU': 1606, 'WS': 1722  # (Australia, Micronesia, Fiji, Kiribati, Marshall Islands, Nauru, New Zealand, Palau, Papua New Guinea, Solomon Islands, Tonga, Tuvalu, Vanuatu, Samoa)
}


# Add necessary columns
author_data['year_map'] = ""
author_data['borncity_coordinates'] = ""
author_data['deathcity_coordinates'] = ""
author_data['activecity_coordinates'] = ""
author_data['borncity_country'] = ""
author_data['deathcity_country'] = ""
author_data['activecity_country'] = ""
author_data['borncity_americas_or_oceania_before_discovery'] = ""
author_data['deathcity_americas_or_oceania_before_discovery'] = ""
author_data['activecity_americas_or_oceania_before_discovery'] = ""
author_data['born_cityid'] = ""
author_data['death_cityid'] = ""
author_data['active_cityid'] = ""


# Define a function to save city data and assign city_id
def save_city_data_and_assign_city_id_column(city_col, author, cache_key, coordinates, country, unique_id):
    """
    Saves city data in the geocode cache, assigns city_id to respective columns, and updates the cache.
    
    Args:
        city_col (str): The column representing the type of city (e.g., 'borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        cache_key (str): The key to cache the city name.
        coordinates (str): The geocoded coordinates of the city.
        country (str): The country where the city is located.
        unique_id (int): The unique city_id to be assigned.
    
    Returns:
        None
    """
    geocode_cache[cache_key] = {'coordinates': coordinates, 'country': country, 'city_id': unique_id}
    if city_col == 'borncity':
        author_data.at[author, 'born_cityid'] = unique_id
    elif city_col == 'deathcity':
        author_data.at[author, 'death_cityid'] = unique_id
    elif city_col == 'activecity':
        author_data.at[author, 'active_cityid'] = unique_id
    save_cache()


        
# Define a function to set the flag based on the year of discovery
def set_flag(city_col, author, country, row):
    """
    Sets the flag 'yes' or 'no' in the column {city_col}_americas_or_oceania_before_discovery
    based on the country's location and its year of discovery.

    Args:
        city_col (str): The column representing the type of city (e.g., 'borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        country (str): The country where the city is located.
        row (pandas.Series): The row of the DataFrame corresponding to the current author being processed.

    Returns:
        None
    """
    is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()
    # Get the year of discovery from the dictionary
    year_discovery_value = year_discovery.get(country, None)
    
    # Ensure the year discovery is available and compare with the year_map
    if year_discovery_value:
        before_year_discovery = row['year_map'] < year_discovery_value
        if before_year_discovery and is_in_americas_or_oceania:
            author_data.at[author, f'{city_col}_americas_or_oceania_before_discovery'] = "yes"
        else:
            author_data.at[author, f'{city_col}_americas_or_oceania_before_discovery'] = "no"
    else:
        # If no year of discovery is available, set the flag as 'no'
        author_data.at[author, f'{city_col}_americas_or_oceania_before_discovery'] = "no"
        


# Define a function to assign unique ID
def assign_unique_id(city_col, author, coordinates, id_cache, unique_id):
    """
    Assigns a unique ID to a city based on its coordinates. If the coordinates are already in the cache, 
    the cached ID is assigned, otherwise a new ID is generated.
    
    Args:
        city_col (str): The column representing the type of city (e.g., 'borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        coordinates (str): The geocoded coordinates of the city.
        id_cache (dict): Cache mapping coordinates to unique IDs.
        unique_id (int): The current unique ID counter.
    
    Returns:
        int: Updated unique ID counter. 
    """
    if coordinates not in id_cache:
        id_cache[coordinates] = unique_id
        author_data.at[author, f'{city_col}_id'] = unique_id
        unique_id += 1
    else:
        author_data.at[author, f'{city_col}_id'] = id_cache[coordinates]
    return unique_id

# Define a function to map coordinates, country, and city_id to the author_data
def map_coordinates(df, city_col):
    """
    Maps the geocoded coordinates, country, and city_id information back to the DataFrame 
    based on previously cached geocode results.
    
    Args:
        df (pandas.DataFrame): The DataFrame containing the city data.
        city_col (str): The column name for the city (e.g., 'borncity', 'deathcity', or 'activecity').
    
    Returns:
        pandas.DataFrame: Updated DataFrame with the coordinates, country, and city_id mapped.
        
    """
    
    df[f'{city_col}_coordinates'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('coordinates', ""))
    df[f'{city_col}_country'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('country', ""))
    df[f'{city_col}_id'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('city_id', ""))
    return df



# Process rows for year_map. For each row, if the death year is not empty, add it to the "year_map" column, if it is empty, add the "birth_year"+ 60
for author, row in author_data.iterrows():
    if pd.notna(row['deathyear']):
        author_data.at[author, "year_map"] = int(row['deathyear'])
    else:
        author_data.at[author, "year_map"] = int(row['birthyear']) + 60
author_data['year_map'] = pd.to_numeric(author_data['year_map'], errors='coerce')

# Initialize a counter for unique IDs
unique_id = 1
id_cache = {}

# In each row, go through each city in each column (born, death and active). If empty return None
for author, row in author_data.iterrows():
    for city_col in ['borncity', 'deathcity', 'activecity']:
        city_name = row[city_col]
        
        # Skip processing if the city name is empty or NaN
        if not city_name or pd.isna(city_name):
            continue
        
        # Create a composite key for the cache using city_name
        cache_key = city_name
        
        # Check if the city is not in the cache
        if city_name not in geocode_cache:
                        
            #geocode using GooGle Maps API
            
            # Modify the geocode_city function to return both coordinates and country
            def geocode_city(city_name, year):
                """
                Geocodes a city using the Google Maps API.
                
                Args:
                    city_name (str): The name of the city to geocode.
                    year (int): The year for historical context (not used directly in this function).
                
                Returns:
                    tuple: The city name, latitude, longitude, and country code.
                """
                time.sleep(1)  # To avoid hitting API limits
                
                geocode_result = gmaps.geocode(city_name)
                
                #If there is only one result for the city:
                if len(geocode_result) == 1:
                    
                    location = geocode_result[0]['geometry']['location']
                    country_code = geocode_result[0]['address_components'][-1]['short_name']  # Get the country code
                    coordinates = f"{location['lat']}, {location['lng']}"
                    
                    # Save the city and set the flag based on the discovery year
                    save_city_data_and_assign_city_id_column(city_col, author, cache_key, coordinates, country_code, unique_id)
                    set_flag(city_col, author, country_code, row)
                    unique_id = assign_unique_id(city_col, author, coordinates, id_cache, unique_id)
                    
                    
                    return city_name, location['lat'], location['lng'], country_code
                
                #If there are multiple results for the city name
                elif len(geocode_result) > 1:
                    europe_location = None
                    americas_oceania_location = None
                    
                    # Loop through the results to check country codes
                    
                    for result in geocode_result:
                        location = result['geometry']['location']
                        country_code = result["address_components"][-1]["short_name"]
                        coordinates = f"{location['lat'], location['lng']}"
                        
                        #Check if the country is in Europe
                        if country_code in european_countries:
                            europe_location = (city_name, location["lat"], location["lng"], country_code)
                            
                         #Check if the country is in Americas or Oceania
                        if country_code in americas_or_oceania_countries:
                            america_oceania_location = (city_name, location['lat'], location['lng'], country_code)
                    
                    # Check the discovery year for countries in the Americas or Oceania
                    if america_oceania_location:
                        country_code = america_oceania_location[3]
                        discovery_year = year_discovery.get(country_code, None)
                        
                        #If the author died before the discovery year, prioritize Europe
                        if discovery_year and year < discovery_year:
                            if europe_location:
                                save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{europe_location[1]}, {europe_location[2]}", europe_location[3], unique_id)
                                set_flag(city_col, author, europe_location[3], row)
                                unique_id = assign_unique_id(city_col, author, f"{europe_location[1]}, {europe_location[2]}", id_cache, unique_id)
                                return europe_location
                            
                            else:
                                #If no European location, prioritize any other non-Americas/Oceania location
                                other_location = None
                                
                                for result in geocode_result:
                                    location = result["geometry"]["location"]
                                    country_code = result["address_components"][-1]["short_name"]
                                    
                                    #Prioritize non-Americas/Oceania countries first
                                    if country_code not in americas_or_oceania_countries and country_code not in european_countries:
                                        other_location = (city_name, location["lat"], location["lng"], country_code)
                                        break
                                    
                                # If there is another location outuside Americas/Oceania, use it 
                                if other_location:
                                    save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{other_location[1]}, {other_location[2]}", other_location[3], unique_id)
                                    set_flag(city_col, author, other_location[3], row)
                                    unique_id = assign_unique_id(city_col, author, f"{other_location[1]}, {other_location[2]}", id_cache, unique_id)
                                    return other_location
                                        
                                # If no other location is found, use Americas/Oceania location
                                if america_oceania_location:
                                    save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{america_oceania_location[1]}, {america_oceania_location[2]}", america_oceania_location[3], unique_id)
                                    set_flag(city_col, author, america_oceania_location[3], row)
                                    unique_id = assign_unique_id(city_col, author, f"{america_oceania_location[1]}, {america_oceania_location[2]}", id_cache, unique_id)
                                    return america_oceania_location
                        
                        #If the year the author died is after the discovery year 
                        else:
                            #Use the first result
                            location = geocode_result[0]['geometry']['location']
                            country_code = geocode_result[0]['address_components'][-1]['short_name']  # Get the country code
                            coordinates = f"{location['lat']}, {location['lng']}"
                            
                            # Save the city and set the flag based on the discovery year
                            save_city_data_and_assign_city_id_column(city_col, author, cache_key, coordinates, country_code, unique_id)
                            set_flag(city_col, author, country_code, row)
                            unique_id = assign_unique_id(city_col, author, coordinates, id_cache, unique_id)
                            return city_name, location['lat'], location['lng'], country_code
                           
                        
                # Return None if geocoding fail
                return city_name, None, None, None    
                    
            
       # If there is a city with the same name in the cache:
        else:     
            # Retrieve all cached results for cities with the same name
            cached_results = geocode_cache[cache_key]
            
            
            # Check if cached_results is a single dictionary or a list
            if isinstance(cached_results, dict):
                cached_results = [cached_results]  # Convert to list if it's a single dictionary
   
                     
            europe_location = None
            america_oceania_location = None
            other_location = None
            
            # Loop through cached results
            for cached_data in cached_results:
                country = cached_data['country']
                coordinates = cached_data['coordinates']
                city_id = cached_data.get('city_id', None)
        
                # Check if the country is in Europe
                if country in european_countries:
                    europe_location = cached_data
                
                # Check if the country is in Americas or Oceania
                if country in americas_or_oceania_countries:
                    america_oceania_location = cached_data
                
                # If country is not in Europe or Americas/Oceania, consider it as another option
                if country not in americas_or_oceania_countries and country not in european_countries:
                    other_location = cached_data
        
            # Check the discovery year for countries in the Americas or Oceania
            if america_oceania_location:
                discovery_year = year_discovery.get(america_oceania_location['country'], None)
                
                # If the author died before the discovery year, prioritize Europe
                if discovery_year and row['year_map'] < discovery_year:
                    if europe_location:
                        cached_data = europe_location
                    elif other_location:
                        cached_data = other_location
                    else:
                        cached_data = america_oceania_location
                else:
                    # If the author died after the discovery year, use the first result 
                    cached_data = cached_results[0]

            
            # Add the cached data to the authors dataframe
            author_data.at[author, f'{city_col}_coordinates'] = cached_data['coordinates']
            author_data.at[author, f'{city_col}_country'] = cached_data['country']
            author_data.at[author, f'{city_col}_id'] = cached_data.get('city_id', None)
            set_flag(city_col, author, cached_data['country'], row)
  
# Apply mapping to all city columns (borncity, deathcity, activecity)
city_columns = ['borncity', 'deathcity', 'activecity']
for city_col in city_columns:
    author_data = map_coordinates(author_data, city_col)

# Reorder the columns, placing city_id before coordinates
cols = ['born_cityid', 'borncity_coordinates', 'borncity_country', 'borncity_americas_or_oceania_before_discovery', 
        'death_cityid', 'deathcity_coordinates', 'deathcity_country', 'deathcity_americas_or_oceania_before_discovery', 
        'active_cityid', 'activecity_coordinates', 'activecity_country', 'activecity_americas_or_oceania_before_discovery']

# Reorder DataFrame columns
author_data = author_data[['indexauthor', 'starturl', 'birthyear', 'deathyear', 'nameandbirthdeathyear', 
                               'georeferenceurl', 'borncity', 'deathcity', 'activecity'] + cols]

# Save the DataFrame with the geocoded results
output_file_csv = 'path/to/your/output_file.csv'  # Save CSV
output_file_excel = 'path/to/your/output_file.xlsx'  # Save Excel

geocoded_data.to_csv(output_file_csv, index=False)
geocoded_data.to_excel(output_file_excel, index=False)

print("Geocoding completed and files saved.")




# # Function to save cache incrementally
# def save_cache():
#     """
#     Saves the current state of the geocoded data cache incrementally to a CSV file.
#     The cache stores previously geocoded city data (city name, coordinates, and country).
#     """
#     cache_df = pd.DataFrame.from_dict(geocode_cache, orient='index')
#     cache_df.reset_index(inplace=True)
#     cache_df.columns = ['city', 'coordinates', 'country', 'country_code']
#     cache_df.to_csv(cache_file, index=False)

# # List of country codes for Americas and Oceania
# americas_oceania_countries = [
#     'US', 'CA', 'MX', 'GT', 'BZ', 'SV', 'HN', 'NI', 'CR', 'PA',  # North America & Central America
#     'CO', 'VE', 'GY', 'SR', 'BR', 'PE', 'BO', 'CL', 'AR', 'UY', 'PY', 'EC',  # South America
#     'CU', 'HT', 'DO', 'JM', 'BS', 'TT', 'BB', 'AG', 'DM', 'GD', 'LC', 'VC', 'KN',  # Caribbean
#     'AU', 'NZ', 'FJ', 'PG', 'SB', 'VU', 'WS', 'TO', 'KI', 'TV', 'NR', 'PW', 'FM', 'MH'  # Oceania
# ]

# # List of country codes for Europe
# european_countries = [
#     'AL', 'AD', 'AM', 'AT', 'BY', 'BE', 'BA', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'GE',
#     'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'KZ', 'XK', 'LV', 'LI', 'LT', 'LU', 'MT', 'MD', 'MC', 'ME',
#     'NL', 'MK', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB'
# ]

# # Function to geocode with Europe constraint for cities before 1500
# def geocode_city(city_name, year):
#     """
#     Geocodes a city name using the Google Maps API, prioritizing locations in Europe if the year is <= 1500.
    
#     Args:
#         city_name (str): The name of the city to geocode.
#         year (int): The year of relevance (e.g., birth year or death year).
    
#     Returns:
#         tuple: Contains the city name, coordinates (latitude, longitude), country name, and country code.
#     """
#     time.sleep(1)  # Rate limiting
    
#     # Geocode the city
#     geocode_result = gmaps.geocode(city_name)
    
#     if geocode_result:
#         europe_location = None
#         country_name = None
#         country_code = None # Get country code for more precise identification

#         for result in geocode_result:
#             address_components = result['address_components']
#             for component in address_components:
#                 # Extract the country name and country code from the address components
#                 if 'country' in component['types']:
#                     country_name = component['long_name']
#                     country_code = component['short_name']
                
#                 # Check if location is in Europe (using country codes for Europe)
#                 if country_code in european_countries:
#                     europe_location = result['geometry']['location']
#                     break  # Prioritize European location if found

#         # If European location is found and year <= 1500, use European location
#         if year <= 1500 and europe_location:
#             return city_name, (europe_location['lat'], europe_location['lng']), country_name, country_code
        
#         # Otherwise, use the first result
#         location = geocode_result[0]['geometry']['location']
#         return city_name, (location['lat'], location['lng']), country_name, country_code
    
#     # Return None if no result found
#     return city_name, (None, None), None, None

# # Step 1: Identify unique city names across columns for geocoding
# city_columns = ['borncity', 'deathcity', 'activecity']

# # Step 2: Create new columns to track incorrect geocodes in the Americas or Oceania before 1500 for each location type
# geocoded_data['borncity_americas_or_oceania_before_1500'] = ""
# geocoded_data['deathcity_americas_or_oceania_before_1500'] = ""
# geocoded_data['activecity_americas_or_oceania_before_1500'] = ""

# # Step 3: Go through each city in each column and build the geocoding cache
# for _, row in geocoded_data.iterrows():
#     for city_col, flag_col in [('borncity', 'borncity_americas_or_oceania_before_1500'), 
#                                ('deathcity', 'deathcity_americas_or_oceania_before_1500'), 
#                                ('activecity', 'activecity_americas_or_oceania_before_1500')]:
        
#         city = row[city_col]
#         # Prioritize deathyear, and if not available, use birthyear + 60 as an estimate
#         year = row['deathyear'] if pd.notna(row['deathyear']) else (row['birthyear'] + 60 if pd.notna(row['birthyear']) else None)
        
#         if pd.notna(city):  # If city is not missing
#             if city not in geocode_cache:
#                 # Geocode city with constraints if not cached
#                 city_name, coordinates, country, country_code = geocode_city(city, year)
#                 if coordinates != (None, None):  # Save successful geocoding
#                     geocode_cache[city] = {'coordinates': coordinates, 'country': country, 'country_code': country_code}
#                     save_cache()  # Save incrementally after each city
#                 else:
#                     # If geocoding failed, set placeholder value
#                     print(f"Geocoding failed for city: {city}")
#                     geocode_cache[city] = {'coordinates': (None, None), 'country': None, 'country_code': None}
            
#             # Now safely access the cached city data
#             cached_city = geocode_cache.get(city, {})
            
#             # Check if 'country_code' exists in the cache, if not skip or handle it
#             country_code = cached_city.get('country_code', None)
#             if country_code is None:
#                 print(f"Missing country code for city: {city}")
#                 continue  # Skip this city if country code is missing
            
#             # Check if the city is in Americas/Oceania and the year is before 1500
#             is_in_americas_or_oceania = country_code in americas_oceania_countries
#             before_1500 = year <= 1500 if year else False
            
#             # Set the flag dynamically
#             if before_1500 and is_in_americas_or_oceania:
#                 geocoded_data.at[_, flag_col] = "yes"
#             else:
#                 geocoded_data.at[_, flag_col] = "no"

# # Step 4: Map the geocoded coordinates and country back to the DataFrame
# def map_coordinates(df, city_col):
#     """
#     Maps the geocoded coordinates and country information back to the DataFrame 
#     based on previously cached geocode results.
    
#     Args:
#         df (pd.DataFrame): The DataFrame containing the city data.
#         city_col (str): The column name for the city (e.g., 'borncity', 'deathcity', or 'activecity').
    
#     Returns:
#         pd.DataFrame: Updated DataFrame with the coordinates and country mapped.
#     """
   
#     df[f'{city_col}_coordinates'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('coordinates', ""))
#     df[f'{city_col}_country'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('country', ""))
    
#     return df

# # Apply mapping to all city columns (borncity, deathcity, activecity)
# for city_col in city_columns:
#     geocoded_data = map_coordinates(geocoded_data, city_col)

# # Step 5: Reorder the columns to place americas_or_oceania_before_1500 after the country columns
# cols = ['borncity_coordinates', 'borncity_country', 'borncity_americas_or_oceania_before_1500', 
#         'deathcity_coordinates', 'deathcity_country', 'deathcity_americas_or_oceania_before_1500', 
#         'activecity_coordinates', 'activecity_country', 'activecity_americas_or_oceania_before_1500']

# # Reorder DataFrame columns
# geocoded_data = geocoded_data[['indexauthor', 'starturl', 'birthyear', 'deathyear', 'nameandbirthdeathyear', 
#                                'georeferenceurl', 'borncity', 'deathcity', 'activecity'] + cols]


# # Step 4: Save the DataFrame with the geocoded results
# output_file_csv = 'path/to/your/output_file.csv'  # Save CSV
# output_file_excel = 'path/to/your/output_file.xlsx'  # Save Excel

# geocoded_data.to_csv(output_file_csv, index=False)
# geocoded_data.to_excel(output_file_excel, index=False)

# print("Geocoding completed and files saved.")