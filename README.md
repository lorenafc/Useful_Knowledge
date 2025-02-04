
# Useful Knowledge Project

## Non-City Authors

### Overview
This part of the project involves the geocoding and visualization of authors from small cities, retrieved from the [Virtual International Authority File (VIAF)](https://viaf.org/) by [Eric Chaney](https://www.tse-fr.eu/sites/default/files/TSE/documents/sem2022/bid/chaney.pdf).

- **Dataset**: The dataset used contains author names, authors index, their birth and death years, birth, death, and active cities, the VIAF URL and  a georeference URL.

- The original dataset had encoding issues with some names. Most of these encoding errors were corrected using the script in Google Colab: fix_city_names_encoding.ipynb. Eric Chaney assisted with correcting the remaining encoding issues.
  
- **Geocoding Scripts**:
  - The geocoding of the locations is performed using Google Maps API, and cities not successfully geocoded are handled with the OpenAI API. Remaining locations will be done manually.

  - **preprocessing_GoogleAPI.py (In Progress)**: Uses Google Maps API to geocode cities according to a historical context, adding flags for cities geocoded incorrectly (e.g., those appearing in the Americas and Oceania before their discovery). Replace `API_KEY = "YOUR_GOOGLE_API_KEY"` with your own key.

  - **preprocessing_openAI_API.py** (Optional): Geocodes the remaining cities not geocoded by Google Maps API using OpenAI’s API, considering historical context. Replace `openai.api_key = 'your_openai_api_key'` with your own key.

- **Visualization**: A mapping script generates maps of author activity hotspots for each year from 800 to 1800 AD, displaying author locations on world maps and creating an animated GIF or video.

## Environment Setup

This project was built using **Python 3.8.19**. Make sure you are using this version or a compatible one to avoid potential issues with library compatibility.

### Libraries:
- **openai**: Version `0.28.0`
- **pandas**: Version `1.4.4`
- **googlemaps**: Version `4.10.0`
- **geopandas**: Version `0.13.2`
- **contextily**: Version `1.6.0`
- **matplotlib**: Version `3.4.3`

### Media Processing Libraries:
- **imageio**: Version `2.33.1` (for GIF creation)
- **moviepy**: Version `1.0.3` (for video creation)

### License
This project is licensed under the MIT License.

### Other
The inicial work of geododing and visualization the UKP was made [here](https://github.com/lorenafc/Capita_Selecta_RHI50403).


