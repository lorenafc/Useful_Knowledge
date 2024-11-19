# -*- coding: utf-8 -*-

"""
Created on Wed Oct 19/11/2024

@author: Lorena Carpes
"""

import pandas as pd
import os
import time
import googlemaps
import json

def load_author_data(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path, dtype={2: str, 6: str}, low_memory=False)

def correct_column_name(df: pd.DataFrame, old_name: str, new_name: str) -> pd.DataFrame:
    if old_name in df.columns:
        df.rename(columns={old_name: new_name}, inplace=True)
    return df

def load_geocode_cache(cache_file: str):
    if os.path.exists(cache_file):
        geocode_cache_df = pd.read_csv(cache_file)
        
        # Drop duplicates
        geocode_cache_df.drop_duplicates(subset=['city', 'coordinates', 'country', 'city_id'], inplace=True)      
        geocode_cache = geocode_cache_df.set_index('city').to_dict(orient='index')
        
        # Determine the next unique city_id
        max_id_in_cache = geocode_cache_df['city_id'].max()
        unique_id = max_id_in_cache
    else:
        # Initialize an empty cache and unique ID if no cache file exists
        geocode_cache = {}
        unique_id = 0

    return geocode_cache, unique_id

def save_cache() -> None: #source - Lucas Koren
    cache_df = pd.DataFrame.from_dict(geocode_cache, orient='index')
    cache_df.reset_index(inplace=True)
    cache_df.columns = ['city', 'coordinates', 'country', 'city_id']

    # Check if the cache file exists
    if os.path.exists(cache_file):
        existing_df = pd.read_csv(cache_file)
        # existing_df = pd.read_csv(cache_file, on_bad_lines='skip')

        # Find new entries that are not already in the file (based on all 4 columns)
        merged_df = pd.merge(cache_df,existing_df, on=['city', 'coordinates', 'country', 'city_id'],how='left', indicator=True)
        new_entries = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

        # Append only new entries to the file
        if not new_entries.empty:
            new_entries.drop_duplicates(subset=['city', 'coordinates', 'country', 'city_id'], inplace=True) ### being redundant to avoid repeated values
            new_entries.to_csv(cache_file, mode='a', index=False, header=False, encoding='utf-8')
    else:
        # If the file does not exist, write the entire DataFrame as the initial cache
        cache_df.to_csv(cache_file, index=False, encoding='utf-8')
            
def load_or_initialize_cities_dict(filename: str) -> None:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        return {}  # Start with an empty dictionary if file does not exist

def save_cities_dict_to_json(cities_dict: dict, filename=str) -> None:
    with open(filename, 'w') as f:
        json.dump(cities_dict, f)
    print(f"Added {city_name} to {filename}")
    print(f"The file has been saved to: {os.path.abspath(filename)}")

def save_city_data_and_assign_city_id_column(city_col: str, author, cache_key, coordinates, country, unique_id: int) -> None:
    """
    Saves city data in the geocode cache, assigns city_id to respective columns, and updates the cache.
    
    Args:
        city_col (str): The column representing the type of city ('borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        cache_key (str): The key to cache the city name.
        coordinates (str): The geocoded coordinates of the city.
        country (str): The country where the city is located.
        unique_id (int): The unique city_id to be assigned.
    """
    geocode_cache[cache_key] = {'coordinates': coordinates, 'country': country, 'city_id': unique_id}
    if city_col == 'borncity':
        author_data.at[author, 'borncity_city_id'] = unique_id
    elif city_col == 'deathcity':
        author_data.at[author, 'deathcity_city_id'] = unique_id
    elif city_col == 'activecity':
        author_data.at[author, 'activecity_city_id'] = unique_id
    save_cache()
        
def set_flag(city_col, author, country, row) -> None:
    """
    Sets the flag 'yes' or 'no' in the column {city_col}_americas_or_oceania_before_discovery
    based on the country's location and its year of discovery.

    Args:
        city_col (str): The column representing the type of city ('borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        country (str): The country where the city is located.
        row (pandas.Series): The row of the DataFrame corresponding to the current author being processed.

    Returns:
        None
    """
    # Check if country is valid (not NaN)
    if isinstance(country, str):
        is_in_americas_or_oceania = country in americas_or_oceania_countries 
    else:
        is_in_americas_or_oceania = False  # Treat NaN or non-string as not in Americas or Oceania - to avoid AttributeError: 'float' object has no attribute 'isin'

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
        author_data.at[author, f'{city_col}_americas_or_oceania_before_discovery'] = ""

def assign_unique_id(city_col, author, coordinates, id_cache) -> int:
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
         
def geocode_city(city_name, year):
     """
     Geocodes a city using the Google Maps API.
     
     Args:
         city_name (str): The name of the city to geocode.
         year (int): The year for historical context (not used directly in this function).
     
     Returns:
         tuple: The city name, latitude, longitude, and country code.
     """
     time.sleep(0.04)  # To avoid hitting API limits
     
     try: # to avoid HTTPError 400 - Bad request
     
         geocode_result = gmaps.geocode(city_name)
         
         # Check if there are no geocoding results
         if len(geocode_result) == 0:
            print(f"(Not geocoded) City {city_name} could not be geocoded. No coordinates were returned.")
            
            # attempt 1 -  empty cache, just column names and comas in the fist row. when run the code again, Rio Tinto shows up.

            # geocode_cache[city_name] = {'coordinates': None, 'country': None, 'city_id': None} # ADDING THE CITIES NOT GEOCODED IN CACHE TOO
            # save_cache()  # Save the cache immediately after adding an unsuccessful attempt # ADDING THE CITIES NOT GEOCODED IN CACHE TOO
            # return city_name, None, None, None
        
            # attempt 2 - shows in the cache only the comas of the first row and id 1. 
        
            # coordinates = None
            # country_name = None            
            # unique_id = assign_unique_id(city_col, author, coordinates, id_cache)
            # save_city_data_and_assign_city_id_column(city_col, author, cache_key, coordinates, country_name, unique_id)
            # return city_name, None, None, None           
          
            # return None
         
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
                  
                  ###############################
                  ##########
                  set_flag(city_col, author, country_name, row)
                  
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
     except Exception as e:
         print(f"Error geocoding {city_name}: {e}")
         return None  # Skip to next city if an error occurs



