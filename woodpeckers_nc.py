# import libraries
import pandas as pd
import numpy as np
import os
import arcpy
import re 
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile
from get_bird_data import get_species_codes, getFeedWatcherData
from process_bird_data import batch_bird_analysis

# Define Globals; Setup
PROJ_PATH = sys.argv[1]
DB_PATH = "fw_GDB.gdb"
DATA_PATH = os.path.join(PROJ_PATH, "data")
FW_FILE = "FW_woodpeckers_NC.csv"
BASE_FC = "FW_woodpeckers_NC"

if __name__ == "__main__":
    ### Set up environment #####

    # Create File Geodatabase
    if not os.path.exists(os.path.join(PROJ_PATH, DB_PATH)):
        arcpy.CreateFileGDB_management(PROJ_PATH, DB_PATH)
    arcpy.env.workspace = os.path.join(PROJ_PATH, DB_PATH)
    # Existing Feature Classes
    existing_fcs = arcpy.ListFeatureClasses()
    # Projected Coordinate System
    coord_system = arcpy.SpatialReference("NAD 1983 StatePlane North Carolina FIPS 3200 (US Feet)")

    ### Get data #####

    # Select 2017 - 2019 (Covered by 2019 Land Cover Raster)
    DATA_TIMEFRAMES = ['2016_2020']
    # All Species
    SPECIES = get_species_codes()
    # Woodpecker Family
    WOODPECKERS = SPECIES.loc[SPECIES['family'] == 'Picidae (Woodpeckers)']

    fw = getFeedWatcherData(outfile="FW_woodpeckers_NC.csv",
                            tfs=DATA_TIMEFRAMES,
                            birds=WOODPECKERS,
                            sub_national_code=['US-NC'],
                            out_dir='data',
                            file_suffix='woodpeckers_NC',
                            save_=True)
    
    ### Process Data and Analyze #####

    # Batch process by species type, for woodpecker family in NC
    batch_bird_analysis(fw_file=FW_FILE, 
                        base_fc=BASE_FC,
                        existing_fcs=existing_fcs, 
                        out_coordinate_system=coord_system,
                        data_path=DATA_PATH,
                        fw_df=fw,
                        species_df=woodpeckers)
