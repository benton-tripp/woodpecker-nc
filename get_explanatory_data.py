import urllib.request
import zipfile
import os
import arcpy 

# Get Raster Data
# Credit to https://svaderia.github.io/articles/downloading-and-unzipping-a-zipfile/

# https://www.lib.ncsu.edu/gis/nlcd
if not os.path.isdir('data/NC_Land_Cover/'):
    # 2019 only 
    zipurl = 'https://gisdata.lib.ncsu.edu/fedgov/mrlc/nlcd2019/NC_NLCD2019only.zip'
    # 2001 - 2019, every 3 years (NOT IN USE)
    # "https://drive.google.com/uc?id=1555Ox4664hH0kFlakGQwi1nzxrMcC61o&confirm=t&uuid=0edbf032-c3ba-45fe-b111-c3752b7cf8ae&at=ALgDtsw-mvJqXBLq4JMNZJ-5g2b7:1676943369421"
    with urlopen(zipurl) as zipresp:
        with ZipFile(BytesIO(zipresp.read())) as zfile:
            zfile.extractall('data/NC_Land_Cover')

if 'nc_nlcd2019_Resample_1k' not in arcpy.ListRasters():
    # Resample cell size of raster(s), save to gdb
    arcpy.management.Resample("data/NC_Land_Cover/nc_nlcd2019", 
                            "nc_nlcd2019_Resample_1k", 
                            "1000 1000", 
                            "MAJORITY")

# Connect to NCSU network (on-campus or through VPN)
if "nc250" not in os.listdir("data/DEM"):
    # URL to the North Carolina boundary 250m DEM
    url = "https://gisdata.lib.ncsu.edu/DEM/nc250.zip"
    zip_file_name = "nc250.zip"
    # Download the zip file from the URL
    urllib.request.urlretrieve(url, zip_file_name)
    # Extract the contents of the zip file to a directory named "data/DEM"
    with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
        zip_ref.extractall("data/DEM")
        
if "nc250" not in arcpy.ListRasters():
    arcpy.management.CopyRaster("data/DEM/nc250", "nc250", nodata_value="-3.402823e+38")