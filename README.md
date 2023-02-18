# Woodpeckers of North Carolina
Arcpy batch processed spatial time series analysis of woodpeckers in NC.

*Final Project for NCSU MGIST GIS 540*

### Running this Analysis
Running this entire script from start to finish can take a fair amount of time (~60-90 minutes). This is for a few reasons:

1. There is simply a lot of data. It's unavoidable.
2. The first time the script is run, the data needs to be downloaded from the 
   [FeederWatch website](https://feederwatch.org/explore/raw-dataset-requests/). 
   Depending on your internet speed, this can take a while.
3. The actual analysis is pretty computationally heavy. In particular, the 
   [local outlier analysis](https://pro.arcgis.com/en/pro-app/latest/tool-reference/space-time-pattern-mining/localoutlieranalysis.htm) is conducting several hundred permutations of the data, so it takes a fair amount of time.

To run, first clone/download the project into your desired location and navigate to
the `woodpecker-nc` directory. Activate a python environment with `arcpy`, `numpy`, and `pandas` installed (you will need ArcGIS Pro installed on your machine to use `arcpy`). Then run:

```
python woodpeckers_nc.py <PROJECT_PATH>
```

<hr>