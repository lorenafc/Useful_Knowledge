# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 12:15:05 2024

@author: Lorena Carpes
"""
# ChatGPT 4.0 used for debbuging and enhancing the code

import pandas as pd
import googlemaps
import time
import os
import json

# Initialize Google Maps Client
API_KEY = "YOUR_GOOGLE_API_KEY"
gmaps = googlemaps.Client(key=API_KEY)

#Load your data
file_path = 'path/to/your/input_file.csv' 
author_data = pd.read_excel(file_path)

cache_file = 'path/to/your/geocode_cache.csv'
dict_file =  './path/to/your/cities_dict.json'

output_file_csv = 'path/to/your/output_file.csv'  # Save CSV
output_file_excel = 'path/to/your/output_file.xlsx'  # Save Excel

# Check for existing geocoded cache file
if os.path.exists(cache_file):
    geocode_cache = pd.read_csv(cache_file).set_index('city').to_dict(orient='index')
else:
    geocode_cache = {}
      
def save_cache(): #source - Lucas Koren
    """
    Saves the current geocode cache to a CSV file incrementally.
    Only appends new entries to the file to avoid complete overwriting.
    """
    # Convert the cache to a DataFrame
    cache_df = pd.DataFrame.from_dict(geocode_cache, orient='index')
    cache_df.reset_index(inplace=True)
    cache_df.columns = ['city', 'coordinates', 'country', 'city_id']

    # Check if the cache file exists
    if os.path.exists(cache_file):
        # Load existing data
        existing_df = pd.read_csv(cache_file)
        # existing_df = pd.read_csv(cache_file, on_bad_lines='skip')

        # Find new entries that are not already in the file (based on all columns)
        merged_df = pd.merge(cache_df,existing_df, on=['city', 'coordinates', 'country', 'city_id'],how='left', indicator=True)
        new_entries = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

        # Append only new entries to the file
        if not new_entries.empty:
            new_entries.to_csv(cache_file, mode='a', index=False, header=False, encoding='utf-8')
    else:
        # If the file does not exist, write the entire DataFrame as the initial cache
        cache_df.to_csv(cache_file, index=False, encoding='utf-8')
      
# Initialize or load the cities dictionary
def load_or_initialize_cities_dict(filename=dict_file):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        return {}  # Start with an empty dictionary if file does not exist

cities_dict = load_or_initialize_cities_dict()

# Function to save the cities dictionary incrementally
def save_cities_dict_to_json(cities_dict, filename=dict_file) -> None:
    """
    Saves the current cities dictionary to a JSON file.
    
    Args:
        cities_dict (dict): Dictionary with city data.
    Returns:
        None
    """
    with open(filename, 'w') as f:
        json.dump(cities_dict, f)
    print(f"Added {city_name} to {filename}")
    print(f"The file has been saved to: {os.path.abspath(filename)}")


cities_dict = load_or_initialize_cities_dict()    

americas_or_oceania_countries = [
    # North America & Central America
    'Belize', 'Canada', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras', 'Mexico', 
    'Nicaragua', 'Panama', 'United States',
    
    # South America
    'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'French Guiana', 
    'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay', 'Venezuela',
    
    # Caribbean
    'Antigua and Barbuda', 'Anguilla', 'Bahamas', 'Barbados', 'Bermuda', 'British Virgin Islands', 
    'Cayman Islands', 'Cuba', 'Dominica', 'Dominican Republic', 'Grenada', 'Haiti', 
    'Jamaica', 'Montserrat', 'Saint Kitts and Nevis', 'Saint Lucia', 
    'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'Turks and Caicos Islands', 
    'US Virgin Islands',
    
    # Oceania
    'Australia', 'Fiji', 'Kiribati', 'Marshall Islands', 'Micronesia', 'Nauru', 
    'New Zealand', 'Palau', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 
    'Tonga', 'Tuvalu', 'Vanuatu'
]

# Europe countries
european_countries = [
    'Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Cyprus', 
    'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 
    'Italy', 'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro',
    'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 
    'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom'
]

year_discovery = {
    # North America & Central America
    'Belize': 1502, 'Canada': 1497, 'Costa Rica': 1502, 'Guatemala': 1523, 'Honduras': 1502, 'Mexico': 1519, 
    'Nicaragua': 1524, 'Panama': 1501, 'El Salvador': 1524, 'United States': 1492,  
    
    # South America
    'Argentina': 1516, 'Bolivia': 1535, 'Brazil': 1500, 'Chile': 1520, 'Colombia': 1499, 'Ecuador': 1531, 
    'Guyana': 1498, 'Peru': 1526, 'Paraguay': 1537, 'Suriname': 1593, 'Uruguay': 1516, 'Venezuela': 1498,  
    
    # Caribbean
    'Antigua and Barbuda': 1493, 'Barbados': 1492, 'Bahamas': 1492, 'Cuba': 1492, 'Dominica': 1493, 
    'Dominican Republic': 1492, 'Grenada': 1498, 'Haiti': 1492, 'Jamaica': 1494, 'Saint Kitts and Nevis': 1493, 
    'Saint Lucia': 1502, 'Trinidad and Tobago': 1498, 'Saint Vincent and the Grenadines': 1498,  
    
    # Oceania
    'Australia': 1606, 'Micronesia': 1529, 'Fiji': 1643, 'Kiribati': 1528, 'Marshall Islands': 1529, 
    'Nauru': 1798, 'New Zealand': 1642, 'Palau': 1543, 'Papua New Guinea': 1526, 'Solomon Islands': 1568, 
    'Tonga': 1616, 'Tuvalu': 1568, 'Vanuatu': 1606, 'Samoa': 1722
}

year_discovery = {
    # North America & Central America
    'Belize': 1502, 'Canada': 1497, 'Costa Rica': 1502, 'El Salvador': 1524, 'Guatemala': 1524, 'Honduras': 1502, 'Mexico': 1519, 
    'Nicaragua': 1502, 'Panama': 1501, 'United States': 1492,  
    
    # South America
    'Argentina': 1502, 'Bolivia': 1535, 'Brazil': 1500, 'Chile': 1520, 'Colombia': 1499, 'Ecuador': 1526, 'French Guiana' : 1498, 
    'Guyana': 1498, 'Paraguay': 1524, 'Peru': 1524, 'Suriname': 1593, 'Uruguay': 1516, 'Venezuela': 1498,  
    
    # Caribbean     
    'Antigua and Barbuda': 1493, 'Anguilla': 1493, 'Bahamas': 1492, 'Barbados': 1492,
    'Bermuda': 1505, 'Cayman Islands': 1503,'Cuba': 1492,'Dominica': 1493, 'Dominican Republic': 1492,
    'Grenada': 1498, 'Haiti': 1492,'Jamaica': 1494,'Montserrat': 1493, 'Saint Kitts and Nevis': 1493,
    'Saint Lucia': 1502, 'Saint Vincent and the Grenadines': 1498,'Trinidad and Tobago': 1498,
    'Turks and Caicos Islands': 1492, 'British Virgin Islands': 1493, 'US Virgin Islands': 1493,
       
    # Oceania
    'Australia': 1606,  'Fiji': 1643, 'Kiribati': 1606, 'Marshall Islands': 1526, 'Micronesia': 1521,
    'Nauru': 1798, 'New Zealand': 1642, 'Palau': 1696, 'Papua New Guinea': 1526, 'Solomon Islands': 1568, 
    'Tonga': 1616, 'Tuvalu': 1568, 'Vanuatu': 1606, 'Samoa': 1722
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
author_data['borncity_city_id'] = ""
author_data['deathcity_city_id'] = ""
author_data['activecity_city_id'] = ""

# UTF-8 encoding for city columns 
author_data['borncity'] = author_data['borncity'].apply(lambda x: str(x).encode('utf-8').decode('utf-8') if isinstance(x, str) else x)
author_data['deathcity'] = author_data['deathcity'].apply(lambda x: str(x).encode('utf-8').decode('utf-8') if isinstance(x, str) else x)
author_data['activecity'] = author_data['activecity'].apply(lambda x: str(x).encode('utf-8').decode('utf-8') if isinstance(x, str) else x)

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
        author_data.at[author, 'borncity_city_id'] = unique_id
    elif city_col == 'deathcity':
        author_data.at[author, 'deathcity_city_id'] = unique_id
    elif city_col == 'activecity':
        author_data.at[author, 'activecity_city_id'] = unique_id
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
def assign_unique_id(city_col, author, coordinates, id_cache):
    """
    Assigns a unique ID to a city based on its coordinates. If the coordinates are already in the cache, 
    the cached ID is assigned, otherwise a new ID is generated.
    
    Args:
        city_col (str): The column representing the type of city (e.g., 'borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        coordinates (str): The geocoded coordinates of the city.
        id_cache (dict): Cache mapping coordinates to unique IDs.
    
    Returns:
        unique_id (int): The assigned or cached unique ID.
    """
    global unique_id  # Access the global unique ID counter

    if coordinates not in id_cache:
        id_cache[coordinates] = unique_id
        author_data.at[author, f'{city_col}_city_id'] = unique_id
        unique_id += 1  # Increment the ID counter for the next city
    else:
        author_data.at[author, f'{city_col}_city_id'] = id_cache[coordinates]

    return unique_id  # Return the unique_id (either new or cached)
         
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
     time.sleep(0.03)  # To avoid hitting API limits
     
     geocode_result = gmaps.geocode(city_name)
     
     # Check if there are no geocoding results
     if len(geocode_result) == 0:
        print(f"(Not geocoded) City {city_name} could not be geocoded. No coordinates were returned.")
        #return city_name, None, None, None
        return None
     
     # Initialize variables before condition checks
     europe_location = None
     america_oceania_location = None
     
     #If there is only one result for the city:
     if len(geocode_result) == 1:
         
         location = geocode_result[0]['geometry']['location']
         country_name = None
         for component in geocode_result[0]['address_components']:
            if "country" in component['types']:
                country_name = component['long_name']  # long_name for full country name
                break
         coordinates = f"{location['lat']}, {location['lng']}"
         
         coordinates = f"{location['lat']}, {location['lng']}"
         
         # Generate a unique city_id based on coordinates and assign it
         unique_id = assign_unique_id(city_col, author, coordinates, id_cache)
         
         # Save the city and set the flag based on the discovery year
         print(f"(Geocoded) Saving city {city_name} to cache. It has only 1 geocoding result. Coordinates: {coordinates}, country: {country_name}, city_id: {unique_id}")
         save_city_data_and_assign_city_id_column(city_col, author, cache_key, coordinates, country_name, unique_id)
         set_flag(city_col, author, country_name, row)
                          
        # Check if city_name is already in cities_dict before adding
         if city_name not in cities_dict:
             
            # Add the city to the dictionary           
            cities_dict[city_name] = {
                "coordinates": [coordinates],
                "country": [country_name],
                "city_id": [unique_id]
            }
        
            # Save the updated dictionary to the JSON file
            save_cities_dict_to_json(cities_dict)
            print(f"Added {city_name} with ID {unique_id} to the dictionary.")
         else:
            print(f"{city_name} already exists in the dictionary. Skipping addition.")
       
         return city_name, location['lat'], location['lng'], country_name
     
     #If there are multiple results for the city name
     elif len(geocode_result) > 1:
         europe_location = None
         americas_oceania_location = None
         
         if city_name not in cities_dict:
             cities_dict[city_name] = []
           
        #Loop through the results to check country codes     
         for i, result in enumerate(geocode_result):
              location = result['geometry']['location']
              country_name = None
              for component in geocode_result[0]['address_components']:
                 if "country" in component['types']:
                     country_name = component['long_name']  # long_name for full country name
                     break
              coordinates = f"{location['lat']}, {location['lng']}"
     
               # Print debugging information
              print(f"(Geocoded) Multiple geocoding results for {city_name}, result {i+1}: Coordinates: {coordinates}, Country: {country_name}")
         
               # Create a unique cache key for each location
              unique_cache_key = f"{city_name}_{coordinates}"
     
               # Assign a unique ID for each result
              unique_id = assign_unique_id(city_col, author, coordinates, id_cache)
         
              # Store each result in the cache with a unique city_id
              print(f"Saving city {city_name} with more than 1 result to cache with coordinates: {coordinates}, country: {country_name}, city_id: {unique_id}")
              save_city_data_and_assign_city_id_column(city_col, author, unique_cache_key, coordinates, country_name, unique_id)
              
              # Add each location to the list under the city_name key in cities_dict
              if coordinates not in cities_dict:   
                  
                  cities_dict[city_name].append({
                      "coordinates": [coordinates],
                      "country": [country_name],
                      "city_id": [unique_id]
                  })
                                               
              # Save the updated dictionary to the JSON file
                  save_cities_dict_to_json(cities_dict)
                  print(f"Added {city_name} with ID {unique_id} to the dictionary.")
              else:
                    print(f"{city_name} already exists in the dictionary. Skipping addition.")
      
             
             #Check if the country is in Europe
              if country_name in european_countries:
                  europe_location = (city_name, location["lat"], location["lng"], country_name)
                 
              #Check if the country is in Americas or Oceania
              if country_name in americas_or_oceania_countries:
                  america_oceania_location = (city_name, location['lat'], location['lng'], country_name)
         
         # Check the discovery year for countries in the Americas or Oceania
         if america_oceania_location:
             country_name = america_oceania_location[3]
             discovery_year = year_discovery.get(country_name, None)
             
             #If the author died before the discovery year, prioritize Europe
             if discovery_year and year < discovery_year:
                 if europe_location:
                     
                     unique_id = assign_unique_id(city_col, author, f"{europe_location[1]}, {europe_location[2]}", id_cache)
                     print(f"(Geocoded) Saving city {city_name} to cache. It has more than 1 result for this name. Geocoded in Europe with coordinates: {coordinates}, country: {country_name}, city_id: {unique_id}")
                     save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{europe_location[1]}, {europe_location[2]}", europe_location[3], unique_id)
                     set_flag(city_col, author, europe_location[3], row)
                     
                                        
                     return europe_location
                 
                 else:
                     #If no European location, prioritize any other non-Americas/Oceania location
                     other_location = None
                     
                     for result in geocode_result:
                         location = result["geometry"]["location"]
                         country_name = None
                         for component in geocode_result[0]['address_components']:
                            if "country" in component['types']:
                                country_name = component['long_name']  # long_name for full country name
                                break
                                             
                         #Prioritize non-Americas/Oceania countries first
                         if country_name not in americas_or_oceania_countries and country_name not in european_countries:
                             other_location = (city_name, location["lat"], location["lng"], country_name)
                             break
                         
                     # If there is another location outuside Americas/Oceania, use it 
                     if other_location:
                         
                         unique_id = assign_unique_id(city_col, author, f"{other_location[1]}, {other_location[2]}", id_cache)
                         print(f" (Geocoded) Saving city {city_name} to cache.  It has more than 1 result for this name. Geocoded outside Europe and Americas/Oceania with coordinates: {coordinates}, country: {country_name}, city_id: {unique_id}")
                         save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{other_location[1]}, {other_location[2]}", other_location[3], unique_id)
                         set_flag(city_col, author, other_location[3], row)                       
                                                  
                         return other_location
                             
                     # If no other location is found, use Americas/Oceania location
                     if america_oceania_location:
                         
                         unique_id = assign_unique_id(city_col, author, f"{america_oceania_location[1]}, {america_oceania_location[2]}", id_cache)
                         print(f" (Geocoded) Saving city {city_name} with more than 1 result in Americas/Oceania (no option in Europe or other location) to cache with coordinates: {coordinates}, country: {country_name}, city_id: {unique_id}")
                         save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{america_oceania_location[1]}, {america_oceania_location[2]}", america_oceania_location[3], unique_id)
                         set_flag(city_col, author, america_oceania_location[3], row)
                                                  
                         return america_oceania_location
                     
            # If the year is greater than or equal to the discovery year, use the first geocoded result
             elif discovery_year and year >= discovery_year:
               first_result = geocode_result[0]
               location = first_result["geometry"]["location"]
               country_name = None
               for component in first_result['address_components']:
                   if "country" in component['types']:
                       country_name = component['long_name']
                       break
       
               unique_id = assign_unique_id(city_col, author, f"{location['lat']}, {location['lng']}", id_cache)
               print(f"(Geocoded) Using first geocoded result for {city_name} with multiple results as year >= discovery year. Coordinates: {location['lat']}, {location['lng']}, country: {country_name}, city_id: {unique_id}")
               save_city_data_and_assign_city_id_column(city_col, author, cache_key, f"{location['lat']}, {location['lng']}", country_name, unique_id)
               set_flag(city_col, author, country_name, row)
       
               return city_name, location["lat"], location["lng"], country_name   

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
    df[f'{city_col}_city_id'] = df[city_col].map(lambda city: geocode_cache.get(city, {}).get('city_id', ""))
    return df

# Process rows for year_map. For each row, if the death year is not empty, add it to the "year_map" column, if it is empty, add the "birth_year"+ 60
for author, row in author_data.iterrows():
    if pd.notna(row['deathyear']):
        author_data.at[author, "year_map"] = int(row['deathyear'])
    else:
        author_data.at[author, "year_map"] = int(row['birthyear']) + 60
author_data['year_map'] = pd.to_numeric(author_data['year_map'], errors='coerce')

# Initialize a counter for unique IDs
unique_id = 0
id_cache = {}

geocode_limit = 20  
geocode_count = 0
geocode_limit_reached = False

# In each row, go through each city in each column (born, death and active). If empty return None
for author, row in author_data.iterrows():
          
       ######## GEOCODE LIMIT TO TEST THE CODE #####

    if geocode_limit_reached: 
        break  # Exit the outer loop if the limit is reached
    
    for city_col in ['borncity', 'deathcity', 'activecity']:
        city_name = row[city_col]
        
        # Skip processing if the city name is empty or NaN
        if not city_name or pd.isna(city_name):
            continue
        
        # Check if the geocode limit was reached
        if geocode_count >= geocode_limit:
            print(f"Geocode limit of {geocode_limit} reached. Stopping geocoding.")
            geocode_limit_reached = True  
            break
        
        geocode_count += 1
        
        ######## ENG GEOCODE LIMIT ######## 
                
        # Create a composite key for the cache using city_name
        cache_key = city_name
        
        # Check if the city is not in the cache
        if city_name not in geocode_cache:
                                   
            #geocode using GooGle Maps API
            print(f"Geocoding city: {city_name}")  # Add a print statement to see the cities being geocoded
                        
                        # Call geocode_city and check if it returns None
            result = geocode_city(city_name, row['year_map'])
            
            if result is not None:
                # Unpack result if it’s not None
                city_name, lat, lng, country_name = result
               
            else:
                print(f"Geocoding failed for {city_name}. No data was returned.")
                                           
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
                # city_id = cached_data.get['city_id']
        
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
                    print(f"(Cache) Using {city_name}. The Author died in {row['year_map']}, before discovery year {discovery_year} for country {america_oceania_location['country']}")
                    
                    if europe_location:
                        print(f" (Cache) Using {city_name} located in Europe with coordinates: {europe_location['coordinates']}")
                        cached_data = europe_location
                    elif other_location:
                        print(f"(Cache) Using {city_name} located outside Americas/Oceania with coordinates: {other_location['coordinates']}")
                        cached_data = other_location
                    else:
                        print(f"(Cache)  Using {city_name} located in Americas/Oceania with coordinates: {america_oceania_location['coordinates']}")
                        cached_data = america_oceania_location
                else:
                    # If the author died after the discovery year, use the first result
                    print(f" (Cache) Using first cached result for {city_name}. Author died in {row['year_map']}, after discovery year {discovery_year} of {country}. ")
                    cached_data = cached_results[0]
            
            # Add the cached data to the authors dataframe
            author_data.at[author, f'{city_col}_coordinates'] = cached_data['coordinates']
            author_data.at[author, f'{city_col}_country'] = cached_data['country']
            author_data.at[author, f'{city_col}_city_id'] = cached_data['city_id']
            # author_data.at[author, f'{city_col}_city_id'] = cached_data.get('city_id', None)
            set_flag(city_col, author, cached_data['country'], row)
            
# Apply mapping to all city columns (borncity, deathcity, activecity)
city_columns = ['borncity', 'deathcity', 'activecity']
for city_col in city_columns:
    author_data = map_coordinates(author_data, city_col)

# Reorder the columns, placing city_id before coordinates
cols = ['borncity_city_id','borncity', 'borncity_country', 'borncity_coordinates',  'borncity_americas_or_oceania_before_discovery',  'deathcity_city_id', "deathcity", 
       'deathcity_country', 'deathcity_coordinates', 'deathcity_americas_or_oceania_before_discovery', 'activecity_city_id', "activecity",
        'activecity_country', 'activecity_coordinates', 'activecity_americas_or_oceania_before_discovery']

# Reorder DataFrame columns
author_data = author_data[['indexauthor', 'starturl', 'birthyear', 'deathyear',"year_map", 'nameandbirthdeathyear', 
                               'georeferenceurl'] + cols]


author_data.to_csv(output_file_csv, index=False)
author_data.to_excel(output_file_excel, index=False)

print("Geocoding completed and files saved.")


# Remove from the df the authors who were wrongly geocoded and makes one spreadsheet of the results wrongly geocoded and one without it:
    
def filter_authors_without_yes_flag(author_data, csv_path_without_flag, excel_path_without_flag, csv_path_with_flag, excel_path_with_flag):
    """
    Filters out rows with a 'yes' flag for locations in the Americas or Oceania before discovery 
    and saves the result to both CSV and Excel formats.

    Parameters:
    - author_data (pd.DataFrame): The input DataFrame containing author data.
    - csv_path_without_flag (str): File path for saving CSV output of authors without 'yes' flags.
    - excel_path_without_flag (str): File path for saving Excel output of authors without 'yes' flags.
    - csv_path_with_flag (str): File path for saving CSV output of authors with 'yes' flags.
    - excel_path_with_flag (str): File path for saving Excel output of authors with 'yes' flags.
    
    Returns:
    - tuple of pd.DataFrame: DataFrames excluding rows with 'yes' flags and only rows with 'yes' flags.
    """
    # Create a boolean mask to identify rows to be excluded
    yes_flag = (
        (author_data["borncity_americas_or_oceania_before_discovery"] == "yes") |
        (author_data["deathcity_americas_or_oceania_before_discovery"] == "yes") |
        (author_data["activecity_americas_or_oceania_before_discovery"] == "yes")
    )

    # Filter the DataFrames for rows with and without the 'yes' flag
    authors_without_yes_flag = author_data.loc[~yes_flag]
    authors_yes_flag = author_data.loc[yes_flag]

    # Save the filtered results to separate CSV and Excel files
    authors_without_yes_flag.to_csv(csv_path_without_flag, index=False)
    authors_without_yes_flag.to_excel(excel_path_without_flag, index=False)
    
    authors_yes_flag.to_csv(csv_path_with_flag, index=False)
    authors_yes_flag.to_excel(excel_path_with_flag, index=False)

    # Print the number of remaining rows
    print(f"Number of authors without 'yes' flag: {authors_without_yes_flag.shape[0]}")
    print(f"Number of authors with 'yes' flag: {authors_yes_flag.shape[0]}")
    
    return authors_without_yes_flag, authors_yes_flag

# Remove from the df the authors with locations wrongly geocoded or not geocoded:

def filter_authors_with_flag_or_not_geocoded(author_data, csv_path_cleaned, excel_path_cleaned, csv_path_bad, excel_path_bad):
    """
    Filters out rows with a 'yes' flag for locations in the Americas or Oceania before discovery
    and rows with cities that are not geocoded, then saves the results to both CSV and Excel formats.

    Parameters:
    - author_data (pd.DataFrame): the dataframe with author data.
    - csv_path_cleaned (str): File path for saving CSV output of cleaned data.
    - excel_path_cleaned (str): File path for saving Excel output of cleaned data.
    - csv_path_bad (str): File path for saving CSV output of bad results.
    - excel_path_bad (str): File path for saving Excel output of bad results.
    
    Returns:
    - tuple of pd.dataframe: df with authors geocoded and authors flagged or not geocoded.
    """
    # Create a boolean mask to identify rows with a 'yes' flag
    yes_flag = (
        (author_data["borncity_americas_or_oceania_before_discovery"] == "yes") |
        (author_data["deathcity_americas_or_oceania_before_discovery"] == "yes") |
        (author_data["activecity_americas_or_oceania_before_discovery"] == "yes")
    )

    # Create a boolean mask for rows not geocoded in born, death, or active cities ( with missing coordinates)
    not_geocoded = (
        ((author_data["borncity"].notna()) & (author_data["borncity_coordinates"].isna())) |
        ((author_data["deathcity"].notna()) & (author_data["deathcity_coordinates"].isna())) |
        ((author_data["activecity"].notna()) & (author_data["activecity_coordinates"].isna()))
    )
    
    # Combine both conditions
    bad_results = yes_flag | not_geocoded

    # separate authors geocoded from the ones wrongly geocoded (flag "yes") or not geocoded (with missing coordinates)
    authors_cleaned = author_data.loc[~bad_results]
    authors_bad_results = author_data.loc[bad_results]

    authors_cleaned.to_csv(csv_path_cleaned, index=False)
    authors_cleaned.to_excel(excel_path_cleaned, index=False)
    
    authors_bad_results.to_csv(csv_path_bad, index=False)
    authors_bad_results.to_excel(excel_path_bad, index=False)

    print(f"Number of authors geocoded: {authors_cleaned.shape[0]}")
    print(f"Number of authors in flagged or not geocoded: {authors_bad_results.shape[0]}")
    
    return authors_cleaned, authors_bad_results
