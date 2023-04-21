# import libraries
import os
import arcpy 
from urllib.request import urlopen
import zipfile
import urllib.request

def getDEMData(data_path:str, wspace:str) -> None:
    """
    MUST BE ON NCSU NETWORK (either on-campus or connected to VPN)
    """
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
        # Download the zip file from the URL
        urllib.request.urlretrieve(url, zip_file_name)
        # Extract the contents of the zip file to a directory named `dem_path` (var)
        with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
            zip_ref.extractall(dem_path)
    
    if "nc250.zip" in os.listdir():
        print("Removing nc250.zip...")
        arcpy.AddMessage("Removing nc250.zip...")
        os.remove("nc250.zip")
            
    if "nc250" not in arcpy.ListRasters():
        arcpy.management.CopyRaster(os.path.join(dem_path, "nc250"), "nc250")
    print("Completed retrieval of explanatory DEM")
    arcpy.AddMessage("Completed retrieval of explanatory DEM")