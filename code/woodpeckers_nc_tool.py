# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# woodpeckers_nc_tool.py

# Script tool (can be run via ArcGIS Pro GUI) that prepares NC Woodpecker data 
# for Presence Only Prediction, and runs a grid search to find the best model
# for each woodpecker species
# 
# 1. Import necessary libraries and modules
# 2. Define variables and set up the working environment
# 3. Retrieve North Carolina boundary data
# 4. Get FeederWatch data (bird observations) for woodpecker species in North Carolina
# 5. Process the data and set up a geodatabase
# 6. Retrieve land cover, DEM, and weather data (explanatory variables)
# 7. Run grid-search to train models with given inputs


# import libraries/modules
import sys
import os
import arcpy
from get_bird_data import getSpeciesCodes, getFeedWatcherData
from get_nc_boundary import getNCBoundary
from get_dem_data import getDEMData
from get_land_cover_data import getLandCoverData
from get_weather_data import getWeatherData
from process_bird_data import batchBirdProcessing
from presence_only import batchMaxEnt

# Define variables 
proj = arcpy.mp.ArcGISProject('CURRENT')
PROJ_PATH = os.path.dirname(proj.filePath) # ./
DB_PATH = proj.defaultGeodatabase # "woodpeckersNC.gdb"
DATA_PATH = os.path.join(PROJ_PATH, "data") # ./data
_PREFIX = "FW_"
_SUFFIX = "woodpeckers_NC"
BASE_FC = f"{_PREFIX}{_SUFFIX}" # "FW_woodpeckers_NC"
FW_FILE = f"{BASE_FC}.csv" # "FW_woodpeckers_NC.csv"

PARAMETER_GRID = {
                    "number_of_iterations": [sys.argv[1]],
                    "basis_expansion_functions": sys.argv[2],
                    "relative_weight": sys.argv[3],
                    "number_knots": sys.argv[4], 
                    "spatial_thinning": sys.argv[5],
                    "link_function": sys.argv[6], 
                    "thinning_distance_band": f"{sys.argv[7]} meters"
                }

PDF_OUTPUT_LOCATION = sys.argv[8]

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
    arcpy.env.workspace = DB_PATH
    print(f"Workspace set to {DB_PATH}")
    arcpy.AddMessage(f"Workspace set to {DB_PATH}...")
    # Existing Feature Classes
    existing_fcs = arcpy.ListFeatureClasses()
    # Projected Coordinate System
    coord_system = arcpy.SpatialReference("NAD 1983 StatePlane North Carolina FIPS 3200 (US Feet)")
    
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
                        wspace=DB_PATH,
                        fw_df=fw,
                        species_df=WOODPECKERS,
                        _prefix=_PREFIX,
                        nc_boundary=nc_boundary)
    
    # Get land cover raster data; Resample to GDB
    land_cover_data = getLandCoverData(data_path=DATA_PATH, 
                                       wspace=DB_PATH, 
                                       coord_sys=coord_system,
                                       nc_boundary=nc_boundary)
    # Get DEM data; Copy to GDB
    dem_data = getDEMData(data_path=DATA_PATH, 
                          wspace=DB_PATH, 
                          coord_sys=coord_system, 
                          nc_boundary=nc_boundary)
    
    # Get Weather raster data; Aggregate in GDB
    avg_prec_data, min_temp_data, max_temp_data = getWeatherData(data_path=DATA_PATH, 
                                                                 wspace=DB_PATH,
                                                                 nc_boundary=nc_boundary,
                                                                 coord_system=coord_system)

    print("\n=================================\nData setup complete.\n=================================")
    arcpy.AddMessage("\n=================================\nData setup complete.\n=================================")

    ### Analyze ###

    NC_WOODPECKERS = WOODPECKERS.loc[WOODPECKERS.species_name.isin(fw.species_name.unique())]
    explanatory_data = [land_cover_data, dem_data, avg_prec_data, min_temp_data, max_temp_data]
    explanatory_rasters = [[dat, "true" if dat == land_cover_data else "false"] for dat in explanatory_data]

    msg_str = """
    Beginning grid-search with the input features. Note that if a previously trained model is found to perform
    better than any of the models attempted in this search, that model will be selected unless the logged data
    is deleted prior to this tool being run.
    """
    print(msg_str)
    arcpy.AddMessage(msg_str)

    batchMaxEnt(species_df=NC_WOODPECKERS, 
                wspace=DB_PATH, 
                data_path=DATA_PATH, 
                explanatory_rasters=explanatory_rasters,
                nc_boundary=nc_boundary,
                parameter_grid=PARAMETER_GRID)

