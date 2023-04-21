import arcpy
import arcpy.mp as mp
import os
import pandas as pd
from birds import Bird
import pickle

with open("C:/Users/bento/final_project/woodpeckerNC/data/species_df.pickle", "rb") as f:
    species_df = pickle.load(f)

project_path="C:/Users/bento/final_project/woodpeckerNC/woodpeckerNC.aprx"
wspace="C:/Users/bento/final_project/woodpeckerNC/woodpeckerNC.gdb"
data_path="C:/Users/bento/final_project/woodpeckerNC/data"
output_folder="maps"

# Set workspace
arcpy.env.workspace = wspace

# Create an output folder for the PDFs
output_folder = os.path.join(data_path, "maps")
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Get trained rasters
trained_rasters = arcpy.ListRasters("*_NC_Trained_Raster")

# Get bird/raster name key/value pairs
brd_rasters = [{Bird(species_df, name).formatted_name + \
                "_NC_Trained_Raster":Bird(species_df, name).formatted_name.replace("_", " ")}\
                for name in species_df.species_name.unique() \
                if Bird(species_df, name).formatted_name + "_NC_Trained_Raster" in trained_rasters]
brd_rasters = {key: value for d in brd_rasters for key, value in d.items()}


# Define project
project = arcpy.mp.ArcGISProject(project_path)

# Loop through each trained raster
for raster in brd_rasters.keys():
    # Get species name
    species_name = brd_rasters[raster]
    print(f"Adding {species_name} raster layer to map...")

    # Create a new map and add it to the project
    m = project.listMaps("Map")[0]

    # List layers in map
    lyr_name = raster + "_Lyr"
    layers = [l.name for l in m.listLayers()]
    
    # Hide all existing layers
    if len(m.listLayers()) > 0:
        for l in m.listLayers():
            l.visible = False

    if lyr_name not in layers:
        # Create a raster layer from the raster
        print(f"Adding {lyr_name} to map...")
        raster_layer = arcpy.MakeRasterLayer_management(raster, raster + "_Lyr")
        m.addLayer(raster_layer[0])
    else:
        print(f"{lyr_name} already in map")

    # Define layer, make visible
    layer = [l for l in m.listLayers() if l.name == lyr_name][0]
    layer.visible = True

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
    layer.visible = False

# Save the current state of the project
project.save()