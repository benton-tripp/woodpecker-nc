import urllib.request
import os
import arcpy 
import zipfile

def getWeatherData(data_path:str, wspace:str) -> None:
    print("Getting explanatory Weather Rasters...")
    # Set workspace
    arcpy.env.workspace = wspace

    vars = ["ppt", "tmax", "tmin"]
    yrs = [2017, 2018, 2019]
    pairs = list()
    pairs = [(v, y) for v in vars for y in yrs if (v, y) not in pairs]

    # Get Raster Data
    # Credit to https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/

    # https://www.prism.oregonstate.edu/documents/PRISM_downloads_web_service.pdf
    out_path = os.path.join(data_path, "weather/")
    os.makedirs(out_path, exist_ok=True)
    for v, y in pairs:
        dwnld_out = os.path.join(out_path, f"{v}_{y}.zip")
        dwnld_path = os.path.join(out_path, f"{v}_{y}")
        if not os.path.exists(dwnld_path):
            url = f"https://services.nacse.org/prism/data/public/4km/{v}/{y}" 
            print(url)
            urllib.request.urlretrieve(url, dwnld_out)
            print(f"Saved {v}/{y} to {dwnld_out}")
            with zipfile.ZipFile(dwnld_out, "r") as zfile:
                zfile.extractall(dwnld_path)
            print(f"Extracted {v}/{y} from {dwnld_out} to {dwnld_path}")
            os.remove(dwnld_out)
        
        #' TODO:
        #' 1) Trim to be only NC
        #' 2) Average with other years of same var type

    

getWeatherData(data_path="C:/gispy/final_project/data", 
              wspace="C:/gispy/final_project/data/woodpeckersNC.gdb")

