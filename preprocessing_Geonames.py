# -*- coding: utf-8 -*-
"""
Created on 07/10/2024

@author: Lorena Carpes
"""


import pandas as pd 
import os



# Use the current working directory 
script_dir = os.getcwd()  # This gets the current working directory

# Change to the script's directory
os.chdir(script_dir)

# Load the GeoNames whitelist - https://public.opendatasoft.com/explore/dataset/geonames-all-cities-with-a-population-500/information/?disjunctive.country
whitelist_file_path = './path/to/file/geonames_all_cities_with_a_population_500_csv.csv' 

geonames_df = pd.read_csv(whitelist_file_path, delimiter=';')
whitelist_cities = geonames_df[["Geoname ID",'Name', "ASCII Name", 'Coordinates', 'Country', "Country Code", 'Population']]  # Keep relevant columns


file_path = './path/to/your/file.xlsx'
author_data = pd.read_excel(file_path)


# Check for existing geocoded cache file
cache_file =  './path/to/geocode_cache.csv'
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

# List of countries for the Americas and Oceania
americas_or_oceania_countries = [
    "Canada", "Mexico", "United States", "Belize", "Costa Rica", "El Salvador", "Guatemala",
    "Honduras", "Nicaragua", "Panama", "Antigua and Barbuda", "Bahamas", "Barbados", "Cuba", 
    "Dominica", "Dominican Republic", "Grenada", "Haiti", "Jamaica", "Saint Kitts and Nevis", 
    "Saint Lucia", "Saint Vincent and the Grenadines", "Trinidad and Tobago", "Argentina", 
    "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "Guyana", "Paraguay", "Peru", 
    "Suriname", "Uruguay", "Venezuela", "Australia", "Fiji", "Kiribati", "Marshall Islands", 
    "Micronesia", "Nauru", "New Zealand", "Palau", "Papua New Guinea", "Samoa", "Solomon Islands", 
    "Tonga", "Tuvalu", "Vanuatu"
]

# European countries list
european_countries = [
    'Albania', 'Andorra', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 'Bosnia and Herzegovina',
    'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France',
    'Georgia', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kazakhstan', 
    'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 
    'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 
    'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 
    'Switzerland', 'Turkey', 'Ukraine', 'United Kingdom', 'Vatican City'
]

# Add necessary columns
author_data['year_map'] = ""
author_data['borncity_coordinates'] = ""
author_data['deathcity_coordinates'] = ""
author_data['activecity_coordinates'] = ""
author_data['borncity_country'] = ""
author_data['deathcity_country'] = ""
author_data['activecity_country'] = ""
author_data['borncity_americas_or_oceania_before_1500'] = ""
author_data['deathcity_americas_or_oceania_before_1500'] = ""
author_data['activecity_americas_or_oceania_before_1500'] = ""
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

# Define a function to set the flag
def set_flag(city_col, author, country, row):
    """
    Sets the flag 'yes' or 'no' in the column {city_col}_americas_or_oceania_before_1500 
    based on the country's location and the year being before 1500.
    
    Args:
        city_col (str): The column representing the type of city (e.g., 'borncity', 'deathcity', 'activecity').
        author (int): The row index of the author in the dataset.
        country (str): The country where the city is located.
        row (pandas.Series): The row of the DataFrame corresponding to the current author being processed.
    
    Returns:
        None
    """
    is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()
    before_1500 = row['year_map'] < 1500
    if before_1500 and is_in_americas_or_oceania:
        author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "yes"
    else:
        author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "no"

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
            # Check if the city exists in the whitelist
            matching_rows = whitelist_cities.loc[(whitelist_cities["Name"] == city_name) | (whitelist_cities["ASCII Name"] == city_name)]
            
            # If there's more than one city with the same name, check if year < 1500
            if len(matching_rows) > 1:  
                if row['year_map'] < 1500:
           
                    
                    # Prioritize European locations if the year is before 1500
                    european_matches = matching_rows[matching_rows["Country"].isin(european_countries)]
                    
                    # If there is more than one city in Europe with the same name
                    if len(european_matches) > 0:
                        # Retrieve the city in Geonames with the largest population from European matches
                        matching_rows = european_matches.loc[european_matches['Population'].idxmax()]
                        
                     # If more than one city, and no one is in Europe, choose the one with biggest population   
                    else:
                         matching_rows = matching_rows.loc[matching_rows['Population'].idxmax()]
                        
                else:
                    # If year > = 1500, choose the row with the largest population
                    matching_rows = matching_rows.loc[matching_rows['Population'].idxmax()]
                    
                coordinates = matching_rows["Coordinates"]
                country = matching_rows["Country"]
                save_city_data_and_assign_city_id_column(city_col, author, cache_key, coordinates, country, unique_id)
                set_flag(city_col, author, country, row)
                unique_id = assign_unique_id(city_col, author, coordinates, id_cache, unique_id)
                
            else:
                # Retrieve cached coordinates, country and city_id
                cached_data = geocode_cache[cache_key]
                author_data.at[author, f'{city_col}_coordinates'] = cached_data['coordinates']
                author_data.at[author, f'{city_col}_country'] = cached_data['country']
                author_data.at[author, f'{city_col}_id'] = cached_data.get('city_id', None)
                set_flag(city_col, author, cached_data['country'], row)

# Apply mapping to all city columns (borncity, deathcity, activecity)
city_columns = ['borncity', 'deathcity', 'activecity']
for city_col in city_columns:
    author_data = map_coordinates(author_data, city_col)

# Reorder the columns, placing city_id before coordinates
cols = ['born_cityid', 'borncity_coordinates', 'borncity_country', 'borncity_americas_or_oceania_before_1500', 
        'death_cityid', 'deathcity_coordinates', 'deathcity_country', 'deathcity_americas_or_oceania_before_1500', 
        'active_cityid', 'activecity_coordinates', 'activecity_country', 'activecity_americas_or_oceania_before_1500']

# Reorder DataFrame columns
author_data = author_data[['indexauthor', 'starturl', 'birthyear', 'deathyear', 'nameandbirthdeathyear', 
                               'georeferenceurl', 'borncity', 'deathcity', 'activecity'] + cols]



print(author_data.head())



output_file_csv = './path/to/your/file.csv'
output_file_excel = './path/to/your/file.xlsx'

author_data.to_csv(output_file_csv, index=False)
author_data.to_excel(output_file_excel, index=False)




 
