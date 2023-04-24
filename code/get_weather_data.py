# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# get_weather_data.py
#
# This script downloads and processes weather raster data for specified variables
# and years, trims the rasters to the North Carolina boundary, and aggregates them
# for each variable type.
#
# The getWeatherData function performs the following tasks:
# 1. Downloads weather raster data for specified variables and years.
# 2. Extracts the data from zip files.
# 3. Trims the raster data to the North Carolina boundary and saves them to the workspace.
# 4. Aggregates the rasters for each variable type (avg precipitation, min temperature, and max temperature).
# 5. Deletes unneeded rasters from the workspace.
# 6. Returns the names of the aggregated rasters as a list of strings.


# Import libraries
import urllib.request
import os
import arcpy 
import zipfile
from typing import List

def getWeatherData(data_path:str, 
                   wspace:str,
                   nc_boundary:str,
                   avg_prec_data:str="avgPrecip_all_years",
                   min_temp_data:str="minTemp_all_years",
                   max_temp_data:str="maxTemp_all_years") -> List[str]:
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    # Set workspace
    arcpy.env.workspace = wspace

    vars = ["ppt", "tmax", "tmin"]
    yrs = [2017, 2018, 2019]
    pairs = list()
    pairs = [(v, y) for v in vars for y in yrs if (v, y) not in pairs]

    # Get Raster Data
    arcpy.AddMessage("Getting explanatory Weather Rasters...")
    print("Getting explanatory Weather Rasters...")
    # Data documentation https://www.prism.oregonstate.edu/documents/PRISM_downloads_web_service.pdf
    out_path = os.path.join(data_path, "weather/")
    os.makedirs(out_path, exist_ok=True)
    for v, y in pairs:
        dwnld_out = os.path.join(out_path, f"{v}_{y}.zip")
        dwnld_path = os.path.join(out_path, f"{v}_{y}")
        if not os.path.exists(dwnld_path):
            url = f"https://services.nacse.org/prism/data/public/4km/{v}/{y}" 
            arcpy.AddMessage(f"Downloading weather data from {url}...")
            print(f"Downloading weather data from {url}...")
            urllib.request.urlretrieve(url, dwnld_out)
            arcpy.AddMessage(f"Saved {v}/{y} to {dwnld_out}")
            print(f"Saved {v}/{y} to {dwnld_out}")
            # Credit to this method of unzipping a zip file goes to Shyamal Vaderia
            # (see https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/)
            with zipfile.ZipFile(dwnld_out, "r") as zfile:
                zfile.extractall(dwnld_path)
            arcpy.AddMessage(f"Extracted {v}/{y} from {dwnld_out} to {dwnld_path}")
            print(f"Extracted {v}/{y} from {dwnld_out} to {dwnld_path}")
            os.remove(dwnld_out)
        
        # Trim to be only NC
        v_y_fc = f"{v}_{y}_weather_raster"
        if any(raster not in arcpy.ListRasters() for raster in \
               [avg_prec_data, min_temp_data, max_temp_data]):
            arcpy.AddMessage(f"Saving {v_y_fc} raster to geodatabase...")
            print(f"Saving {v_y_fc} raster to geodatabase...")
            arcpy.env.workspace = dwnld_path
            raster = os.path.join(dwnld_path, arcpy.ListRasters()[0])
            arcpy.env.workspace = wspace
            out_raster = arcpy.sa.ExtractByMask(raster, nc_boundary)
            out_raster.save(v_y_fc)
            arcpy.AddMessage(f"Saved {v_y_fc} successfully!")
            print(f"Saved {v_y_fc} successfully!")

    # Average with other years of same var type
    for var in vars:
        rasters = [f"{var}_{yr}_weather_raster" for yr in yrs]
        if var == "tmax":
            raster_out = max_temp_data
            agg_func = "MAXIMUM"
        elif var == "tmin":
            raster_out = min_temp_data
            agg_func = "MINIMUM"
        elif var == "ppt":
            raster_out = avg_prec_data
            agg_func = "MEAN"
        if not raster_out in arcpy.ListRasters():
                arcpy.AddMessage(f"Aggregating {var} for all years...")
                print(f"Aggregating {var} for all years...")
                outCellStats = arcpy.sa.CellStatistics(rasters, agg_func, "DATA")
                outCellStats.save(raster_out)
                arcpy.AddMessage(f"Finished aggregating {var} for all years.")
                print(f"Finished aggregating {var} for all years.")
    
    # Delete unneeded rasters
    for v, y in pairs:
        if f"{v}_{y}_weather_raster" in arcpy.ListRasters():
            print(f"Cleaning up {v}_{y}_weather_raster")
            arcpy.AddMessage(f"Cleaning up {v}_{y}_weather_raster")
            arcpy.Delete_management(f"{v}_{y}_weather_raster")

    return [avg_prec_data, min_temp_data, max_temp_data]