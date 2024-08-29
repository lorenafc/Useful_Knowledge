# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 11:25:27 2024

@author: Lorena Carpes
"""
 
# -*- coding: utf-8 -*-

#source: chatGPT 4.0

import openai
import pandas as pd
import time
import logging
from googlemaps import Client as GoogleMaps
import os



# Load the GeoNames whitelist - https://public.opendatasoft.com/explore/dataset/geonames-all-cities-with-a-population-500/information/?disjunctive.country
whitelist_file_path = './path/to/your/file/file.csv'
geonames_df = pd.read_csv(whitelist_file_path, delimiter=';')
whitelist_cities = geonames_df['Name'].str.strip().unique().tolist()

def correct_city_name_simple(city_name, api_key):
    """
    Corrects the encoding and spelling of a city name using the OpenAI API,
    unless the city name is on a whitelist of known correct names.

    Parameters:
    city_name (str): The city name to be corrected.
    api_key (str): OpenAI API key.

    Returns:
    str: The corrected city name, or the original name if no correction was needed.
    """
    if city_name in whitelist_cities:
        return city_name

    openai.api_key = api_key

    try:
        prompt_correct = (
            f"Correct the spelling of the following city name: '{city_name}'. "
            "Provide the correct city name only."
        )
        response_correct = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo", #"gpt-4o", gpt-4o-mini,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_correct}
            ],
            max_tokens=30,
            temperature=0.1,
            seed=123,
        )
        corrected_name = response_correct['choices'][0]['message']['content'].strip()
        return corrected_name
    except Exception as e:
        print(f"Error processing city name {city_name}: {e}")
        return city_name

def geocode_city_with_openai(city_name, name_and_year_info, birthyear, deathyear, api_key):
    """
    Geocodes a corrected city name using the OpenAI API, considering historical context.

    Parameters:
    city_name (str): The city name to be geocoded.
    name_and_year_info (str): Contextual information including the author's name and other details.
    birthyear (int/float): The birth year of the author (or NaN if not available).
    deathyear (int/float): The death year of the author (or NaN if not available).
    api_key (str): OpenAI API key.

    Returns:
    tuple: The latitude, longitude, and country name.
    """
    openai.api_key = api_key

    context = name_and_year_info
    if not pd.isna(birthyear):
        context += f", born in {int(birthyear)}"
    if not pd.isna(deathyear):
        context += f", died in {int(deathyear)}"

    try:
        prompt_geocode = (
            f"Given the city name '{city_name}' and the historical context '{context}', "
            "provide the most likely correct latitude, longitude, and country. Return the result in the format: latitude, longitude, country."
        )
        response_geocode = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo", #"gpt-4o",   "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_geocode}
            ],
            max_tokens=30,
            temperature=0.1,
            seed=123
        )
        result = response_geocode['choices'][0]['message']['content'].strip()
        parts = result.split(',')
        if len(parts) == 3:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            country = parts[2].strip()
            return lat, lon, country
        else:
            raise ValueError("Invalid response format from API")
    except Exception as e:
        print(f"Error processing city name {city_name}: {e}")
        return None, None, None

def correct_and_geocode(df, openai_api_key, output_file_csv, output_file_excel):
    """
    Corrects the city names in the DataFrame and geocodes the corrected names using OpenAI API.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the city names to be corrected and geocoded.
    openai_api_key (str): OpenAI API key.
    output_file_csv (str): The path to save the updated DataFrame with geocoded results in CSV format.
    output_file_excel (str): The path to save the updated DataFrame with geocoded results in Excel format.

    Returns:
    None
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    df['corrected_borncity'] = df.apply(lambda row: correct_city_name_simple(
        row['borncity'], openai_api_key
    ) if pd.notnull(row['borncity']) else row['borncity'], axis=1)

    df['corrected_deathcity'] = df.apply(lambda row: correct_city_name_simple(
        row['deathcity'], openai_api_key
    ) if pd.notnull(row['deathcity']) else row['deathcity'], axis=1)

    df['corrected_activecity'] = df.apply(lambda row: correct_city_name_simple(
        row['activecity'], openai_api_key
    ) if pd.notnull(row['activecity']) else row['activecity'], axis=1)

    df[['borncity_latitude', 'borncity_longitude', 'borncity_country']] = pd.DataFrame(df.apply(lambda row: geocode_city_with_openai(
        row['corrected_borncity'], row['nameandbirthdeathyear'], row['birthyear'], row['deathyear'], openai_api_key
    ) if pd.notnull(row['corrected_borncity']) else (None, None, None), axis=1).tolist(), index=df.index)

    df[['deathcity_latitude', 'deathcity_longitude', 'deathcity_country']] = pd.DataFrame(df.apply(lambda row: geocode_city_with_openai(
        row['corrected_deathcity'], row['nameandbirthdeathyear'], row['birthyear'], row['deathyear'], openai_api_key
    ) if pd.notnull(row['corrected_deathcity']) else (None, None, None), axis=1).tolist(), index=df.index)

    df[['activecity_latitude', 'activecity_longitude', 'activecity_country']] = pd.DataFrame(df.apply(lambda row: geocode_city_with_openai(
        row['corrected_activecity'], row['nameandbirthdeathyear'], row['birthyear'], row['deathyear'], openai_api_key
    ) if pd.notnull(row['corrected_activecity']) else (None, None, None), axis=1).tolist(), index=df.index)

    # Remove the 'Unnamed: 0' column if it exists
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    # Save the updated DataFrame to a CSV file
    df.to_csv(output_file_csv, index=False)
    logging.info(f"Saved the updated DataFrame to {output_file_csv}")

    # Save the updated DataFrame to an Excel file
    df.to_excel(output_file_excel, index=False)
    logging.info(f"Saved the updated DataFrame to {output_file_excel}")



# Load your CSV file into a DataFrame
file_path = './path/to/your/file/file.csv'
df = pd.read_csv(file_path)


# Set your API keys
openai_api_key = 'your_openai_api_key'  # Replace with your OpenAI API key
gmaps_key = 'your_google_maps_api_key'  # Replace with your Google Maps API key


# Set the output file path
output_file_csv = './path/to/your/file/output_file.csv'
output_file_excel = './path/to/your/file/output_file.xlsx'

# Run the correction and geocoding process
correct_and_geocode(df, openai_api_key, output_file_csv, output_file_excel)

