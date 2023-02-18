# import libraries
import pandas as pd
import os
import arcpy
from final_project.birds import Bird

# Define Globals; Setup
PROJ_PATH = "C:/Users/bento/OneDrive/code_and_data/ncsu-mgist/courses/gis_540/final_project"
DB_PATH = "fw_GDB.gdb"
# Create File Geodatabase
if not os.path.exists(os.path.join(PROJ_PATH, DB_PATH)):
    arcpy.CreateFileGDB_management(PROJ_PATH, DB_PATH)
arcpy.env.workspace = os.path.join(PROJ_PATH, DB_PATH)
DATA_PATH = os.path.join(PROJ_PATH, "data")
FW_FILE = "FW_woodpeckers_NC.csv"
BASE_FC = "FW_woodpeckers_NC"
EXISTING_FCS = arcpy.ListFeatureClasses()
# Projected Coordinate System
COORD_SYSTEM = arcpy.SpatialReference("NAD 1983 StatePlane North Carolina FIPS 3200 (US Feet)")

def batch_bird_analysis(fw_file:str, 
                        base_fc:str,
                        existing_fcs:list,
                        out_coordinate_system:arcpy.SpatialReference, 
                        data_path:str,
                        fw_df:pd.DataFrame,
                        species_df:pd.DataFrame) -> None:
    """
    Batch processing and analysis of FeederWatch bird data. 
    Steps:
    1) Creates Feature Class from .csv file in file Geodatabase
    2) Adds projection, saving to new Feature Class
    3) Filters Projected Feature Class by species, saving individual
       species to their own Feature Classes in the database
    4) Creates Space-Time-Cube for each species. Note that this might
       fail if there is insufficient data (< 60 records). If this is
       the case, the remaining steps will be skipped for this species
    5) Creates 3D Visualizaton
    6) Identifies Outliers
    7) Computes time series clustering analysis
    Args: 
    - fw_file: FeederWatch data .csv file
    - base_fc: Base Feature Class name
    - existing_fcs: List of existing Feature Classes already saved to the 
      database (if they already exist, they will be skipped during batch
      processing)
    - out_coordinate_system: Projected coordinate system
    - data_path: Path to save space-time-cubes
    - fw_df: FeederWatch dataframe
    - species_df: Species dataframe
    """
    # Create base feature class
    if base_fc not in existing_fcs:
        arcpy.management.XYTableToPoint(in_table=os.path.join(data_path, fw_file),
                                        out_feature_class=base_fc,
                                        x_field="longitude", 
                                        y_field="latitude")
    # Add projection to base FC
    if f"{base_fc}_projected" not in existing_fcs:
        arcpy.management.Project(base_fc, 
                                f"{base_fc}_projected", 
                                out_coordinate_system)
    # Add to GDB by species
    for species_name in fw_df.species_name.unique():
        brd = Bird(dataframe=species_df, bird_name=species_name)
        if brd.fc_name not in existing_fcs:
            print(f'Adding {brd.name} to gdb...')
            arcpy.analysis.Select(f"{base_fc}_projected", 
                                brd.fc_name, 
                                f"species_name = '{brd.name}'")
        # Create Space-Time-Cube (.nc file)
        if f"{brd.fc_name}.nc" not in os.listdir(data_path):
            try:
            # https://pro.arcgis.com/en/pro-app/latest/tool-reference/space-time-pattern-mining/create-space-time-cube.htm
                arcpy.stpm.CreateSpaceTimeCube(brd.fc_name, 
                                            os.path.join(data_path, brd.fc_name),
                                            time_field="date", 
                                            time_step_interval="1 Months", 
                                            time_step_alignment="START_TIME", 
                                            distance_interval="3 Miles", 
                                            summary_fields="how_many MEAN ZEROS", 
                                            aggregation_shape_type="HEXAGON_GRID") 
                print(f'Created Space-Time Cube for {brd.name} in data folder.\n')
            except arcpy.ExecuteError:
                print(arcpy.GetMessages())
                print(f"Skipping {brd.name}...\n")
        
        if f"{brd.fc_name}.nc" in os.listdir(data_path):
            # Create 3D Visualization
            if f"{brd.fc_name}_Visualize3D" not in existing_fcs:
                arcpy.stpm.VisualizeSpaceTimeCube3D(os.path.join(data_path, f"{brd.fc_name}.nc"), 
                                        "HOW_MANY_MEAN_ZEROS", 
                                        "VALUE", 
                                        f"{brd.fc_name}_Visualize3D")
                print(f"Created 3D Visualization for {brd.name}.\n")
            # Find outliers
            if f"{brd.fc_name}_outliers" not in existing_fcs:
                try:
                    # https://pro.arcgis.com/en/pro-app/latest/tool-reference/space-time-pattern-mining/localoutlieranalysis.htm
                    print(f'Finding outliers for {brd.name}...\n')
                    arcpy.stpm.LocalOutlierAnalysis(in_cube=os.path.join(data_path, f"{brd.fc_name}.nc"), 
                                                    analysis_variable="HOW_MANY_MEAN_ZEROS", 
                                                    output_features=f"{brd.fc_name}_outliers", 
                                                    neighborhood_distance="25 Miles", 
                                                    neighborhood_time_step=3, 
                                                    number_of_permutations=499, 
                                                    conceptualization_of_spatial_relationships="FIXED_DISTANCE")
                except arcpy.ExecuteError:
                    print(arcpy.GetMessages())
                    print(f"Skipping {brd.name}...\n")
            # Time Series Clustering Analysis
            if f"{brd.fc_name}_ts_clusters" not in existing_fcs:
                try:
                    print(f'Time Series Clustering for {brd.name}...\n')
                    # https://pro.arcgis.com/en/pro-app/latest/tool-reference/space-time-pattern-mining/time-series-clustering.htm
                    arcpy.stpm.TimeSeriesClustering(in_cube=os.path.join(data_path, f"{brd.fc_name}.nc"), 
                                                    analysis_variable="HOW_MANY_MEAN_ZEROS", 
                                                    output_features=f"{brd.fc_name}_ts_clusters", 
                                                    characteristic_of_interest="PROFILE_FOURIER", 
                                                    cluster_count=3, 
                                                    output_table_for_charts=f"{brd.fc_name}_ts_clusters_table", 
                                                    shape_characteristic_to_ignore="TIME_LAG", 
                                                    enable_time_series_popups="CREATE_POPUP")
                except arcpy.ExecuteError:
                    print(arcpy.GetMessages())
                    print(f"Skipping {brd.name}...\n")
        