import arcpy
import arcpy.mp as mp
import os
import pandas as pd
from birds import Bird

def create_map_and_export(project_path:str, 
                          wspace:str, 
                          brd_rasters:dict, 
                          output_folder:str) -> None:
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
        
        # Create a new map and add it to the project
        m = project.listMaps("Map")[0]
        m.addLayer(raster_layer[0])
        raster_layer[0].visible = True

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
        raster_layer[0].visible = False

    # Save the current state of the project
    project.save()


def output_maps(species_df:pd.DataFrame, 
                project_path:str, 
                wspace:str, 
                data_path:str, 
                output_folder:str) -> None:
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
