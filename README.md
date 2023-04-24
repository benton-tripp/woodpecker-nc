# Woodpeckers of North Carolina
Arcpy batch processed spatial time series analysis of woodpeckers in NC.

*Final Project for NCSU MGIST GIS 540*

## Script names/summaries

- **woodpeckers_nc.py**
   * (Primary script) Analyzes woodpecker species data in North Carolina (runs all scripts, with the exception of data_setup_tool.py)
   * Completes the following steps:
      1. Import necessary libraries and modules
      2. Define variables and set up the working environment
      3. Retrieve North Carolina boundary data
      4. Get FeederWatch data (bird observations) for woodpecker species in North Carolina
      5. Process the data and set up a geodatabase
      6. Retrieve land cover, DEM, and weather data (explanatory variables)
      7. Analyze the data using MaxEnt (maximum entropy modeling) for each woodpecker species
      8. Output trained rasters to map layers; Export PDFs of each layer
- **data_setup_tool**
   * (ArcGIS Pro Script Tool) Similar to woodpeckers_nc.py, except only the data downloading/processing portion
   * Completes the following steps:
      1. Import necessary libraries and modules
      2. Define variables and set up the working environment
      3. Retrieve North Carolina boundary data
      4. Get FeederWatch data (bird observations) for woodpecker species in North Carolina
      5. Process the data and set up a geodatabase
      6. Retrieve land cover, DEM, and weather data (explanatory variables)
- **get_nc_boundary.py**
   * This script downloads the North Carolina state boundary shapefile from the US Census Bureau's TIGER/Line dataset, extracts the shapefile, adds it to a geodatabase, dissolves the polygons into a single polygon, and projects it to a specified coordinate system. The script uses the arcpy library to perform geoprocessing tasks and urllib to download the shapefile. It also uses os and zipfile for file handling.
- **birds.py**
   * This script provides a set of classes to manage bird species data extracted from
   FeederWatch dataframes. The Species class organizes raw FeederWatch data into
   human-understandable metadata, while the Bird class, a subclass of Species,
   creates bird objects with formatted feature class name attributes.
- **get_bird_data.py**
   * Queries the Species Codes sheet from the FeederWatch Data Dictionary and returns a pandas dataframe of species using `getSpeciesCodes()`
   * Gets FeederWatch data from website, cleans/ filters data using `cleanFeederWatchData()`, and concatenates and saves the final output to a .csv file. Returns a pandas dataframe of the selected FeederWatch bird data.
- **process_bird_data.py**
   * This script contains a function to batch process bird data from FeederWatch. The processing steps include creating a feature class from the CSV file, adding a projection, filtering by species, and saving individual species as separate feature classes in the geodatabase.
- **get_land_cover_data.py** 
   * This script contains a function to download and process land cover raster data for North Carolina from the NCSU GIS library. The land cover data is downloaded, resampled to 2 km resolution, reprojected, and clipped to the state boundary.
- **get_dem_data.py**
   * This script downloads, extracts, and processes the 250m Digital Elevation Model (DEM) data for North Carolina. The data is sourced from https://gisdata.lib.ncsu.edu/DEM/nc250.zip. The script uses the arcpy library to perform geoprocessing tasks, and urllib to download the data. It also uses os and zipfile for file handling. Note that the user must be connected to the NCSU network (on-campus or via VPN) if downloading the data for the first time.
- **get_weather_data.py**
   * This script downloads and processes weather raster data for specified variables and years, trims the rasters to the North Carolina boundary, and aggregates them for each variable type.
   * The `getWeatherData()` function performs the following tasks:
      1. Downloads weather raster data for specified variables and years.
      2. Extracts the data from zip files.
      3. Trims the raster data to the North Carolina boundary and saves them to the workspace.
      4. Aggregates the rasters for each variable type (avg precipitation, min temperature, and max temperature).
      5. Deletes unneeded rasters from the workspace.
      6. Returns the names of the aggregated rasters as a list of strings.
- **presence_only.py**
   * This script performs presence-only species distribution modeling using the MaxEnt algorithm for a list of bird species in North Carolina. The script reads species occurrence data from a pandas DataFrame, generates a set of potential parameter combinations for the MaxEnt model, and performs a grid search to find the best combination of parameters based on the F1 score. The best performing model for each species is saved to a geodatabase, along with related output data, such as trained features, response curves, and sensitivity tables.
   * The script makes use of the arcpy library to interact with geospatial data and perform geoprocessing tasks. It also uses the pandas library for data manipulation and os, pickle, and itertools for file and data handling.
- **presence_only_mapping.py** 
   * Creates and exports maps of modeled woodpecker distribution in North Carolina

### Running this Analysis
Running this entire script from start to finish can take a fair amount of time (~60-90 minutes). This is for a few reasons:

1. There is simply a lot of data. It's unavoidable.
2. The first time the script is run, the data needs to be downloaded from the 
   [FeederWatch website](https://feederwatch.org/explore/raw-dataset-requests/). 
   Depending on your internet speed, this can take a while.
3. The actual analysis is pretty computationally heavy.

To run, first clone/download the project into your desired location and navigate to
the `woodpecker-nc` directory. Activate a python environment with `arcpy`, `numpy`, and `pandas` installed (you will need ArcGIS Pro installed on your machine to use `arcpy`). Then run:

```
python woodpeckers_nc.py <PROJECT_PATH>
```

<hr>