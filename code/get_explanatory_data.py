# import libraries
import os
import arcpy 
from io import BytesIO
from urllib.request import urlopen
import zipfile
from zipfile import ZipFile
import urllib.request

def getRasterData(data_path:str, wspace:str) -> None:
    print("Getting explanatory Rasters...")
    arcpy.AddMessage("Getting explanatory Rasters...")
    # Set workspace
    arcpy.env.workspace = wspace

    # Get Raster Data
    # Credit to https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/

    # https://www.lib.ncsu.edu/gis/nlcd
    raster_path = os.path.join(data_path, "NC_Land_Cover/")
    if not os.path.isdir(raster_path):
        # 2019 only 
        zipurl = 'https://gisdata.lib.ncsu.edu/fedgov/mrlc/nlcd2019/NC_NLCD2019only.zip'
        # 2001 - 2019, every 3 years (NOT IN USE)
        # "https://drive.google.com/uc?id=1555Ox4664hH0kFlakGQwi1nzxrMcC61o&confirm=t&uuid=0edbf032-c3ba-45fe-b111-c3752b7cf8ae&at=ALgDtsw-mvJqXBLq4JMNZJ-5g2b7:1676943369421"
        with urlopen(zipurl) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zfile:
                zfile.extractall(raster_path)
        
        if "NC_NLCD2019only.zip" in os.listdir():
            print("NC_NLCD2019only.zip...")
            arcpy.AddMessage("NC_NLCD2019only.zip...")
            os.remove("NC_NLCD2019only.zip")

    if 'nc_nlcd2019_Resample_1k' not in arcpy.ListRasters():
        print("Resampling explanatory rasters to 1k...")
        arcpy.AddMessage("Resampling explanatory rasters to 1k...")
        # Resample cell size of raster(s), save to gdb
        arcpy.management.Resample(os.path.join(raster_path, "nc_nlcd2019"), 
                                "nc_nlcd2019_Resample_1k", 
                                "1000 1000", 
                                "MAJORITY")
    print("Completed processing of explanatory rasters")
    arcpy.AddMessage("Completed processing of explanatory rasters")

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
        arcpy.management.CopyRaster(os.path.join(dem_path, "nc250"), 
                                    "nc250", 
                                    nodata_value="-3.402823e+38")
    print("Completed retrieval of explanatory DEM")
    arcpy.AddMessage("Completed retrieval of explanatory DEM")