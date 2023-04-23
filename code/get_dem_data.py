# import libraries
import os
import arcpy
import zipfile
import urllib.request

def getDEMData(data_path:str, wspace:str, coord_sys:arcpy.SpatialReference) -> None:
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
        arcpy.management.CopyRaster(os.path.join(dem_path, "nc250"), "nc250_base")

        # Reproject the input raster if the spatial references do not match
        arcpy.ProjectRaster_management("nc250_base", "nc250_projected", coord_sys)

        # Get the mask polygon's extent
        mask_polygon_extent = arcpy.Describe("nc_state_boundary").extent

        # Set the output extent to match the mask polygon's extent
        arcpy.env.extent = mask_polygon_extent

        out_dem = arcpy.sa.ExtractByMask("nc250_projected", "nc_state_boundary")
        out_dem.save("nc250")

        arcpy.env.extent = "MAXOF"

        # Delete unneeded rasters
        for ras in ["nc250_projected", "nc250_base"]:
            arcpy.Delete_management(ras)

    print("Completed retrieval of explanatory DEM")
    arcpy.AddMessage("Completed retrieval of explanatory DEM")