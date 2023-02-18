# import libraries
import sys
import os
import arcpy
from get_bird_data import get_species_codes, get_fw_data
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

    # Timeframes available in FeederWatch
    data_timeframes = ['1988_1995', '1996_2000', '2001_2005', 
                    '2006_2010', '2011_2015', '2016_2020', 
                    '2021']
    # All Species
    species = get_species_codes()
    # Woodpecker Family
    woodpeckers = species.loc[species['family'] == 'Picidae (Woodpeckers)']
    # Get FW data for NC woodpeckers
    # Data from https://feederwatch.org/explore/raw-dataset-requests/
    fw = get_fw_data(outfile="FW_woodpeckers_NC.csv",
                     tfs=data_timeframes,
                     birds=woodpeckers,
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
