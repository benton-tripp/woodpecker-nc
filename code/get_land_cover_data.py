# import libraries
import os
import arcpy 
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

def getLandCoverData(data_path:str, wspace:str) -> None:
    print("Getting explanatory Land Cover Rasters...")
    arcpy.AddMessage("Getting explanatory Land Cover Rasters...")
    # Set workspace
    arcpy.env.workspace = wspace

    # Get Raster Data
    # Credit to https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/

    # https://www.lib.ncsu.edu/gis/nlcd
    raster_path = os.path.join(data_path, "NC_Land_Cover/")
    if not os.path.isdir(raster_path):
        # 2019 only 
        zipurl = 'https://gisdata.lib.ncsu.edu/fedgov/mrlc/nlcd2019/NC_NLCD2019only.zip'
        print(f"Downloading land cover data from {zipurl}...")
        arcpy.AddMessage(f"Downloading land cover data from {zipurl}...")
        # 2001 - 2019, every 3 years (NOT IN USE)
        # "https://drive.google.com/uc?id=1555Ox4664hH0kFlakGQwi1nzxrMcC61o&confirm=t&uuid=0edbf032-c3ba-45fe-b111-c3752b7cf8ae&at=ALgDtsw-mvJqXBLq4JMNZJ-5g2b7:1676943369421"
        with urlopen(zipurl) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zfile:
                zfile.extractall(raster_path)
        
        if "NC_NLCD2019only.zip" in os.listdir():
            print("NC_NLCD2019only.zip...")
            arcpy.AddMessage("NC_NLCD2019only.zip...")
            os.remove("NC_NLCD2019only.zip")

    if 'nc_nlcd2019_Resample_2k' not in arcpy.ListRasters():
        print("Resampling explanatory rasters to 2k...")
        arcpy.AddMessage("Resampling explanatory rasters to 2k...")
        # Resample cell size of raster(s), save to gdb
        arcpy.management.Resample(os.path.join(raster_path, "nc_nlcd2019"), 
                                "nc_nlcd2019_Resample_2k", 
                                "2000 2000", 
                                "NEAREST")
    print("Completed processing of explanatory rasters")
    arcpy.AddMessage("Completed processing of explanatory rasters")
