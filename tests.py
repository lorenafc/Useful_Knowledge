# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 15:59:24 2024

@author: Lorena Carpes
"""

#source: chatGPT 4.0


import pandas as pd

def check_ungeocoded_locations(file_path):
    # Load the csv file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Strip spaces and replace empty strings with NaN
    df['corrected_borncity'] = df['corrected_borncity'].apply(lambda x: x.strip() if isinstance(x, str) else x).replace('', pd.NA)
    df['corrected_deathcity'] = df['corrected_deathcity'].apply(lambda x: x.strip() if isinstance(x, str) else x).replace('', pd.NA)
    df['corrected_activecity'] = df['corrected_activecity'].apply(lambda x: x.strip() if isinstance(x, str) else x).replace('', pd.NA)
    
    # Check for missing geocoding in borncity
    ungeocoded_borncity = df[(df['corrected_borncity'].notnull()) & 
                              (df['borncity_latitude'].isnull() | df['borncity_longitude'].isnull())]
    
    # Check for missing geocoding in deathcity
    ungeocoded_deathcity = df[(df['corrected_deathcity'].notnull()) & 
                              (df['deathcity_latitude'].isnull() | df['deathcity_longitude'].isnull())]
    
    # Check for missing geocoding in activecity
    ungeocoded_activecity = df[(df['corrected_activecity'].notnull()) & 
                                (df['activecity_latitude'].isnull() | df['activecity_longitude'].isnull())]
    
    # Combine all unique geocoded places considering the coordinates (different locations can have the same name)
    unique_geocoded_places = pd.concat([
        df[['borncity_latitude', 'borncity_longitude']].dropna().drop_duplicates(),
        df[['deathcity_latitude', 'deathcity_longitude']].dropna().drop_duplicates(),
        df[['activecity_latitude', 'activecity_longitude']].dropna().drop_duplicates()
    ]).drop_duplicates().shape[0]
    
    # Combine all unique ungeocoded places
    unique_ungeocoded_places = pd.concat([
        ungeocoded_borncity['corrected_borncity'],
        ungeocoded_deathcity['corrected_deathcity'],
        ungeocoded_activecity['corrected_activecity']
    ]).nunique()
    
    # Calculate the percentage of unique places that were not geocoded
    percentage_ungeocoded = (unique_ungeocoded_places / unique_geocoded_places) * 100 if unique_geocoded_places > 0 else 0
    
    # Print out the results
    # print(f"Number of ungeocoded born cities: {len(ungeocoded_borncity)}")
    # print(f"Number of ungeocoded death cities: {len(ungeocoded_deathcity)}")
    # print(f"Number of ungeocoded active cities: {len(ungeocoded_activecity)}")
    
    # total_ungeocoded = len(ungeocoded_borncity) + len(ungeocoded_deathcity) + len(ungeocoded_activecity)
    # print(f"Total number of ungeocoded locations: {total_ungeocoded}")
    
    print(f"Total number of unique places: {unique_geocoded_places}")
    print(f"Total number of unique places not geocoded: {unique_ungeocoded_places}")
    print(f"Percentage of unique places not geocoded: {round(percentage_ungeocoded, 2)}%")
    
    return ungeocoded_borncity, ungeocoded_deathcity, ungeocoded_activecity

# Add your file
file_path = 'path/to/your/file.csv'
check_ungeocoded_locations(file_path)


