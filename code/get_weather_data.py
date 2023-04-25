# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# get_weather_data.py
#
# This script downloads and processes weather raster data for specified variables and years at a 
# 4km resolution and 30-year monthly normals at an 800m resolution. The script downloads, 
# aggregates, and resamples the rasters before trimming them to the North Carolina boundary.
#
# The `getWeatherData()` function performs the following tasks:
# 1. Downloads weather raster data for specified variables (yearly 4km 2017-19, monthly 30 year norms 800m)
# 2. Extracts the data from zip files.
# 3. Aggregates the rasters for each variable type (avg precipitation, min temperature, and max temperature).
# 4. Resamples the 4km data at an 800m level, and smooths it using the aggregated 800m monthly normals
# 5. Trims the raster data to the North Carolina boundary and saves them to the workspace.
# 6. Deletes unneeded rasters from the workspace.
# 7. Returns the names of the aggregated rasters as a list of strings.
#
### Simple Pseudocode #####
# FUNCTION getRastersFromDir(variables, periods, output path)
#     SET empty list for storing arcpy.Raster objects
#     FOR each period in periods
#         CONSTRUCT arcpy.Raster object with the period and variable
#         ADD arcpy.Raster object to the list
#     ENDFOR
#     RETURN list of arcpy.Raster objects
# ENDFUNC
# 
# FUNCTION getWeatherData(data path, workspace, NC Boundary, Coordinate System, 
#                         Avg. Prec. Output Name, Min. Temp. Output Name, 
#                         Max. Temp. Output Name)
#     CHECK if data_path exists, otherwise RAISE FileNotFoundError
#     CHECK if wspace exists, otherwise RAISE FileNotFoundError
#     SET workspace
#     GET raster data
#     PROCESS data and add to GDB
#     DELETE unneeded rasters
#     RETURN list of aggregated raster layer names
# ENDFUNC


# Import libraries
import urllib.request
import os
import arcpy 
import zipfile
from typing import List

def getRastersFromDir(var:str, 
                      periods:list, 
                      out_path:str) -> List[arcpy.Raster]:
    """
    Retrieves a list of arcpy.Raster objects from the specified directory based on the input parameters.
    Args
    var : The variable type (e.g. 'prcp', 'tmin', or 'tmax').
    periods : A list of periods (years or months) for which rasters are needed.
    out_path : The path to the directory containing the raster files.
    Output
    A list of arcpy.Raster objects corresponding to the specified variable and periods.
    """
    return [
        arcpy.Raster(
            os.path.join(
                os.path.join(out_path, f"{var}_{p}"), 
                [f for f in os.listdir(os.path.join(out_path, f"{var}_{p}") ) \
                 if f.endswith('.bil') and var in f][0]
            )
        ) for p in periods] 

