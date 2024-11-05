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


# Combine geographic data with modified latitude and longitude parsing
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
            plt.close(fig)  # Close the figure to avoid memory issues
            # plt.show()


# generate plots
authors_gdf = combine_geographic_data(authors_small_cities)
plot_maps_per_year(995, 998, authors_gdf, output_images_dir)