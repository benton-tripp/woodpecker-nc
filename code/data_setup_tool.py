# import libraries/modules
import sys
import os
import arcpy
from get_bird_data import get_species_codes, getFeedWatcherData
from get_explanatory_data import getRasterData, getDEMData
from process_bird_data import batchBirdAnalysis

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
    
    ### Get FeederWatch data #####
   
    # Select 2017 - 2019 (Covered by 2019 Land Cover Raster)
    DATA_TIMEFRAMES = ['2016_2020']
    # All Species
    SPECIES = get_species_codes(data_path=DATA_PATH)
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
    
    # Get raster data; Resample to GDB
    getRasterData(data_path=DATA_PATH, wspace=DB_PATH)
    # Get DEM data; Copy to GDB
    getDEMData(data_path=DATA_PATH, wspace=DB_PATH)

    print("\n=================================\nData setup complete.\n=================================")
    arcpy.AddMessage("\n=================================\nData setup complete.\n=================================")


