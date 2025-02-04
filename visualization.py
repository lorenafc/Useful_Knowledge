# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 2024

@author: Lorena Carpes

"""


# source Chat GPT and Lucas Koren


# Install necessary libraries if not already installed
# Uncomment these lines if needed
# !pip install geopandas
# !pip install matplotlib
# !pip install contextily
# !pip install pyproj
# !pip install matplotlib-scalebar

# Import libraries
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as cx
import os
import imageio
from pyproj import Geod
from moviepy.editor import ImageSequenceClip
from shapely.geometry import Point, LineString
import matplotlib.colors as mcolors
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.patches as mpatches



# Set file paths for Spyder
file_path = 'path/to/your/file.csv'
# Set file paths for relative paths

output_images_dir = 'path/to/your/output/folder'
os.makedirs(output_images_dir, exist_ok=True)

# Load data
authors_small_cities = pd.read_csv(file_path)


def combine_geographic_data(df):
    """
    Combines geographic points data from birth, death, and active locations into a single GeoDataFrame,
    applies temporal filters, and adjusts coordinate reference systems.
    
    :param df: pd.DataFrame, the DataFrame containing geographic coordinates and temporal data.
    :return: gpd.GeoDataFrame, the combined and filtered GeoDataFrame with geographic and temporal adjustments.
    """
    # Function to split coordinates into latitude and longitude
    def parse_coordinates(coord_str):
        try:
            lat, lon = map(float, coord_str.split(", "))
            return lon, lat  # Order should be (lon, lat) for Point
        except:
            return None, None

    # Extract coordinates for birth, death, and active locations
    birth_points = gpd.GeoSeries(
        [Point(parse_coordinates(xy)) if xy and pd.notnull(xy) else None for xy in df['borncity_coordinates']],
        crs="EPSG:4326"
    )
    death_points = gpd.GeoSeries(
        [Point(parse_coordinates(xy)) if xy and pd.notnull(xy) else None for xy in df['deathcity_coordinates']],
        crs="EPSG:4326"
    )
    active_points = gpd.GeoSeries(
        [Point(parse_coordinates(xy)) if xy and pd.notnull(xy) else None for xy in df['activecity_coordinates']],
        crs="EPSG:4326"
    )

    # Combine points into a single GeoSeries, prioritizing death, active, then birth
    combined_points = death_points.fillna(active_points).fillna(birth_points)
    
    # Create a GeoDataFrame using the combined geometry column
    authors_geo_df = gpd.GeoDataFrame(df, geometry=combined_points)
    authors_geo_df = authors_geo_df[authors_geo_df.geometry.notnull()]  # Filter non-null geometry

    # Use the 'year_map' column as 'effective_year' 
    authors_geo_df['effective_year'] = authors_geo_df['year_map']
    
    # Convert CRS to Web Mercator for mapping
    authors_geo_df = authors_geo_df.set_crs("EPSG:4326").to_crs(epsg=3857)

    return authors_geo_df



# function to plot the maps
def plot_maps_per_year(startyear, endyear, gdf, output_images_dir):
    """
    Generates a series of maps showing authors' activity hotspots for each year within the specified range
    and saves the maps as PNG files.

    Parameters:
    startyear (int): The starting year for generating maps.
    endyear (int): The ending year for generating maps.
    gdf (GeoDataFrame): GeoDataFrame containing author data with columns for death year and geometry.
    output_images_dir (str): The directory where the output plot images will be saved.
    """
    # World boundaries in Web Mercator projection
    world_bounds = [-20037508.34, -8399737.88, 20037508.34, 10958014.95]
    
    # if Europe map:
    # Europe boundaries in Web Mercator projection:
    # world_bounds = [-1669792, 3503549.84, 3339584.72, 8399737.88] # ajust to zoom in or out if you want to show more/less countries.


    # Invisible points to ensure full basemap is displayed
    invisible_points = gpd.GeoDataFrame({
        'geometry': [
            Point(-20037508.34, -20037508.34),  # Bottom left
            Point(20037508.34, -20037508.34),   # Bottom right
            Point(-20037508.34, 20037508.34),   # Top left
            Point(20037508.34, 20037508.34)     # Top right
        ],
        'point_count': [0, 0, 0, 0]
    }, crs="EPSG:3857")

    # Define a custom color map
    cmap = mcolors.ListedColormap(['#B0B0B0', '#8C8C8C', '#696969', '#4D4D4D', '#303030', '#000000'])
    bounds = [1, 2, 4, 6, 8, 10]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    # Function to determine opacity
    def get_opacity(count):
        if count >= 10:
            return 0.4  # 40% opacity
        elif count >= 4:
            return 0.6  # 60% opacity
        else:
            return 1.0  # No transparency

    # Loop through each year in the specified range
    for year in range(startyear, endyear + 1):
        # Create a string to represent the current year
        years = f"{year}"

        # Filter the GeoDataFrame for authors active in the timestep for 10 years prior to his/her death
        authors_active_timestep = gdf[
            (gdf['effective_year'] >= year) &
            (gdf['effective_year'] <= year + 10)
        ]

        # Check if there are any valid records for the current timestep
        if not authors_active_timestep.empty:
            # Group by unique points and get the count for each group and turn into GeoDataFrame
            unique_points_gdf = gpd.GeoDataFrame(
                authors_active_timestep.groupby('geometry').size().reset_index(name='point_count'),
                geometry='geometry'
            )

            # Ensure the CRS is set to EPSG:3857 for latitude and longitude
            unique_points_gdf = unique_points_gdf.set_crs(epsg=3857, allow_override=True)

            # Add invisible points to ensure full basemap is displayed
            unique_points_gdf = pd.concat([unique_points_gdf, invisible_points], ignore_index=True)

            # Add opacity column based on the point_count
            unique_points_gdf['opacity'] = unique_points_gdf['point_count'].apply(get_opacity)

            fig, ax = plt.subplots(figsize=(19, 10))
            
            # if Europe map:
            # fig, ax = plt.subplots(figsize=(10, 9))

            # Plot the points with the custom color map and varying transparency
            unique_points_gdf.plot(
                ax=ax,
                column='point_count',
                cmap=cmap,
                norm=norm,
                markersize=unique_points_gdf['point_count'] * 30,
                aspect=0.7,
                alpha=unique_points_gdf['opacity'] )#,  # Use the opacity column here
                #edgecolor='black'
           #)

            # Add basemap with fixed zoom level
            cx.add_basemap(ax, attribution=False, zoom=2, crs=unique_points_gdf.crs.to_string(), source=cx.providers.CartoDB.VoyagerNoLabels)

            # Tight layout
            fig.tight_layout(pad=3)

            # Labels inside the map
            ax.tick_params(direction="in")

            # Set plot limits to fixed geographic bounds
            ax.set_xlim(world_bounds[0], world_bounds[2])
            ax.set_ylim(world_bounds[1], world_bounds[3])

            # Set title and axis labels
            ax.set_title(f"Authors' Hotspots ({years})")
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')

            # Set tick labels to show the Mercator projection coordinates
            ax.set_xticks([-20037508.34, -16697923.611, -13358339.89, -10018754.17, -6679169.45, -3339584.72, 0, 3339584.72, 6679169.45, 10018754.17, 13358339.89, 16697923.61, 20037508.34])
            ax.set_xticklabels(['', '', '120° W', '90° W', '60° W', '30° W', '0°', '30° E', '60° E', '90° E', '120° E', '150° E', ''])

            ax.set_yticks([-8399737.88, -5621521.48, -3503549.84, -1689200.13, 0, 1689200.13, 3503549.84, 5621521.48, 8399737.88, 10958014.95])
            ax.set_yticklabels(["", "45° S", '30° S', "15° S", '0°', "15° N", '30° N', "45° N", "60° N", ""])

            # if Europe map:
            ## Set title and axis labels
            # ax.set_title(f"Authors' Hotspots ({years}) - Europe")
            # ax.set_xlabel('Longitude')
            # ax.set_ylabel('Latitude')
        
            # ax.set_xticks([-1669792, 0, 1669792, 3339584.72])
            # ax.set_xticklabels(['', '0°', '15° E', ''])
        
            # ax.set_yticks([3503549.84, 5621521, 7361866, 8399737.88])
            # ax.set_yticklabels(['', '45° N', '55° N', ''])


            # Disable the grid lines
            ax.grid(False)

            # Adjust position of tick labels
            ax.tick_params(axis='x', pad=-15, labelsize=8)
            ax.tick_params(axis='y', pad=-30, labelsize=8)

            # Add the Projected Coordinate System
            ax.annotate("Projected Coordinate System:\n WGS 84 / Pseudo-Mercator", xy=(0.08, 0.04), ha="center", va="center", fontsize=8, xycoords=ax.transAxes)

            # Create a legend
            legend_handles = [
                mpatches.Patch(color="#B0B0B0", label="1 author"),     # Lightest Grey
                mpatches.Patch(color="#8C8C8C", label="2-3 authors"),  # Light Grey
                mpatches.Patch(color="#696969", label="4-5 authors"),  # Medium Grey
                mpatches.Patch(color="#4D4D4D", label="6-7 authors"),  # Dark Grey
                mpatches.Patch(color="#303030", label="8-9 authors"),  # Very Dark Grey
                mpatches.Patch(color="#000000", label="10+ authors")   # Black
            ]

            # Add the legend to the plot
            ax.legend(handles=legend_handles, loc='lower right')

            # North arrow
            x, y, arrow_length = 0.95, 0.95, 0.08
            ax.annotate('N', xy=(x, y), xytext=(x, y - arrow_length),
                        arrowprops=dict(facecolor='black', width=5, headwidth=15),
                        ha='center', va='center', fontsize=20,
                        xycoords=ax.transAxes)

            # Save plot as .png file
            output_path = os.path.join(output_images_dir, f"active_hotspot_world_year_{years}.png")
            plt.savefig(output_path)
            plt.close(fig)  
            # plt.show()


# # generate plots
# authors_gdf = combine_geographic_data(authors_small_cities)
# plot_maps_per_year(800, 1800, authors_gdf, output_images_dir)



# Birth Death Map - 800-1800

def plot_authors_birth_death(gdf, start_year, end_year, output_dir):

    """
    Plots the birth and death locations of authors along with geodesic lines connecting these points on a map.

    Parameters:
    gdf (DataFrame): DataFrame containing author data with columns for latitude and longitude of birth and death.
    start_year (int): The start year for filtering the authors.
    end_year (int): The end year for filtering the authors.
    output_dir (str): The directory where the output plot image will be saved.

    """
   
    gdf = gdf[(gdf['deathyear'] >= start_year) & (gdf['deathyear'] <= end_year)  
    gdf = gdf.dropna(subset=['latitude_born', 'longitude_born', 'latitude_death', 'longitude_death'])

    gdf['birth_point'] = gdf.apply(lambda row: Point(row['longitude_born'], row['latitude_born']), axis=1)
    gdf['death_point'] = gdf.apply(lambda row: Point(row['longitude_death'], row['latitude_death']), axis=1)

    def create_geodesic_line(row):
        geod = Geod(ellps="WGS84")
        lon1, lat1 = row['longitude_born'], row['latitude_born']
        lon2, lat2 = row['longitude_death'], row['latitude_death']
        # Use npts method to calculate geodesic line
        points = geod.npts(lon1, lat1, lon2, lat2, 20) # Use npts to get intermediate points

        return LineString([(lon1, lat1)] + points + [(lon2, lat2)])

    gdf['line'] = gdf.apply(create_geodesic_line, axis=1)

    # Create GeoDataFrames for points and lines
    birth_points_gdf = gpd.GeoDataFrame(gdf, geometry='birth_point')
    death_points_gdf = gpd.GeoDataFrame(gdf, geometry='death_point')
    lines_gdf = gpd.GeoDataFrame(gdf, geometry='line')

    birth_points_gdf.set_crs(epsg=4326, inplace=True)
    death_points_gdf.set_crs(epsg=4326, inplace=True)
    lines_gdf.set_crs(epsg=4326, inplace=True)

    # Convert to Web Mercator projection 
    birth_points_gdf = birth_points_gdf.to_crs(epsg=3857)
    death_points_gdf = death_points_gdf.to_crs(epsg=3857)
    lines_gdf = lines_gdf.to_crs(epsg=3857)

    world_bounds = [-20037508.34, -8399737.88, 20037508.34, 10958014.95] # World boundaries

    fig, ax = plt.subplots(figsize=(19, 10))

    birth_points_gdf.plot(ax=ax, color='orange', alpha=0.8, markersize=1, marker="*", zorder=3, label='Birth Locations')

    death_points_gdf.plot(ax=ax, color='black', markersize=1, marker="x", zorder=2, label='Death Locations')

    lines_gdf.plot(ax=ax, color='grey', linewidth=0.1, zorder=1)

    cx.add_basemap(ax, attribution=False, zoom=5, crs=birth_points_gdf.crs.to_string(), source=cx.providers.CartoDB.VoyagerNoLabels)
    fig.tight_layout(pad=3)
    ax.tick_params(direction="in")

    plt.legend(['Birth Location', 'Death Location'], loc="lower left")

    x, y, arrow_length = 0.95, 0.95, 0.07
    ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                arrowprops=dict(facecolor='black', width=4, headwidth=12),
                ha='center', va='center', fontsize=17,
                xycoords=ax.transAxes)

    ax.set_xlim(world_bounds[0], world_bounds[2])
    ax.set_ylim(world_bounds[1], world_bounds[3])

    ax.set_title("Authors' Birth and Death Locations (800-1800)")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    ax.set_xticks([-20037508.34, -16697923.611, -13358339.89, -10018754.17, -6679169.45, -3339584.72, 0, 3339584.72, 6679169.45, 10018754.17, 13358339.89, 16697923.61, 20037508.34])
    ax.set_xticklabels(['', '', '120° W', '90° W', '60° W', '30° W', '0°', '30° E', '60° E', '90° E', '120° E', '150° E', ''])

    ax.set_yticks([-8399737.88, -5621521.48, -3503549.84, -1689200.13, 0, 1689200.13, 3503549.84, 5621521.48, 8399737.88, 10958014.95])
    ax.set_yticklabels(["", "45° S", '30° S', "15° S", '0°', "15° N", '30° N', "45° N", "60° N", ""])

    ax.grid(False)

    ax.tick_params(axis='x', pad=-15, labelsize=8)
    ax.tick_params(axis='y', pad=-30, labelsize=8)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/authors_birth_death_world_{start_year}-{end_year}.png")

    plt.show()

plot_authors_birth_death(authors_small_cities_copy, start_year, end_year, output_dir)



################### North Sea region (NL, BE, UK):
    
def load_north_sea_data(file_name_ns, nl_shapefile, uk_shapefile, be_shapefile):
    """
    Loads the north sea data from an Excel file and combines shapefiles for the Netherlands, Belgium, and the UK.

    Parameters:
    file_name_ns (str): The path to the Excel file containing north sea data.
    nl_shapefile (str): The path to the Netherlands shapefile.
    uk_shapefile (str): The path to the UK shapefile.
    be_shapefile (str): The path to the Belgium shapefile.

    Returns:
    tuple: A DataFrame with north sea data and a combined GeoDataFrame of shapefiles.
    """
    # Load the north sea Excel file
    north_sea = pd.read_excel(file_name_ns, engine='openpyxl')

    # Load the shapefiles and convert them to the Web Mercator projection
    netherlands = gpd.read_file(nl_shapefile).to_crs(epsg=3857)
    belgium = gpd.read_file(be_shapefile).to_crs(epsg=3857)
    uk = gpd.read_file(uk_shapefile).to_crs(epsg=3857)

    # Combine the shapefiles into a single GeoDataFrame
    combined_shapefile = pd.concat([netherlands, belgium, uk])

    return north_sea, combined_shapefile


def prepare_geodata(authors_geo_df, combined_shapefile, north_sea):
    """
    Performs a spatial join to filter author points within the combined shapefile and prepares the north sea data for mapping.

    Parameters:
    authors_geo_df (GeoDataFrame): The GeoDataFrame containing author data. (it is the return of the function combine_geographic_data(df) )
    combined_shapefile (GeoDataFrame): The combined shapefiles for Netherlands, Belgium, and UK.
    north_sea (DataFrame): The DataFrame containing north sea data with longitude and latitude columns.

    Returns:
    tuple: A GeoDataFrame of authors within boundaries and a GeoDataFrame of north sea points in Web Mercator projection.
    """
    # Spatial join to filter points within the combined shapefile
    authors_within_boundaries = gpd.sjoin(authors_geo_df, combined_shapefile, predicate='within')

    # Convert the north sea data into a GeoDataFrame
    northsea_gdf = gpd.GeoDataFrame(
        north_sea, geometry=gpd.points_from_xy(north_sea.longitude, north_sea.latitude), crs="EPSG:4326"
    )

    # Convert the north sea GeoDataFrame to Web Mercator projection
    northsea_gdf = northsea_gdf.to_crs(epsg=3857)

    return authors_within_boundaries, northsea_gdf


""" This function below cleans the north sea and non city combined gdf. The resulting (renamed) columns are

    'indexnoncityandnorthseaauthors', 'indexnoncityauthor', 'starturl', 'birthyear', 'deathyear',
    'nameauthor', 'georeferenceurl', 'borncity', 'deathcity', 'activecity', 'citynorthsea', 'bairochcountry',
    'latnoncityborn', 'lonnoncityborn', 'latnoncitydeath', 'lonnoncitydeath',
    'latnoncityactive', 'lonnoncityactive', 'latnorthsea', 'lonnorthsea',
    'yearnoncity', 'yearnorthsea', 'year_plot', 'geometry'.

    The year_plot is sorted. The latitude (renamed "latnorthsea") and longitude
    (renamed "lonnorthsea") of the North sea dataset is only of the city used for the geocoding. In the Non city dataset
    The latitude and longitude were retrieved from all cities (it was added in the end of the lat and lon
    columns names  "noncityborn", "noncitydeath", "noncityactive")

    """

def combine_year_columns(authors_within_boundaries, northsea_gdf):
    """
    Creates a unified 'year_plot' column for both small cities and big cities datasets,
    change column names for the North Sea and Non city dataset, combines them into a single GeoDataFrame,
    sorts by 'year_plot', adds an index column 'indexnoncityandnorthseaauthors', and reorders columns.

    Parameters:
    authors_within_boundaries (GeoDataFrame): The GeoDataFrame of authors from small cities.
    northsea_gdf (GeoDataFrame): The GeoDataFrame of authors from big cities (North Sea region).

    Returns:
    GeoDataFrame: Combined GeoDataFrame with standardized columns, sorted by 'year_plot',
    with indices and columns in the specified order.
    """
    # Standardize the 'year_plot' column for both datasets
    authors_within_boundaries['year_plot'] = authors_within_boundaries['effective_year']
    northsea_gdf['year_plot'] = northsea_gdf['finalcedate']

    # Standardize the column names for the North Sea GeoDataFrame
    northsea_gdf = northsea_gdf.rename(columns={
        'finalname': 'nameauthor',
        'cleanedbirth': 'birthyear',
        'cleaneddeath': 'deathyear',
        'born': 'borncity',
        'death': 'deathcity',
        'active': 'activecity',
        'finalcedate': 'yearnorthsea',
        "city" : "citynorthsea",
        "latitude": "latnorthsea",
        "longitude": "lonnorthsea"
    })

    # Rename small cities' column to match North Sea dataset
    authors_within_boundaries = authors_within_boundaries.rename(columns={
        'nameandbirthdeathyear': 'nameauthor',
        'indexauthor': 'indexnoncityauthor',
        'effective_year': 'yearnoncity',
        "latitude_born": "latnoncityborn",
        "longitude_born": "lonnoncityborn",
        "latitude_death": "latnoncitydeath",
        "longitude_death": "lonnoncitydeath",
        "latitude_active": "latnoncityactive",
        "longitude_active": "lonnoncityactive"
    })

    # Combine the two datasets by appending rows
    combined_authors = pd.concat([authors_within_boundaries, northsea_gdf], ignore_index=True)

    # Drop unnecessary columns and handle duplicate columns (with .1 suffixes)
    columns_to_drop = [
        'shape0', 'shapeiso', 'shapegroup', 'shapetype', 'id', 'name', 'source', 'shapeid',
        'index_right', 'Unnamed: 21',
        'city.1', 'finalcedate.1', 'cleanedbirth.1', 'cleaneddeath.1',
        'originalbirth', 'originaldeath', 'deathid', 'bornid', 'activeid', 'cityid', 'finalcityid', 'imputeddeath'
    ]
    combined_authors = combined_authors.drop(columns=columns_to_drop, errors='ignore')

    # Sort the combined dataset by 'year_plot' from smallest to highest
    combined_authors = combined_authors.sort_values(by='year_plot', ascending=True)

    # Create a new index column called 'indexnoncityandnorthseaauthors'
    combined_authors['indexnoncityandnorthseaauthors'] = range(len(combined_authors))

    # Convert 'indexnoncityauthor' to numeric, allowing NaNs to remain unchanged
    combined_authors['indexnoncityauthor'] = pd.to_numeric(combined_authors['indexnoncityauthor'], downcast='integer', errors='coerce')

    # Reorder the columns as specified
    columns_order = [
    'indexnoncityandnorthseaauthors', 'indexnoncityauthor', 'starturl', 'birthyear', 'deathyear',
    'nameauthor', 'georeferenceurl', 'borncity', 'deathcity', 'activecity', 'citynorthsea', 'bairochcountry',
    'latnoncityborn', 'lonnoncityborn', 'latnoncitydeath', 'lonnoncitydeath',
    'latnoncityactive', 'lonnoncityactive', 'latnorthsea', 'lonnorthsea',
    'yearnoncity', 'yearnorthsea', 'year_plot', 'geometry'
]




    combined_authors = combined_authors[columns_order]

    return combined_authors


def save_combined_authors_to_files(combined_authors, file_path_excel, file_path_csv):
    """
    Saves the combined GeoDataFrame to both Excel and CSV files.

    Parameters:
    combined_authors (GeoDataFrame): The combined GeoDataFrame of authors data.
    file_path_excel (str): Path where the Excel file will be saved.
    file_path_csv (str): Path where the CSV file will be saved.
    """
    # Save the GeoDataFrame as an Excel file
    combined_authors.to_excel(file_path_excel, index=False)

    # Save the GeoDataFrame as a CSV file
    combined_authors.to_csv(file_path_csv, index=False)



# source: chatGPT and Lucas Koren

# The Norh Sea boundaries in Web Mercator projection
world_bounds = [0, 6000000, 837000, 7500000]

# Invisible points to ensure full basemap is displayed
invisible_points = gpd.GeoDataFrame({
    'geometry': [
        Point(-20037508.34, -20037508.34),  # Bottom left
        Point(20037508.34, -20037508.34),   # Bottom right
        Point(-20037508.34, 20037508.34),   # Top left
        Point(20037508.34, 20037508.34)     # Top right
    ],
    'point_count': [0, 0, 0, 0]
}, crs="EPSG:3857")

# Define a custom color map with inverted greyscale
cmap = mcolors.ListedColormap(['#000000', '#303030', '#4D4D4D', '#696969', '#8C8C8C', '#B0B0B0'])
bounds = [1, 3, 6, 9, 12, 15]
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Function to determine opacity
def get_opacity(count):
    if count >= 15:
        return 0.4
    elif count >= 9:
        return 0.6
    else:
        return 1.0

# Function to plot maps for each year
def plot_maps_per_year(startyear, endyear, combined_authors):
    for year in range(startyear, endyear + 1):
        # Filter the GeoDataFrame for authors active in the timestep for 10 years prior to their death
        # using the new unified 'year_plot' column
        combined_active_timestep = combined_authors[
            (combined_authors['year_plot'] >= year) &
            (combined_authors['year_plot'] <= year + 10)
        ]

        # Check if there are any valid records for the current year
        if not combined_active_timestep.empty:
            # Create a point_count column
            combined_active_timestep['point_count'] = 1

            # Group by unique points and get the count for each group and turn into GeoDataFrame  # source: https://sparkbyexamples.com/pandas/pandas-groupby-sum-examples/
            unique_points_gdf = combined_active_timestep.groupby('geometry').agg({'point_count': 'sum'}).reset_index()

        
            unique_points_gdf = gpd.GeoDataFrame(unique_points_gdf, geometry='geometry', crs='EPSG:3857')

            # Add invisible points to ensure full basemap is displayed
            unique_points_gdf = pd.concat([unique_points_gdf, invisible_points], ignore_index=True)

         
            unique_points_gdf['opacity'] = unique_points_gdf['point_count'].apply(get_opacity)


           
            fig, ax = plt.subplots(figsize=(19, 10))


            unique_points_gdf.plot(
                ax=ax,
                column='point_count',
                cmap=cmap,
                norm=norm,
                markersize=unique_points_gdf['point_count']*10,
                alpha=unique_points_gdf['opacity'],
                edgecolor='black'
            )

           
            cx.add_basemap(ax, attribution=False, zoom=3, crs=unique_points_gdf.crs.to_string(), source=cx.providers.CartoDB.VoyagerNoLabels)
       
            ax.set_xlim(world_bounds[0], world_bounds[2])
            ax.set_ylim(world_bounds[1], world_bounds[3])

            ax.set_title(f"Authors' Hotspots - North Sea area (The Netherlands, Belgium and UK) in {year}")
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')

            ax.set_xticks([-1669792, 0, 1113194])
            ax.set_xticklabels(['', '0°', ''])

            ax.set_yticks([6106854, 7361866, 8399737.88])
            ax.set_yticklabels(['', '55° N', ''])

         
            ax.tick_params(axis='x', pad=-15, labelsize=8)
            ax.tick_params(axis='y', pad=-30, labelsize=8)

            ax.annotate("Projected Coordinate System:\n WGS 84 / Pseudo-Mercator", xy=(0.87,0.04), ha= "center", va="center", fontsize=8, xycoords= ax.transAxes)



            legend_handles = [
                mpatches.Patch(color="#000000", label="1-2 authors"),
                mpatches.Patch(color="#303030", label="3-5 authors"),
                mpatches.Patch(color="#4D4D4D", label="6-8 authors"),
                mpatches.Patch(color="#696969", label="9-11 authors"),
                mpatches.Patch(color="#8C8C8C", label="12-14 authors"),
                mpatches.Patch(color="#B0B0B0", label="15+ authors")
            ]


            ax.legend(handles=legend_handles, loc='lower left')

            x, y, arrow_length = 0.95, 0.95, 0.08
            ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                        arrowprops=dict(facecolor='black', width=5, headwidth=15),
                        ha='center', va='center', fontsize=20,
                        xycoords=ax.transAxes)

            output_image_path = os.path.join(output_images_dir, f'active_north_sea_{year}.png')
            plt.savefig(output_image_path)
            plt.close(fig)
            # plt.show()


file_name_ns = '/content/belgiumnetherlandsuk.xlsx'
nl_shapefile = '/content/nl.shp'
uk_shapefile = '/content/uk.shp'
be_shapefile = '/content/be.shp'


north_sea, combined_shapefile = load_north_sea_data(file_name_ns, nl_shapefile, uk_shapefile, be_shapefile)

authors_geo_df = combine_geographic_data(authors_small_cities)

# Perform spatial join and get both non-city gdf and northsea_gdf
authors_within_boundaries, northsea_gdf = prepare_geodata(authors_geo_df, combined_shapefile, north_sea)

combined_authors = combine_year_columns(authors_within_boundaries, northsea_gdf)
     

plot_maps_per_year(800, 1800, combined_authors)