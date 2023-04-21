# import libraries
import sys
import os
import arcpy
from get_bird_data import getSpeciesCodes, getFeedWatcherData
from get_dem_data import getDEMData
from get_land_cover_data import getLandCoverData
from get_weather_data import getWeatherData
from process_bird_data import batchBirdAnalysis
from presence_only import batchMaxEnt


# Define variables 
PROJ_PATH = sys.argv[1]
try:
    proj = arcpy.mp.ArcGISProject(PROJ_PATH)
except:
    print("Error: Please ensure you entered the correct path to the ArcGIS Project.")
    sys.exit()

PROJ_PATH = os.path.dirname(proj.filePath) # ./
DB_PATH = proj.defaultGeodatabase # "woodpeckersNC.gdb"
DATA_PATH = os.path.join(PROJ_PATH, "data") # ./data
_PREFIX = "FW_"
_SUFFIX = "woodpeckers_NC"
BASE_FC = f"{_PREFIX}{_SUFFIX}" # "FW_woodpeckers_NC"
FW_FILE = f"{BASE_FC}.csv" # "FW_woodpeckers_NC.csv"

if __name__ == "__main__":
    ### Set up environment #####
    print(f"Setting up environment in {PROJ_PATH}...")
    # Create File Geodatabase
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    if not os.path.exists(os.path.join(DATA_PATH, DB_PATH)):
        arcpy.CreateFileGDB_management(DATA_PATH, DB_PATH)
    arcpy.env.workspace = os.path.join(DATA_PATH, DB_PATH)
    print(f"Workspace set to {os.path.join(DATA_PATH, DB_PATH)}")
    # Existing Feature Classes
    existing_fcs = arcpy.ListFeatureClasses()
    # Projected Coordinate System
    coord_system = arcpy.SpatialReference("NAD 1983 StatePlane North Carolina FIPS 3200 (US Feet)")

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
    batchBirdAnalysis(fw_file=FW_FILE, 
                    base_fc=BASE_FC,
                    existing_fcs=existing_fcs, 
                    out_coordinate_system=coord_system,
                    data_path=DATA_PATH,
                    fw_df=fw,
                    species_df=WOODPECKERS,
                    _prefix=_PREFIX)
    
    # Get land cover raster data; Resample to GDB
    getLandCoverData(data_path=DATA_PATH, wspace=DB_PATH)
    # Get DEM data; Copy to GDB
    getDEMData(data_path=DATA_PATH, wspace=DB_PATH)
    # Get Weather raster data; Aggregate in GDB
    getWeatherData(data_path=DATA_PATH, wspace=DB_PATH, coord_sys=coord_system)

    # pdb.set_trace()
    ### Analyze ###
    NC_WOODPECKERS = WOODPECKERS.loc[WOODPECKERS.species_name.isin(fw.species_name.unique())]

    batchMaxEnt(species_df=NC_WOODPECKERS, wspace=DB_PATH, data_path=DATA_PATH)

    print("Finished running woodpeckers_nc.py")
