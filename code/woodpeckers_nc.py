# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# woodpeckers_nc.py

# Analyzes woodpecker species data in North Carolina
# 1. Import necessary libraries and modules
# 2. Define variables and set up the working environment
# 3. Retrieve North Carolina boundary data
# 4. Get FeederWatch data (bird observations) for woodpecker species in North Carolina
# 5. Process the data and set up a geodatabase
# 6. Retrieve land cover, DEM, and weather data (explanatory variables)
# 7. Analyze the data using MaxEnt (maximum entropy modeling) for each woodpecker species
# 8. Output trained rasters to map layers; Export PDFs of each layer
#
# Example:
# your/working/directory/woodpeckerNC$ python code/woodpeckers_nc.py woodpeckerNC.aprx
# >>> Setting up environment your/working/directory/woodpeckerNC...
# >>> Workspace set to woodpeckersNC.gdb...
# >>> ... <other output from modules called confirming success/failure> ...
# >>> Finished running woodpeckers_nc.py

# import libraries
import sys
import os
import arcpy
from get_bird_data import getSpeciesCodes, getFeederWatchData
from get_nc_boundary import getNCBoundary
from get_dem_data import getDEMData
from get_land_cover_data import getLandCoverData
from get_weather_data import getWeatherData
from process_bird_data import batchBirdProcessing
from presence_only import batchMaxEnt
from presence_only_mapping import outputMaxEntMaps

# Define variables 
try:
    PROJ_PATH = os.path.abspath(sys.argv[1])
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
    arcpy.env.workspace = DB_PATH
    print(f"Workspace set to {DB_PATH}")
    # Existing Feature Classes
    existing_fcs = arcpy.ListFeatureClasses()
    # Projected Coordinate System
    coord_system = arcpy.SpatialReference("NAD 1983 StatePlane North Carolina FIPS 3200 (US Feet)")
    # coord_system = arcpy.SpatialReference().loadFromString('PROJCS["NAD_1983_StatePlane_North_Carolina_FIPS_3200_Feet",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",2000000.002616666],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-79.0],PARAMETER["Standard_Parallel_1",34.33333333333334],PARAMETER["Standard_Parallel_2",36.16666666666666],PARAMETER["Latitude_Of_Origin",33.75],UNIT["Foot_US",0.3048006096012192]]')

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

    fw = getFeederWatchData(outfile=FW_FILE,
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

    ### Analyze ###

    NC_WOODPECKERS = WOODPECKERS.loc[WOODPECKERS.species_name.isin(fw.species_name.unique())]
    explanatory_data = [land_cover_data, dem_data, avg_prec_data, min_temp_data, max_temp_data]
    explanatory_rasters = [[dat, "true" if dat == land_cover_data else "false"] for dat in explanatory_data]

    batchMaxEnt(species_df=NC_WOODPECKERS, 
                wspace=DB_PATH, 
                data_path=DATA_PATH, 
                explanatory_rasters=explanatory_rasters,
                nc_boundary=nc_boundary)
    
    ### Mapping ##########

    outputMaxEntMaps(species_df=NC_WOODPECKERS, 
                     project_path=os.path.abspath(sys.argv[1]), 
                     wspace=DB_PATH, 
                     data_path=DATA_PATH, 
                     output_folder=os.path.join(DATA_PATH, "maps"),
                     tool_script=False)

    print("Finished running woodpeckers_nc.py")
