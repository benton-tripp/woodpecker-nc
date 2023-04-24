# Name: Benton Tripp
# unity ID: btripp
###################################################################################
#
# get_land_cover_data.py
#
# This script contains a function to download and process land cover raster data
# for North Carolina from the NCSU GIS library. The land cover data is downloaded,
# resampled to 2 km resolution, reprojected, and clipped to the state boundary.


# import libraries
import os
import arcpy 
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

def getLandCoverData(data_path:str, 
                     wspace:str, 
                     coord_sys:arcpy.SpatialReference,
                     nc_boundary:str,
                     fc_name:str="nc_nlcd2019") -> str:
    """
    Downloads and processes land cover raster data for North Carolina. The land cover
    data is downloaded, resampled to 2 km resolution, reprojected, and clipped to the
    state boundary.
    Args
    - data_path : File path to the data directory.
    - wspace : File path to the working geodatabase.
    - coord_sys : The projected coordinate system to be used for the raster data.
    - nc_boundary : name of NC Boundary layer
    - fc_name : name of new feature layer 
    Output
    New feature layer name
    """
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    print("Getting explanatory Land Cover Rasters...")
    arcpy.AddMessage("Getting explanatory Land Cover Rasters...")
    # Set workspace
    arcpy.env.workspace = wspace

    # Get Raster Data
    # https://www.lib.ncsu.edu/gis/nlcd
    raster_path = os.path.join(data_path, "NC_Land_Cover/")
    if not os.path.isdir(raster_path):
        # 2019 only 
        zipurl = 'https://gisdata.lib.ncsu.edu/fedgov/mrlc/nlcd2019/NC_NLCD2019only.zip'
        print(f"Downloading land cover data from {zipurl}...")
        arcpy.AddMessage(f"Downloading land cover data from {zipurl}...")
        # 2001 - 2019, every 3 years (NOT IN USE)
        # "https://drive.google.com/uc?id=1555Ox4664hH0kFlakGQwi1nzxrMcC61o&confirm=t&uuid=0edbf032-c3ba-45fe-b111-c3752b7cf8ae&at=ALgDtsw-mvJqXBLq4JMNZJ-5g2b7:1676943369421"
        
        # Credit to this method of unzipping a zip file goes to Shyamal Vaderia
        # (see https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/)
        with urlopen(zipurl) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zfile:
                zfile.extractall(raster_path)
        
        if "NC_NLCD2019only.zip" in os.listdir():
            print("NC_NLCD2019only.zip...")
            arcpy.AddMessage("NC_NLCD2019only.zip...")
            os.remove("NC_NLCD2019only.zip")

    if fc_name not in arcpy.ListRasters():
        print("Resampling explanatory rasters to 2k...")
        arcpy.AddMessage("Resampling explanatory rasters to 2k...")
        # Resample cell size of raster(s), save to gdb
        arcpy.management.Resample(os.path.join(raster_path, "nc_nlcd2019"), 
                                f"{fc_name}_Resample_2k", 
                                "2000 2000", 
                                "NEAREST")
        
        # Reproject the input raster if the spatial references do not match
        arcpy.ProjectRaster_management(f"{fc_name}_Resample_2k", f"{fc_name}_projected", coord_sys)

        # Get the mask polygon's extent
        mask_polygon_extent = arcpy.Describe(nc_boundary).extent

        # Set the output extent to match the mask polygon's extent
        arcpy.env.extent = mask_polygon_extent

        out_dem = arcpy.sa.ExtractByMask(f"{fc_name}_projected", nc_boundary)
        out_dem.save(fc_name)

        arcpy.env.extent = "MAXOF"

        # Delete unneeded rasters
        for ras in [f"{fc_name}_projected", f"{fc_name}_Resample_2k"]:
            arcpy.Delete_management(ras)

    print("Completed processing of explanatory rasters")
    arcpy.AddMessage("Completed processing of explanatory rasters")

    return fc_name