# Define a function to map coordinates, country, and city_id to the author_data
def map_coordinates(df, city_col) -> pd.DataFrame:
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

def add_columns_to_author_data(df) -> pd.DataFrame:
    columns_to_add = [
        'year_map',
        'borncity_coordinates',
        'deathcity_coordinates',
        'activecity_coordinates',
        'borncity_country',
        'deathcity_country',
        'activecity_country',
        'borncity_americas_or_oceania_before_discovery',
        'deathcity_americas_or_oceania_before_discovery',
        'activecity_americas_or_oceania_before_discovery',
        'borncity_city_id',
        'deathcity_city_id',
        'activecity_city_id'
    ]
    
    for col in columns_to_add:
        df[col] = ""
    
    return df

def ensure_utf8_encoding(column):
    def convert_to_utf8(value):
        if isinstance(value, str):
            return str(value).encode('utf-8').decode('utf-8')
        return value
    
    return column.apply(convert_to_utf8)

def reorder_author_data_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        'borncity_city_id', 'borncity', 'borncity_country', 'borncity_coordinates',
        'borncity_americas_or_oceania_before_discovery', 'deathcity_city_id', "deathcity",
        'deathcity_country', 'deathcity_coordinates', 'deathcity_americas_or_oceania_before_discovery',
        'activecity_city_id', "activecity", 'activecity_country', 'activecity_coordinates',
        'activecity_americas_or_oceania_before_discovery'
    ]
    
    new_order_cols = [
        'indexauthor', 'starturl', 'birthyear', 'deathyear', "year_map",
        'nameandbirthdeathyear', 'georeferenceurl'
    ] + cols
    
    return df[new_order_cols]

def replace_empty_NA(column: pd.Series) -> pd.Series:
    """
    Strips spaces from strings in a column, replaces empty strings with pandas NA.

    Args:
        column (pd.Series): A pandas Series to clean.

    Returns:
        pd.Series: Cleaned pandas Series with stripped strings and missing values handled as pandas.NA.
    """
    def strip_spaces(value):
        if isinstance(value, str):
            return value.strip()
        return value

    return column.apply(strip_spaces).replace('', pd.NA)


def filter_flag_and_not_geocoded_authors(author_data, csv_path_cleaned, excel_path_cleaned, csv_path_bad, excel_path_bad):
    """
    Filters out rows with a 'yes' flag for locations in the Americas or Oceania before discovery
    and rows with cities that are not geocoded, then saves the results to both CSV and Excel formats.

    Parameters:
    - author_data (pd.DataFrame): The input DataFrame containing author data.
    - csv_path_cleaned (str): File path for saving CSV output of cleaned data.
    - excel_path_cleaned (str): File path for saving Excel output of cleaned data.
    - csv_path_bad (str): File path for saving CSV output of bad results.
    - excel_path_bad (str): File path for saving Excel output of bad results.
    
    Returns:
    - tuple of pd.DataFrame: DataFrames with cleaned data and bad results.
    """   
    author_data["borncity"] = replace_empty_NA(author_data["borncity"])
    author_data["deathcity"] = replace_empty_NA(author_data["deathcity"])
    author_data["activecity"] = replace_empty_NA(author_data["activecity"])
    
    # Create a boolean mask to identify rows with a 'yes' flag
    yes_flag = (
        (author_data["borncity_americas_or_oceania_before_discovery"] == "yes") |
        (author_data["deathcity_americas_or_oceania_before_discovery"] == "yes") |
        (author_data["activecity_americas_or_oceania_before_discovery"] == "yes")
    )    

    # Create a boolean mask for rows with missing coordinates in born, death, or active cities
    not_geocoded = (
        ((author_data["borncity"].notnull()) & (author_data["borncity_coordinates"].isnull())) |
        ((author_data["deathcity"].notna()) & (author_data["deathcity_coordinates"].isna())) |
        ((author_data["activecity"].notna()) & (author_data["activecity_coordinates"].isna()))
    )

    # Combine both conditions to filter out rows flagged with 'yes' or missing coordinates
    bad_results = yes_flag | not_geocoded

    # DataFrames for cleaned data and bad results
    authors_cleaned = author_data.loc[~bad_results]
    authors_bad_results = author_data.loc[bad_results]

    # Save the cleaned and bad results data to separate CSV and Excel files
    authors_cleaned.to_csv(csv_path_cleaned, index=False)
    authors_cleaned.to_excel(excel_path_cleaned, index=False)
    
    authors_bad_results.to_csv(csv_path_bad, index=False)
    authors_bad_results.to_excel(excel_path_bad, index=False)

    print(f"Number of rows in cleaned data: {authors_cleaned.shape[0]}")
    print(f"Number of rows in bad results: {authors_bad_results.shape[0]}")
    
    return authors_cleaned, authors_bad_results


    