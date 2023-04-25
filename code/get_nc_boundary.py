# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# get_nc_boundary.py
#
# This script downloads the North Carolina state boundary shapefile from the US Census Bureau's TIGER/Line dataset,
# extracts the shapefile, adds it to a geodatabase, dissolves the polygons into a single polygon, and projects it 
# to a specified coordinate system. The script uses the arcpy library to perform geoprocessing tasks and urllib 
# to download the shapefile. It also uses os and zipfile for file handling.

# Import libraries
import urllib.request
import os
import arcpy 
import zipfile

def getNCBoundary(data_path:str, 
                  wspace:str, 
                  coord_sys:arcpy.SpatialReference,
                  fc_name:str="nc_state_boundary") -> str:
    """
    Downloads, extracts, and processes the North Carolina state boundary shapefile.
    Downloads the shapefile from the US Census Bureau's TIGER/Line dataset, adds it to a geodatabase, 
    dissolves the polygons into a single polygon, and projects it to the specified coordinate system.
    Args
    - data_path : The path to the directory where the data will be downloaded.
    - wspace : The workspace where the feature class will be added.
    - coord_sys : The coordinate system to project the boundary feature class.
    - fc_name : The name of the output feature class. Defaults to "nc_state_boundary".
    Output
    The name of the output feature class.
    """
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    # Set workspace
    arcpy.env.workspace = wspace

    # Get NC Boundary Shape File if not downloaded
    nc_shp_path = os.path.join(data_path, "nc_state_boundary")
    nc_shp_file = os.path.join(nc_shp_path, "tl_2018_37_cousub.shp")
    os.makedirs(nc_shp_path, exist_ok=True)
    if not os.path.exists(nc_shp_file):
        nc_shp_url = "https://www2.census.gov/geo/tiger/TIGER2018/COUSUB/tl_2018_37_cousub.zip"
        arcpy.AddMessage(f"Downloading NC State Boundary shapefile from {nc_shp_url}...")
        print(f"Downloading NC State Boundary shapefile from {nc_shp_url}...")
        nc_out = os.path.join(nc_shp_path, "nc_state_boundary.zip")
        urllib.request.urlretrieve(nc_shp_url, nc_out)
        with zipfile.ZipFile(nc_out, "r") as zfile:
            zfile.extractall(nc_shp_path)
        os.remove(nc_out)

    # Add to GDB if needed
    if fc_name not in arcpy.ListFeatureClasses():
        arcpy.AddMessage("NC State Boundary download completed. Adding to geodatabase...")
        print("NC State Boundary download completed. Adding to geodatabase...")
        arcpy.management.Dissolve(nc_shp_file , f"{fc_name}_dissolved", None, None, 
                                  "SINGLE_PART", "DISSOLVE_LINES")
        arcpy.Project_management(f"{fc_name}_dissolved", f"{fc_name}", coord_sys)
        arcpy.Delete_management(f"{fc_name}_dissolved")
        arcpy.AddMessage(f"Finished adding boundary to geodatabase.")
        print("Finished adding boundary to geodatabase.")

    return fc_name