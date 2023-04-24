# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# process_bird_data.py
# 
# This script contains a function to batch process bird data from FeederWatch. The
# processing steps include creating a feature class from the CSV file, adding a
# projection, filtering by species, and saving individual species as separate feature
# classes in the geodatabase.

# Import libraries/modules
import os
import arcpy
import pandas as pd
from birds import Bird

def batchBirdProcessing(fw_file:str, 
                        base_fc:str,
                        existing_fcs:list,
                        out_coordinate_system:arcpy.SpatialReference, 
                        data_path:str,
                        wspace:str,
                        fw_df:pd.DataFrame,
                        species_df:pd.DataFrame,
                        nc_boundary:str,
                        _prefix:str = "FW_") -> None:
    """
    Batch processing of FeederWatch bird data. 
    Steps:
    1) Creates Feature Class from .csv file in file Geodatabase
    2) Adds projection, saving to new Feature Class
    3) Filters Projected Feature Class by species, saving individual
       species to their own Feature Classes in the database
    Args: 
    - fw_file: FeederWatch data .csv file
    - base_fc: Base Feature Class name
    - existing_fcs: List of existing Feature Classes already saved to the 
      database (if they already exist, they will be skipped during batch
      processing)
    - out_coordinate_system: Projected coordinate system
    - data_path: Path to feederwatch data
    - fw_df: FeederWatch dataframe
    - species_df: Species dataframe
    - nc_boundary: North Carolina State boundary to be used as the study area
    """
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    fw_file = os.path.join(data_path, fw_file)
    if not os.path.exists(fw_file):
        raise FileNotFoundError(f"Data path '{fw_file}' not found.")

    print("Starting batch processing of bird data prior to analysis...")
    arcpy.AddMessage("Starting batch processing of bird data prior to analysis...")

    arcpy.env.workspace = wspace
    
    # Create base feature class
    if f"{base_fc}_NC" not in existing_fcs:
        
        arcpy.management.XYTableToPoint(in_table=fw_file,
                                        out_feature_class=base_fc,
                                        x_field="longitude", 
                                        y_field="latitude")
        # Add projection to base FC
        arcpy.Project_management(base_fc, f"{base_fc}_projected", out_coordinate_system)

        arcpy.SelectLayerByLocation_management(f"{base_fc}_projected", 
                                               "INTERSECT", 
                                               nc_boundary)
        
        arcpy.CopyFeatures_management(f"{base_fc}_projected", 
                                      f"{base_fc}_NC")
        
        # Delete unneeded feature layers
        for fc in [base_fc, f"{base_fc}_projected"]:
            arcpy.Delete_management(fc)

    # Add to GDB by species
    for species_name in fw_df.species_name.unique():
        brd = Bird(dataframe=species_df, bird_name=species_name, _prefix=_prefix)
        if brd.fc_name not in existing_fcs:
            print(f'Adding {brd.name} to gdb...')
            arcpy.AddMessage(f'Adding {brd.name} to gdb...')
            arcpy.analysis.Select(f"{base_fc}_NC", 
                                  brd.fc_name, 
                                  f"species_name = '{brd.name}'")
    
    print("Finished batch processing of bird data prior to analysis")
    arcpy.AddMessage("Finished batch processing of bird data prior to analysis")