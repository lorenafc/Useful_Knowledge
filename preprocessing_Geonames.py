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
    Saves the current state of the geocoded data cache incrementally to a CSV file.
    The cache stores previously geocoded city data (city name, coordinates, and country).
    """
    cache_df = pd.DataFrame.from_dict(geocode_cache, orient='index')
    cache_df.reset_index(inplace=True)
    cache_df.columns = ['city_id', "city", 'country', 'coordinates'] #columns storaged in the cache
    cache_df.to_csv(cache_file, index=False)


americas_or_oceania_countries = [
    # North America
    "Canada", "Mexico","United States", 
    
    # Central America
    "Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Nicaragua", "Panama",
    
    # Caribbean
    "Antigua and Barbuda", "Bahamas", "Barbados", "Cuba", "Dominica", "Dominican Republic", 
    "Grenada", "Haiti", "Jamaica", "Saint Kitts and Nevis", "Saint Lucia", 
    "Saint Vincent and the Grenadines", "Trinidad and Tobago",
    
    # South America
    "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "Guyana", "Paraguay", 
    "Peru", "Suriname", "Uruguay", "Venezuela",
    
    # Oceania
    "Australia", "Fiji", "Kiribati", "Marshall Islands", "Micronesia", "Nauru", "New Zealand", 
    "Palau", "Papua New Guinea", "Samoa", "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu"
]


european_countries = [
    'Albania', 'Andorra', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 'Bosnia and Herzegovina',
    'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France',
    'Georgia', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kazakhstan', 
    'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 
    'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 
    'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 
    'Switzerland', 'Turkey', 'Ukraine', 'United Kingdom', 'Vatican City'
] 

author_data['year_map'] = "" # New column for the year considered to plot the maps (death year or birth year + 60)

# Create new columns to add the coordinates of the places
author_data['borncity_coordinates'] = ""
author_data['deathcity_coordinates'] = ""
author_data['activecity_coordinates'] = ""

# Create new columns to indicate the countries of the places
author_data['borncity_country'] = ""
author_data['deathcity_country'] = ""
author_data['activecity_country'] = ""

# Create new columns to track incorrect geocodes in the Americas or Oceania before 1500 for each location type
author_data['borncity_americas_or_oceania_before_1500'] = ""
author_data['deathcity_americas_or_oceania_before_1500'] = ""
author_data['activecity_americas_or_oceania_before_1500'] = ""

author_data['city_id'] = ""  # New column for unique IDs
author_data['city_id_number'] = ""  # New column for unique IDs numbers



# Identify unique city names across columns for geocoding
city_columns = ['borncity', 'deathcity', 'activecity']


# Initialize a counter for unique IDs
unique_id = 1  # Start with 1 and increment for each new unique location
# A dictionary to store existing coordinates and their IDs
id_cache = {}

 


# For each row, if the death year is not empty, add it to the "year_map" column, if it is empty, add the "birth_year"+ 60
for author, row in author_data.iterrows():
    if pd.notna(row['deathyear']):  # If there is a death year
        author_data.at[author, "year_map"] = int(row['deathyear'])  # the column "year_map" receives the deathyear
    else:
        author_data.at[author, "year_map"] = int(row['birthyear']) + 60  # the column "year_map" receives the birthyear + 60
        
author_data['year_map'] = pd.to_numeric(author_data['year_map'], errors='coerce')

    # In each row, go through each city in each column (born, death and active). If empty return None
for author, row in author_data.iterrows():
 
    for city_col in city_columns:
        city_name = row[city_col]

        # Skip processing if the city name is empty or NaN
        if not city_name or pd.isna(city_name):
            continue 
        
        # Create a composite key for the cache using city_name and unique_id (optional, you could use city_name + country)
        cache_key = city_name
        
        # Check if the city is not in the cache
        if city_name not in geocode_cache:
            # Check if the city exists in the whitelist
            matching_rows = whitelist_cities.loc[(whitelist_cities["ASCII Name"] == city_name) | (whitelist_cities["Name"] == city_name)]

            
            # If there's more than one matching row, apply the 1500 year rule for prioritization
            if len(matching_rows) > 1:
                if row['year_map'] < 1500:
                    # Filter for European locations if the year is before 1500
                    european_matches = matching_rows[matching_rows["Country"].isin(european_countries)]
                    
                    if len(european_matches) > 0:
                        # Retrieve the city with the largest population from European matches
                        matching_rows = european_matches.loc[european_matches['Population'].idxmax()]
                        
                        
                        coordinates = matching_rows["Coordinates"]
                        country = matching_rows["Country"]

                        # Update the geocoded data for the respective city column (born, death, or active)
                        author_data.at[author, f'{city_col}_coordinates'] = coordinates
                        author_data.at[author, f'{city_col}_country'] = country
                        
                        # Store the city and its associated data in the geocode cache
                        geocode_cache[cache_key] = {'coordinates': coordinates, 'country': country, 'city_id': unique_id}
                        
                        # Save incrementally after each city
                        save_cache()  
                        
                        
                        # Set the flag dynamically, if a country is in america or oceania before 1500, set yes, otherwise, no
                        is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()

                        # is_in_americas_or_oceania = country in americas_or_oceania_countries
                        before_1500 = row['year_map'] < 1500
                        
                        if before_1500 and is_in_americas_or_oceania:
                            author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "yes"
                        else:
                            author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "no"     
                            
                        
                        # Assign unique ID based on coordinates
                        if coordinates not in id_cache:  # If the coordinates of the place are not in the cache yet
                            id_cache[coordinates] = unique_id  # Give a unique ID to that coordinate (location)
                            author_data.at[author, f'{city_col}_id'] = unique_id  # Assign unique ID to the corresponding city column (born, death, or active)
                            unique_id += 1
                        else:
                            # Assign the already existing ID to the city column
                            author_data.at[author, f'{city_col}_id'] = id_cache[coordinates]

                            
                            
                    else:
                        # If no European match, choose the row with the largest population
                        matching_rows = matching_rows.loc[matching_rows['Population'].idxmax()]
                        
                        
                        coordinates = matching_rows["Coordinates"]
                        country = matching_rows["Country"]

                        # Update the geocoded data for the respective city column (born, death, or active)
                        author_data.at[author, f'{city_col}_coordinates'] = coordinates
                        author_data.at[author, f'{city_col}_country'] = country
                        
                        # Store the city and its associated data in the geocode cache
                        geocode_cache[cache_key] = {'coordinates': coordinates, 'country': country, 'city_id': unique_id}
                        
                        # Save incrementally after each city
                        save_cache()  
                        
                        
                        # Set the flag dynamically, if a country is in america or oceania before 1500, set yes, otherwise, no
                        is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()

                        # is_in_americas_or_oceania = country in americas_or_oceania_countries
                        
                        before_1500 = row['year_map'] < 1500
                        if before_1500 and is_in_americas_or_oceania:
                            author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "yes"
                        else:
                            author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "no"   
                            
                        
                        # Assign unique ID based on coordinates
                        if coordinates not in id_cache:  # If the coordinates of the place are not in the cache yet
                            id_cache[coordinates] = unique_id  # Give a unique ID to that coordinate (location)
                            author_data.at[author, f'{city_col}_id'] = unique_id  # Assign unique ID to the corresponding city column (born, death, or active)
                            unique_id += 1
                        else:
                            # Assign the already existing ID to the city column
                            author_data.at[author, f'{city_col}_id'] = id_cache[coordinates]

                        
                            
                else:
                    # If the year is >= 1500, choose the city with the largest population
                    matching_rows = matching_rows.loc[matching_rows['Population'].idxmax()]  # Retrieve the city with the current largest population
                    
                    
                    coordinates = matching_rows["Coordinates"]
                    country = matching_rows["Country"]

                    # Update the geocoded data for the respective city column (born, death, or active)
                    author_data.at[author, f'{city_col}_coordinates'] = coordinates
                    author_data.at[author, f'{city_col}_country'] = country
                    
                    # Store the city and its associated data in the geocode cache
                    geocode_cache[cache_key] = {'coordinates': coordinates, 'country': country, 'city_id': unique_id}
                    
                    # Save incrementally after each city
                    save_cache()  
                    
                    
                    # Set the flag dynamically, if a country is in america or oceania before 1500, set yes, otherwise, no
                    is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()

                    # is_in_americas_or_oceania = country in americas_or_oceania_countries
                    before_1500 = row['year_map'] < 1500
                    if before_1500 and is_in_americas_or_oceania:
                        author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "yes"
                    else:
                        author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "no"  
                    
                    
                    # Assign unique ID based on coordinates
                    if coordinates not in id_cache:  # If the coordinates of the place are not in the cache yet
                        id_cache[coordinates] = unique_id  # Give a unique ID to that coordinate (location)
                        author_data.at[author, f'{city_col}_id'] = unique_id  # Assign unique ID to the corresponding city column (born, death, or active)
                        unique_id += 1
                    else:
                        # Assign the already existing ID to the city column
                        author_data.at[author, f'{city_col}_id'] = id_cache[coordinates]

                    
                    
                    
            
            # Check if there is only one city in the whitelist that matches the city author
            if len(matching_rows) == 1:
                # Retrieve the coordinates and country from the matched row
                coordinates = matching_rows["Coordinates"].iloc[0]
                country = matching_rows["Country"].loc[0]

                # Update the geocoded data for the respective city column (born, death, or active)
                author_data.at[author, f'{city_col}_coordinates'] = coordinates
                author_data.at[author, f'{city_col}_country'] = country
                
                # Store the city and its associated data in the geocode cache
                geocode_cache[cache_key] = {'coordinates': coordinates, 'country': country, 'city_id': unique_id}
                
                # Save incrementally after each city
                save_cache()                     
                
                # Set the flag dynamically, if a country is in america or oceania before 1500, set yes, otherwise, no
                is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()

                # is_in_americas_or_oceania = country in americas_or_oceania_countries
                before_1500 = row['year_map'] < 1500
                if before_1500 and is_in_americas_or_oceania:
                    author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "yes"
                else:
                    author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "no"     
                
                # Assign unique ID based on coordinates
                if coordinates not in id_cache:  # If the coordinates of the place are not in the cache yet
                    id_cache[coordinates] = unique_id  # Give a unique ID to that coordinate (location)
                    author_data.at[author, f'{city_col}_id'] = unique_id  # Assign unique ID to the corresponding city column (born, death, or active)
                    unique_id += 1
                else:
                    # Assign the already existing ID to the city column
                    author_data.at[author, f'{city_col}_id'] = id_cache[coordinates]

        else:
            # Retrieve cached coordinates and country
            cached_data = geocode_cache[cache_key]
            author_data.at[author, f'{city_col}_coordinates'] = cached_data['coordinates']
            author_data.at[author, f'{city_col}_country'] = cached_data['country']
            author_data.at[author, f'{city_col}_id'] = cached_data.get('city_id',None)
            
            # Check if the cached country is in Americas or Oceania and apply the flag logic
            country = cached_data.get('country', None)
            is_in_americas_or_oceania = country in americas_or_oceania_countries if isinstance(country, str) else country.isin(americas_or_oceania_countries).any()

            # is_in_americas_or_oceania = country in americas_or_oceania_countries
            before_1500 = row['year_map'] < 1500

            if before_1500 and is_in_americas_or_oceania:
                author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "yes"
            else:
                author_data.at[author, f'{city_col}_americas_or_oceania_before_1500'] = "no"


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
    author_data = map_coordinates(author_data, city_col)

# Step 5: Reorder the columns to place americas_or_oceania_before_1500 after the country columns
cols = ['borncity_coordinates', 'borncity_country', 'borncity_americas_or_oceania_before_1500', 
        'deathcity_coordinates', 'deathcity_country', 'deathcity_americas_or_oceania_before_1500', 
        'activecity_coordinates', 'activecity_country', 'activecity_americas_or_oceania_before_1500']

# Reorder DataFrame columns
author_data = author_data[['indexauthor', 'starturl', 'birthyear', 'deathyear', 'nameandbirthdeathyear', 
                               'georeferenceurl', 'borncity', 'deathcity', 'activecity'] + cols]



print(author_data.head())



output_file_csv = './path/to/your/file.csv'
output_file_excel = './path/to/your/file.xlsx'

author_data.to_csv(output_file_csv, index=False)
author_data.to_excel(output_file_excel, index=False)




 