def getWeatherData(data_path:str, 
                   wspace:str,
                   nc_boundary:str,
                   coord_system:arcpy.SpatialReference,
                   avg_prec_data:str="avgPrecip_all_years",
                   min_temp_data:str="minTemp_all_years",
                   max_temp_data:str="maxTemp_all_years") -> List[str]:
    """
    Downloads and processes weather raster data for specified variables and years at a 4km resolution 
    and 30-year monthly normals at an 800m resolution. The function downloads, aggregates, and resamples 
    the rasters before trimming them to the North Carolina boundary.
    Args
    - data_path : A file path to the data directory
    - wspace : A file path to the working directory/GDB
    - nc_boundary : A polygon of the state of North Carolina
    - coord_sys : The projected coordinate system
    - avg_prec_data : output raster name for average precipitation data
    - min_temp_data : output raster name for min temp. data
    - max_temp_data : output raster name for max temp. data
    Output
    A list of aggregated raster layer names (should match the last three inputs)
    """
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    ### Setup #######
    # Set workspace
    arcpy.env.workspace = wspace

    vars = ["ppt", "tmax", "tmin"]
    # Setup for yearly 4km resolution 
    yrs = [2017, 2018, 2019]
    pairs = list()
    pairs = [(v, y) for v in vars for y in yrs if (v, y) not in pairs]
    # Setup for 30 year normal monthly 800m resolution

    mnths = ["{:02d}".format(m) for m in range(1, 13)]
    norm_pairs = list()
    norm_pairs = [(v, m) for v in vars for m in mnths if (v, m) not in norm_pairs]

    ### Get Raster Data ######
    arcpy.AddMessage("Getting explanatory Weather Rasters...")
    print("Getting explanatory Weather Rasters...")
    # Data documentation https://www.prism.oregonstate.edu/documents/PRISM_downloads_web_service.pdf
    out_path = os.path.join(data_path, "weather/")
    os.makedirs(out_path, exist_ok=True)

    # 4km yearly data (for 2017-2019)
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
    
    # 800m monthly data (30 year normals), used to estimate higher resolution for the 4km data
    for v, m in norm_pairs:
        dwnld_out = os.path.join(out_path, f"{v}_{m}.zip")
        dwnld_path = os.path.join(out_path, f"{v}_{m}")
        if not os.path.exists(dwnld_path):
            url = f"https://services.nacse.org/prism/data/public/normals/800m/{v}/{m}" 
            arcpy.AddMessage(f"Downloading weather data from {url}...")
            print(f"Downloading weather data from {url}...")
            urllib.request.urlretrieve(url, dwnld_out)
            arcpy.AddMessage(f"Saved {v}/{m} to {dwnld_out}")
            print(f"Saved {v}/{m} to {dwnld_out}")
            # Credit to this method of unzipping a zip file goes to Shyamal Vaderia
            # (see https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/)
            with zipfile.ZipFile(dwnld_out, "r") as zfile:
                zfile.extractall(dwnld_path)
            arcpy.AddMessage(f"Extracted {v}/{m} from {dwnld_out} to {dwnld_path}")
            print(f"Extracted {v}/{m} from {dwnld_out} to {dwnld_path}")
            os.remove(dwnld_out)

    ### Process data and add to GDB #########
    for var in vars:
        if var == "tmax":
            raster = max_temp_data
        elif var == "tmin":
            raster = min_temp_data
        else:
            raster = avg_prec_data
        if raster not in arcpy.ListRasters():
            arcpy.env.overwriteOutput = True
            # Average with other years of same var type
            agg_rasters = dict()
            # Yearly data
            rasters = getRastersFromDir(var, yrs, out_path)
            raster_out = raster + "_US"
            if var == "tmax":
                agg_func = "MAXIMUM"
            elif var == "tmin":
                agg_func = "MINIMUM"
            elif var == "ppt":
                agg_func = "MEAN"
            agg_rasters.update({var:{"yr":raster_out}})
            arcpy.AddMessage(f"Aggregating {var} for all years...")
            print(f"Aggregating {var} for all years...")
            outCellStats = arcpy.sa.CellStatistics(rasters, agg_func, "DATA")
            outCellStats.save(raster_out)
            arcpy.AddMessage(f"Finished aggregating {var} for all years.")
            print(f"Finished aggregating {var} for all years.")
            # Monthly 30-year normals

            rasters = getRastersFromDir(var, mnths, out_path) 
            raster_out = f"{var}_30yr_800m"
            agg_rasters[var].update({"norm":raster_out})
            arcpy.AddMessage(f"Aggregating {var} for all 800m 30 year normal months...")
            print(f"Aggregating {var} for all 800m 30 year normal months...")
            outCellStats = arcpy.sa.CellStatistics(rasters, agg_func, "DATA")
            outCellStats.save(raster_out)
            arcpy.AddMessage(f"Finished aggregating {var} for all 30 year normal months.")
            print(f"Finished aggregating {var} for all 30 year normal months.")

            # Project to coord_sys
            input_4km_proj = f"{agg_rasters[var]['yr']}_projected"
            input_800m_proj = f"{agg_rasters[var]['norm']}_projected"
            arcpy.ProjectRaster_management(agg_rasters[var]["yr"], input_4km_proj, coord_system)
            arcpy.ProjectRaster_management(agg_rasters[var]["norm"], input_800m_proj, coord_system)

            arcpy.Resample_management(
                in_raster=input_4km_proj,
                out_raster=f"resampled_{var}_800m",
                cell_size=f"{800*3.28084} {800*3.28084}", #meters to feet
                resampling_type="BILINEAR"  # You can choose other resampling methods if you prefer
            )
            # Calculate the weights based on the number of years in the datasets
            initial_weight_4km = 3.0
            initial_weight_800m = 3.0 / 30.0
            total_weight = initial_weight_4km + initial_weight_800m
            normalized_weight_4km = initial_weight_4km / total_weight
            normalized_weight_800m = initial_weight_800m / total_weight

            # Combine the rasters using the weighted average
            combined_raster = (arcpy.Raster(f"resampled_{var}_800m") * normalized_weight_4km) + \
                (arcpy.Raster(input_800m_proj) * normalized_weight_800m)

            arcpy.AddMessage(f"Saving final {var} raster to geodatabase...")
            print(f"Saving final {var} raster to geodatabase...")
            out_raster = arcpy.sa.ExtractByMask(combined_raster, nc_boundary)
            out_raster.save(raster)
            arcpy.AddMessage(f"Saved {var} raster successfully!")
            print(f"Saved {var} raster successfully!")

            # Delete unneeded rasters
            for k in agg_rasters.keys():
                for k2 in agg_rasters[k].keys():
                    if agg_rasters[k][k2] in arcpy.ListRasters():
                        arcpy.Delete_management(agg_rasters[k][k2])
            for r in [f"resampled_{var}_800m", input_4km_proj, input_800m_proj]:
                if r in arcpy.ListRasters():
                    arcpy.Delete_management(r)

            arcpy.env.overwriteOutput = False

    return [avg_prec_data, min_temp_data, max_temp_data]