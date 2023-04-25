# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# birds.py
#
# This script provides a set of classes to manage bird species data extracted from
# FeederWatch dataframes. The Species class organizes raw FeederWatch data into
# human-understandable metadata, while the Bird class, a subclass of Species,
# creates bird objects with formatted feature class name attributes.


# Import libraries
import pandas as pd
import numpy as np
import re

class Species():
    """
    A class to organize raw FeederWatch dataframes into human-understandable metadata.

    Attributes:
    -----------
    species_code : list
        List of species codes.
    species_name : list
        List of species names.
    family : list
        List of families for each species.
        
    Parameters:
    -----------
    dataframe : pandas.DataFrame
        Raw FeederWatch dataframe containing information on bird species.
    """
    def __init__(self, dataframe:pd.DataFrame) -> None:
        """
        Initialize Species class with the given FeederWatch dataframe.

        Parameters:
        -----------
        dataframe : pandas.DataFrame
            Raw FeederWatch dataframe containing information on bird species.
        """
        self.species_code = dataframe.species_code.to_list()
        self.species_name = dataframe.species_name.to_list()
        self.family = dataframe.family.to_list()

class Bird(Species):
    """
    A class to create a bird object from a FeederWatch dataframe. It is a subclass of Species.

    Attributes:
    -----------
    code : str
        Bird species code.
    name : str
        Bird species name.
    family : str
        Bird family.
    formatted_name : str
        Bird name formatted for use as feature class name attribute.
    fc_name : str
        Feature class name attribute for the bird.

    Parameters:
    -----------
    dataframe : pandas.DataFrame
        Raw FeederWatch dataframe containing information on bird species.
    bird_name : str
        Name of the bird species to create.
    _prefix : str, optional
        Prefix to be added to the feature class name attribute, by default "FW_".
    """
    def __init__(self, dataframe:pd.DataFrame, bird_name:str, _prefix="FW_") -> None:
        """
        Initialize Bird class with the given FeederWatch dataframe, bird name, and prefix.

        Parameters:
        -----------
        dataframe : pandas.DataFrame
            Raw FeederWatch dataframe containing information on bird species.
        bird_name : str
            Name of the bird species to create.
        _prefix : str, optional
            Prefix to be added to the feature class name attribute, by default "FW_".
        """
        super().__init__(dataframe)
        # Get index from original dataframe
        bird_idx = np.array([bird_name == b for b in self.species_name])
        # Create attributes
        self.code = str(np.array(self.species_code)[bird_idx][0])
        self.name = str(np.array(self.species_name)[bird_idx][0])
        self.family = str(np.array(self.family)[bird_idx][0])
        # Adjust name for formatted feature class name attribute
        name_parts = self.name.split(', ')
        self.formatted_name = re.sub("[()]", "", name_parts[1] + "_" + name_parts[0])\
                .replace(" ", "_").replace("-", "_")
        self.fc_name = f"{_prefix}{self.formatted_name}_NC"


# Import libraries/modules
import arcpy
import os
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


    # Create map layers export map pdfs for each of the rasters
    createMapAndExport(project_path, wspace, brd_rasters, output_folder)


# with open("data/species_df.pickle", "wb") as f:
#   pickle.dump(NC_WOODPECKERS, f)

import pickle

with open("data/species_df.pickle", "rb") as f:
    species_df = pickle.load(f)

project_path="woodpeckerNC.aprx"
wspace="woodpeckerNC.gdb"
data_path="data"
output_folder="maps"

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


colors = [
        "#ffffcc",
        "#ffeda0",
        "#fed976",
        "#feb24c",
        "#fd8d3c",
        "#fc4e2a",
        "#e31a1c",
        "#bd0026",
        "#800026",
        "#4d004b",
    ]


# Define project
project = arcpy.mp.ArcGISProject(project_path)
arcpy.env.overwriteOutput = True
arcpy.env.resamplingMethod = "CUBIC"

raster = [k for k in brd_rasters.keys()][0]
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
# Reclassify the raster using the remap_range object
reclass_list = []
num_classes = 10
for i in range(num_classes):
    lower_bound = i * (1 / num_classes)
    upper_bound = (i + 1) * (1 / num_classes)
    reclass_list.append([lower_bound, upper_bound, i + 1])

reclassified_raster = arcpy.sa.Reclassify(in_raster=raster, 
                                            reclass_field="Value", 
                                            remap=arcpy.sa.RemapRange(reclass_list))
# Create a raster layer from the raster
raster_layer = arcpy.MakeRasterLayer_management(reclassified_raster, raster + "_Lyr")
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
sym.colorizer.classificationField = f"{species_name} Estimated Probability"
# sym.colorizer.breakCount = 5
upperBound = 0.1
for i, brk in enumerate(sym.colorizer.classBreaks):
    # brk.upperBound = upperBound
    brk.label = "\u2264 " + str(locale.format_string("%.2f", upperBound, grouping=True))
    brk.color = {'RGB' : hexToRGB(colors[i])}
    print(brk.color)
    sym.colorizer.classBreaks[i] = brk
    upperBound += upperBound

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
