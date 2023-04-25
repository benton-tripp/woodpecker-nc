# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# get_dem_data.py
#
# This script downloads, extracts, and processes the 250m Digital Elevation Model (DEM) data for North Carolina.
# The data is sourced from https://gisdata.lib.ncsu.edu/DEM/nc250.zip. The script uses the arcpy library to
# perform geoprocessing tasks, and urllib to download the data. It also uses os and zipfile for file handling.
# Note that the user must be connected to the NCSU network (on-campus or via VPN) if downloading the data for the
# first time.

# Import libraries
import os
import arcpy
import zipfile
import urllib.request

def getDEMData(data_path:str, 
               wspace:str, 
               coord_sys:arcpy.SpatialReference,
               nc_boundary:str,
               fc_name:str="nc250") -> str:
    """
    MUST BE ON NCSU NETWORK (either on-campus or connected to VPN) if the data is being
    downloaded for the first time.

    Downloads the 250m DEM data for North Carolina from https://gisdata.lib.ncsu.edu/DEM/nc250.zip
    if it has not already been downloaded and decompressed within data_path. Then, the 
    raster is added to the workspace with the defined projected coordinate system and within the 
    extent of the nc_boundary.
    Args
    - data_path : A file path to the data directory
    - wspace : A file path to the working directory/GDB
    - coord_sys : The projected coordinate system
    - nc_boundary : A polygon of the state of North Carolina
    Output
    Returns the name of the Feature Layer added to the workspace (by default "nc250")
    """
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    print("Getting explanatory DEM...")
    arcpy.AddMessage("Getting explanatory DEM...")
    # Connect to NCSU network (on-campus or through VPN)
    # Set workspace
    arcpy.env.workspace = wspace
    dem_path = os.path.join(data_path, "DEM/")
    if not os.path.exists(dem_path):
        os.makedirs(dem_path)
    if "nc250" not in os.listdir(dem_path):
        # URL to the North Carolina boundary 250m DEM
        url = "https://gisdata.lib.ncsu.edu/DEM/nc250.zip"
        print(f"Downloading DEM Data from {url}...")
        arcpy.AddMessage(f"Downloading DEM Data from {url}...")
        zip_file_name = "nc250.zip"
        # Extract the contents of the zip file to a directory named `dem_path` (var)
        # Credit to this method of unzipping a zip file goes to Shyamal Vaderia
        # (see blog post at https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/)
        urllib.request.urlretrieve(url, zip_file_name)
        with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
            zip_ref.extractall(dem_path)
        # End Credit
    if "nc250.zip" in os.listdir():
        print("Removing nc250.zip...")
        arcpy.AddMessage("Removing nc250.zip...")
        os.remove("nc250.zip")
            
    if fc_name not in arcpy.ListRasters():
        arcpy.management.CopyRaster(os.path.join(dem_path, "nc250"), f"{fc_name}_base")

        # Reproject the input raster if the spatial references do not match
        arcpy.ProjectRaster_management(f"{fc_name}_base", f"{fc_name}_projected", coord_sys)

        # Get the mask polygon's extent
        mask_polygon_extent = arcpy.Describe(nc_boundary).extent

        # Set the output extent to match the mask polygon's extent
        arcpy.env.extent = mask_polygon_extent

        out_dem = arcpy.sa.ExtractByMask(f"{fc_name}_projected", nc_boundary)
        out_dem.save(fc_name)

        arcpy.env.extent = "MAXOF"

        # Delete unneeded rasters
        for ras in [f"{fc_name}_projected", f"{fc_name}_base"]:
            arcpy.Delete_management(ras)

    print("Completed retrieval of explanatory DEM")
    arcpy.AddMessage("Completed retrieval of explanatory DEM")
    return fc_name