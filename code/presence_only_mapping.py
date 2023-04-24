# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# presence_only_mapping.py
#
# Creates and exports maps of modeled woodpecker distribution in North Carolina
# 1. Import necessary libraries and modules
# 2. Define the create_map_and_export() function to create maps and export them as PDFs
#    - Set workspace and project
#    - Loop through each trained raster and create a raster layer
#    - Add the raster layer to the map, set visibility, and create a layout
#    - Update the layout title and zoom to the raster layer extent
#    - Export the layout to a PDF and hide the raster layer
#    - Save the project
# 3. Define the output_maps() function to organize and generate maps for each species
#    - Set workspace and create an output folder for the PDFs
#    - Get trained rasters and bird/raster name key/value pairs
#    - Create map layers and export map PDFs for each of the rasters


# Import libraries/modules
import arcpy
import os
import pandas as pd
from birds import Bird

def hex_to_rgb(hex_color:str) -> tuple:
    """
    Convert Hexidecimal Color to RGB
    Args
    - hex_color
    Output
    Tuple with RGB Value
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_map_and_export(project_path:str, 
                          wspace:str, 
                          brd_rasters:dict, 
                          output_folder:str) -> None:
    """
    Creates and exports maps for the modeled distribution of each bird species.
    Args
    - project_path : The file path to the project file.
    - wspace : The workspace location for the raster layers.
    - brd_rasters : The bird/raster name key/value pairs.
    - output_folder : The output folder location for the PDFs.
    """
        
    # Set workspace
    arcpy.env.workspace = wspace

    # Define project
    project = arcpy.mp.ArcGISProject(project_path)

    # Loop through each trained raster
    for raster in brd_rasters.keys():
        # Get species name
        species_name = brd_rasters[raster]
        print(f"Adding {species_name} raster layer to map...")
        # Create a raster layer from the raster
        raster_layer = arcpy.MakeRasterLayer_management(raster, raster + "_Lyr")

        # Apply manual symbology
        remap = arcpy.sa.RemapRange([[0, 0.2, 1],
                                      [0.2, 0.4, 2],
                                      [0.4, 0.6, 3],
                                      [0.6, 0.8, 4],
                                      [0.8, 1.0, 5]])

        classified_raster = arcpy.sa.Reclassify(raster_layer, "Value", remap, "NODATA")
        classified_raster.save(os.path.join(wspace, raster + "_classified"))

        classified_layer = arcpy.MakeRasterLayer_management(os.path.join(wspace, raster + "_classified"), 
                                                            raster + "_classified_Lyr")
        m.addLayer(classified_layer[0])
        classified_layer[0].visible = True

        # Define colors for symbology
        colors = ['#F6FCE1', '#CFD6B4', '#F5CA7A', '#DDAF5B', '#9C5B00']
        rgb_colors = [hex_to_rgb(color) for color in colors]

        # Set the symbology and labels for the classified raster layer
        sym = classified_layer[0].symbology
        sym.updateColorizer('Classify')
        sym.renderer.classificationMethod = 'Manual'
        sym.renderer.breakCount = 5

        sym.renderer.breaks[0].label = '0-0.2'
        sym.renderer.breaks[0].color = {'RGB': rgb_colors[0]}

        sym.renderer.breaks[1].label = '0.2-0.4'
        sym.renderer.breaks[1].color = {'RGB': rgb_colors[1]}

        sym.renderer.breaks[2].label = '0.4-0.6'
        sym.renderer.breaks[2].color = {'RGB': rgb_colors[2]}

        sym.renderer.breaks[3].label = '0.6-0.8'
        sym.renderer.breaks[3].color = {'RGB': rgb_colors[3]}

        sym.renderer.breaks[4].label = '0.8-1.0'
        sym.renderer.breaks[4].color = {'RGB': rgb_colors[4]}

        classified_layer[0].symbology = sym
        
        # Create a new map and add it to the project
        m = project.listMaps("Map")[0]
        m.addLayer(classified_layer[0])
        classified_layer[0].visible = True

        print(f"Creating a layout for {species_name}...")
        # Get the default layout
        layout = project.listLayouts("Layout")[0]

        # Update the title of the layout
        title = [el for el in layout.listElements("TEXT_ELEMENT")][0]
        print("Updating title in layout...")
        title.text = species_name + " Modeled Distribution"
        
        # Zoom to the extent of the raster layer
        print("Zooming to map layer extent...")
        mf = layout.listElements("MAPFRAME_ELEMENT")[0]
        mf.zoomToAllLayers()

        # Export the layout to a PDF
        pdf_path = os.path.join(output_folder, raster.replace('Trained_Raster', 'Dist') + ".pdf")
        print(f"Exporting {species_name} layout to {pdf_path}...")
        layout.exportToPDF(pdf_path)
        
        # Hide the added raster layer from the map
        classified_layer[0].visible = False

    # Save the current state of the project
    project.save()


def output_maps(species_df:pd.DataFrame, 
                project_path:str, 
                wspace:str, 
                data_path:str, 
                output_folder:str) -> None:
    """
    Organizes and generates maps for each bird species.
    Args
    - species_df : The DataFrame of bird species.
    - project_path : The file path to the project file.
    - wspace : The workspace location for the raster layers.
    - data_path : The file path to the data folder.
    - output_folder : The output folder location for the PDFs.
    """
    # Checks to confirm valid file paths
    if not os.path.exists(project_path):
        raise FileNotFoundError(f"Project path '{project_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    # Set workspace
    arcpy.env.workspace = wspace

    # Create an output folder for the PDFs
    output_folder = os.path.join(data_path, "maps")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get trained rasters
    trained_rasters = arcpy.ListRasters("*_NC_Trained_Raster")

    # Get bird/raster name key/value pairs
    brd_rasters = [{Bird(species_df, name).formatted_name +\
                   "_NC_Trained_Raster":Bird(species_df, name).formatted_name.replace("_", " ")}\
                   for name in species_df.species_name.unique() \
                   if Bird(species_df, name).formatted_name + "_NC_Trained_Raster" in trained_rasters]
    brd_rasters = {key: value for d in brd_rasters for key, value in d.items()}

    # Create map layers export map pdfs for each of the rasters
    create_map_and_export(project_path, wspace, brd_rasters, output_folder)


# with open("data/species_df.pickle", "wb") as f:
#   pickle.dump(NC_WOODPECKERS, f)

import pickle

with open("data/species_df.pickle", "rb") as f:
    species_df = pickle.load(f)

output_maps(species_df, 
            project_path="woodpeckerNC.aprx", 
            wspace="woodpeckerNC.gdb", 
            data_path="data", 
            output_folder="maps")
