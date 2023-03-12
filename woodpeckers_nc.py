# import libraries
import sys
import os
import arcpy
from get_bird_data import get_species_codes, getFeedWatcherData
from get_explanatory_data import getRasterData, getDEMData
from process_bird_data import batchBirdAnalysis
from presence_only import batchMaxEnt

# Define Globals; Setup
PROJ_PATH = sys.argv[1]
DB_PATH = "fw_GDB.gdb"
DATA_PATH = os.path.join(PROJ_PATH, "data")
FW_FILE = "FW_woodpeckers_NC.csv"
BASE_FC = "FW_woodpeckers_NC"

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
    SPECIES = get_species_codes(data_path=DATA_PATH)
    # Woodpecker Family
    WOODPECKERS = SPECIES.loc[SPECIES['family'] == 'Picidae (Woodpeckers)']

    fw = getFeedWatcherData(outfile="FW_woodpeckers_NC.csv",
                            tfs=DATA_TIMEFRAMES,
                            birds=WOODPECKERS,
                            sub_national_code=['US-NC'],
                            out_dir=DATA_PATH,
                            file_suffix='woodpeckers_NC',
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
                      species_df=WOODPECKERS)
    
    # Get raster data; Resample to GDB
    getRasterData(data_path=DATA_PATH, wspace=os.path.join(DATA_PATH, DB_PATH))
    # Get DEM data; Copy to GDB
    getDEMData(data_path=DATA_PATH, wspace=os.path.join(DATA_PATH, DB_PATH))

    ### Analyze ###
    batchMaxEnt()

    print("Finished running woodpeckers_nc.py")
