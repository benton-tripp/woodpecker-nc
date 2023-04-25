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
import locale

def hexToRGB(hex_color:str) -> tuple:
    """
    Convert Hexidecimal Color to RGB
    Args
    - hex_color
    Output
    Tuple with RGB Value
    """
    hex_color = hex_color.lstrip('#')
    return list(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + [100]



def createMapAndExport(project_path:str, 
                       wspace:str, 
                       brd_rasters:dict, 
                       output_folder:str,
                       colors:list=['#F6FCE1', '#CFD6B4', '#F5CA7A', '#D98754']) -> None:
    """
    Creates and exports maps for the modeled distribution of each bird species.
    Args
    - project_path : The file path to the project file.
    - wspace : The workspace location for the raster layers.
    - brd_rasters : The bird/raster name key/value pairs.
    - output_folder : The output folder location for the PDFs.
    - colors : list of 5 hexidecimal color values
    """
        
    # Set workspace
    arcpy.env.workspace = wspace

    # Define project
    project = arcpy.mp.ArcGISProject(project_path)
    arcpy.env.overwriteOutput = True
    arcpy.env.resamplingMethod = "CUBIC"

    # Loop through each trained raster
    for raster in brd_rasters.keys():
        # Get species name
        species_name = brd_rasters[raster]
        print(f"Adding {species_name} raster layer to map...")

        # Create a new map and add it to the project
        m = project.listMaps("Map")[0]
        
        # Check if raster + "_Lyr" already exists in the map and remove it
        for lyr in m.listLayers():
            if lyr.name == raster + "_Lyr":
                m.removeLayer(lyr)
                break
        
        # Create a raster layer from the raster
        raster_layer = arcpy.MakeRasterLayer_management(raster, raster + "_Lyr")
        # Add layer to map
        m.insertLayer(reference_layer=m.listLayers()[1], 
                      insert_layer_or_layerfile=raster_layer[0],
                      insert_position="AFTER")
        
        # lyrs = [lyr.name for lyr in m.listLayers()]
        for i, lyr in enumerate(m.listLayers()):
            if lyr.name == raster + "_Lyr":
                l = lyr
                l_idx = i
            elif lyr.name not in ["World Terrain Reference", "World Terrain Base", "World Hillshade"]:
                lyr.visible = False

        sym = l.symbology
        sym.updateColorizer("RasterClassifyColorizer")
        # sym.colorizer.classificationField = f"{species_name} Estimated Probability"
        # sym.colorizer.breakCount = 5
        upperBound = 0.25
        for i, brk in enumerate(sym.colorizer.classBreaks):
            # brk.upperBound = upperBound
            brk.label = "\u2264 " + str(locale.format_string("%.2f", upperBound, grouping=True))
            brk.color = {'RGB' : hexToRGB(colors[i])}
            sym.colorizer.classBreaks[i] = brk
            upperBound += 0.25

        l.symbology = sym
        l.visible = True
        
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
        layer_extent = mf.getLayerExtent(l)
        mf.panToExtent(layer_extent)

        # Legend
        print("Updating legend...")
        legend = layout.listElements("LEGEND_ELEMENT", "Legend")[0]
        for lyr in legend.items:
            if lyr.name != raster + "_Lyr":
                legend.removeItem(lyr)
        if not l.name in [lyr.name for lyr in legend.items]:
            legend.addItem(l)
        legend.showTitle = True
        legend.title = f"{species_name} Estimated Probability"

        # Export the layout to a PDF
        pdf_path = os.path.join(output_folder, raster.replace('Trained_Raster', 'Dist') + ".pdf")
        print(f"Exporting {species_name} layout to {pdf_path}...")
        layout.exportToPDF(pdf_path, 
                           resolution=250, 
                           image_quality="BEST", 
                           image_compression="NONE")
        
        # Hide the added raster layer from the map
        l.visible = False
    arcpy.env.overwriteOutput = False
    # Save the current state of the project
    project.save()


def outputMaps(species_df:pd.DataFrame, 
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
    createMapAndExport(project_path, wspace, brd_rasters, output_folder)



