import arcpy
import pandas as pd
from final_project.birds import Bird

def batchBirdAnalysis(fw_file:str, 
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