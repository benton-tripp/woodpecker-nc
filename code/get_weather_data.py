import urllib.request
import os
import arcpy 
import zipfile

def getWeatherData(data_path:str, wspace:str, coord_sys:arcpy.SpatialReference) -> None:
    # Set workspace
    arcpy.env.workspace = wspace

    vars = ["ppt", "tmax", "tmin"]
    yrs = [2017, 2018, 2019]
    pairs = list()
    pairs = [(v, y) for v in vars for y in yrs if (v, y) not in pairs]

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
        arcpy.management.Dissolve(nc_shp_file , "nc_state_boundary", None, None, 
                                  "SINGLE_PART", "DISSOLVE_LINES")
        arcpy.management.DefineProjection("nc_state_boundary", coord_sys)
        arcpy.AddMessage(f"Finished adding boundary to geodatabase.")
        print("Finished adding boundary to geodatabase.")

    # Get Raster Data
    # Credit to https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/
    arcpy.AddMessage("Getting explanatory Weather Rasters...")
    print("Getting explanatory Weather Rasters...")
    # https://www.prism.oregonstate.edu/documents/PRISM_downloads_web_service.pdf
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
            with zipfile.ZipFile(dwnld_out, "r") as zfile:
                zfile.extractall(dwnld_path)
            arcpy.AddMessage(f"Extracted {v}/{y} from {dwnld_out} to {dwnld_path}")
            print(f"Extracted {v}/{y} from {dwnld_out} to {dwnld_path}")
            os.remove(dwnld_out)
        
        # Trim to be only NC
        v_y_fc = f"{v}_{y}_weather_raster"
        if not v_y_fc in arcpy.ListRasters():
            arcpy.AddMessage(f"Saving {v_y_fc} raster to geodatabase...")
            print(f"Saving {v_y_fc} raster to geodatabase...")
            arcpy.env.workspace = dwnld_path
            raster = os.path.join(dwnld_path, arcpy.ListRasters()[0])
            arcpy.env.workspace = wspace
            out_raster = arcpy.sa.ExtractByMask(raster, "nc_state_boundary")
            out_raster.save(v_y_fc)
            arcpy.AddMessage(f"Saved {v_y_fc} successfully!")
            print(f"Saved {v_y_fc} successfully!")

    # Average with other years of same var type
    for var in vars:
        rasters = [f"{var}_{yr}_weather_raster" for yr in yrs]
        if var == "tmax":
            raster_out = "maxTemp_all_years"
            agg_func = "MAXIMUM"
        elif var == "tmin":
            raster_out = "minTemp_all_years"
            agg_func = "MINIMUM"
        elif var == "ppt":
            raster_out = "avgPrecip_all_years"
            agg_func = "MEAN"
        if not raster_out in arcpy.ListRasters():
                arcpy.AddMessage(f"Aggregating {var} for all years...")
                print(f"Aggregating {var} for all years...")
                outCellStats = arcpy.sa.CellStatistics(rasters, agg_func, "DATA")
                outCellStats.save(raster_out)
                arcpy.AddMessage(f"Finished.")
                print(f"Finished.")