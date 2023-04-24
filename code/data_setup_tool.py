# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# data_setup_tool.py

# Script tool (can be run via ArcGIS Pro GUI) that prepares NC Woodpecker data 
# for Presence Only Prediction
# 
# 1. Import necessary libraries and modules
# 2. Define variables and set up the working environment
# 3. Retrieve North Carolina boundary data
# 4. Get FeederWatch data (bird observations) for woodpecker species in North Carolina
# 5. Process the data and set up a geodatabase
# 6. Retrieve land cover, DEM, and weather data (explanatory variables)


# import libraries/modules
import sys
import os
import arcpy
from get_bird_data import getSpeciesCodes, getFeedWatcherData
from get_dem_data import getDEMData
from get_land_cover_data import getLandCoverData
from get_weather_data import getWeatherData
from process_bird_data import batchBirdProcessing

# Define variables 
proj = arcpy.mp.ArcGISProject('CURRENT')
PROJ_PATH = os.path.dirname(proj.filePath) # ./
DB_PATH = proj.defaultGeodatabase # "woodpeckersNC.gdb"
DATA_PATH = os.path.join(PROJ_PATH, "data") # ./data
_PREFIX = sys.argv[1] # "FW_"
_SUFFIX = sys.argv[2] # "woodpeckers_NC"
COORD_SYS = sys.argv[3] # "NAD 1983 StatePlane North Carolina FIPS 3200 (US Feet)"
BASE_FC = f"{_PREFIX}{_SUFFIX}" # "FW_woodpeckers_NC"
FW_FILE = f"{BASE_FC}.csv" # "FW_woodpeckers_NC.csv"

if __name__ == "__main__":
    print("\n=================================\nStarting data setup...\n=================================")
    arcpy.AddMessage("\n=================================\nStarting data setup...\n=================================")
    ### Set up environment #####
    print(f"Setting up environment in {PROJ_PATH}...")
    arcpy.AddMessage(f"Setting up environment in {PROJ_PATH}...")
    # Create File Geodatabase
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    if not os.path.exists(DB_PATH):
        arcpy.CreateFileGDB_management(DB_PATH)
    arcpy.env.workspace = os.path.join(DB_PATH)
    print(f"Workspace set to {DB_PATH}")
    arcpy.AddMessage(f"Workspace set to {DB_PATH}...")
    # Existing Feature Classes
    existing_fcs = arcpy.ListFeatureClasses()
    # Projected Coordinate System
    try:
        coord_system = arcpy.SpatialReference(COORD_SYS)
    except:
        coord_system = arcpy.SpatialReference()
        coord_system.loadFromString(COORD_SYS)
    
    ### Get NC Boundary ##########
    nc_boundary = getNCBoundary(data_path=DATA_PATH, 
                                wspace=DB_PATH, 
                                coord_sys=coord_system)
    
    ### Get FeederWatch data #####
   
    # Select 2017 - 2019 (Covered by 2019 Land Cover Raster)
    DATA_TIMEFRAMES = ['2016_2020']
    # All Species
    SPECIES = getSpeciesCodes(data_path=DATA_PATH)
    # Woodpecker Family
    WOODPECKERS = SPECIES.loc[SPECIES['family'] == 'Picidae (Woodpeckers)']

    fw = getFeedWatcherData(outfile=FW_FILE,
                            tfs=DATA_TIMEFRAMES,
                            birds=WOODPECKERS,
                            sub_national_code=['US-NC'],
                            out_dir=DATA_PATH,
                            file_suffix=_SUFFIX,
                            save_=True,
                            min_year=2017,
                            max_year=2019)
    
    ### Process Data (including explanatory variables); set up GDB #####

    # Batch process by species type, for woodpecker family in NC
    batchBirdProcessing(fw_file=FW_FILE, 
                        base_fc=BASE_FC,
                        existing_fcs=existing_fcs, 
                        out_coordinate_system=coord_system,
                        data_path=DATA_PATH,
                        fw_df=fw,
                        species_df=WOODPECKERS,
                        _prefix=_PREFIX,
                        nc_boundary=nc_boundary)
    
    # Get land cover raster data; Resample to GDB
    getLandCoverData(data_path=DATA_PATH, 
                     wspace=DB_PATH, 
                     coord_sys=coord_system,
                     nc_boundary=nc_boundary)
    # Get DEM data; Copy to GDB
    getDEMData(data_path=DATA_PATH, 
               wspace=DB_PATH, 
               coord_sys=coord_system, 
               nc_boundary=nc_boundary)
    
    # Get Weather raster data; Aggregate in GDB
    getWeatherData(data_path=DATA_PATH, 
                   wspace=DB_PATH,
                   nc_boundary=nc_boundary)

    print("\n=================================\nData setup complete.\n=================================")
    arcpy.AddMessage("\n=================================\nData setup complete.\n=================================")


