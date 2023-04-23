import urllib.request
import os
import arcpy 
import zipfile

def getNCBoundary(data_path:str, wspace:str, coord_sys:arcpy.SpatialReference) -> None:

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
    if "nc_state_boundary" not in arcpy.ListFeatureClasses():
        arcpy.AddMessage("NC State Boundary download completed. Adding to geodatabase...")
        print("NC State Boundary download completed. Adding to geodatabase...")
        arcpy.management.Dissolve(nc_shp_file , "nc_state_boundary_dissolved", None, None, 
                                  "SINGLE_PART", "DISSOLVE_LINES")
        arcpy.Project_management("nc_state_boundary_dissolved", "nc_state_boundary", coord_sys)
        arcpy.Delete_management("nc_state_boundary_dissolved")
        arcpy.AddMessage(f"Finished adding boundary to geodatabase.")
        print("Finished adding boundary to geodatabase.")