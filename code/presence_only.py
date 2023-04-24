# Name: Benton Tripp
# unity ID: btripp
###################################################################################
# 
# presence_only.py
# 
# This script performs presence-only species distribution modeling using the MaxEnt algorithm for a list of bird species
# in North Carolina. The script reads species occurrence data from a pandas DataFrame, generates a set of potential
# parameter combinations for the MaxEnt model, and performs a grid search to find the best combination of parameters
# based on the F1 score. The best performing model for each species is saved to a geodatabase, along with related output
# data, such as trained features, response curves, and sensitivity tables.
# 
# The script makes use of the arcpy library to interact with geospatial data and perform geoprocessing tasks. It also
# uses the pandas library for data manipulation and os, pickle, and itertools for file and data handling.
# 
# Reference to PresenceOnlyPredicton using arcpy:
# https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-statistics/presence-only-prediction.htm


# Import libraries/modules
import itertools
import arcpy 
import pandas as pd
from birds import Bird
import pickle
from math import inf
import os
import json
import gc

def getPrecision(TP:float, FP:float) -> float:
    """
    Calculates the precision measurement given the True/False positive inputs
    Args
    - TP : True Positive
    - FP : False Positive 
    Output
    - float value of precision (-inf if zero division error)
    """
    try:
        return TP / (TP + FP)
    except ZeroDivisionError:
        return -inf

def getF1(TP:float, FP:float, recall:float) -> float:
    """
    Calculates the F1 Score given the True/False positive and Recall inputs.
    Used in `scoreFromSensitivityTable` function
    Args
    - TP : True Positive
    - FP : False Positive 
    - Recall : recall measurement
    Output
    - float value of F1 score (-inf if zero division error)
    """
    try:
        return 2 * ((TP / (TP + FP)) * recall) / ((TP / (TP + FP)) + recall)
    except ZeroDivisionError:
        return -inf

def scoreFromSensitivityTable(sensitivity_table: str) -> float:
    """
    Computes the F1 score of a model from the output values within the sensitivity table
    Args
    - sensitivity_table : name of sensitivity table in the GDB
    """
    # field_names = [field.name for field in arcpy.ListFields(sensitivity_table)]
    with arcpy.da.SearchCursor(sensitivity_table, 
                            ['CUTOFF', 'FPR', 'TPR', 'FNR', 'TNR', 'SENSE', 'SPEC']) as cursor:
        vals = [
            {
                "cutoff": cutoff,
                "FP": FP,
                "TP": TP,
                "FN": FN,
                "TN": TN,
                "recall": recall,
                "specificity": specificity,
                "precision": getPrecision(TP, FP),
                "f1": getF1(TP, FP, recall),
            }
            for (cutoff, FP, TP, FN, TN, recall, specificity) in cursor
        ]
    df = pd.DataFrame.from_dict(vals)
    return(df)

# Log model parameters after they are trained
def logModel(params:dict, log_file:str) -> None:
    """
    Logs the parameters used to train a model. The workflow is structured such that
    a log_file will correspond to each species of bird, and the logged parameters
    are those in the `parameter_grid` dictionary along with the best F1 score and 
    corresponding cutoff value. A new file will be created if it doesn't already
    exist. Logs are dictionary values saved in a json file, each respectively 
    appended to a list.
    Args
    - params : The parameter dictionary
    - log_file : The path/file where the log should be dumped
    """
    # If the file doesn't exist, create it with an empty list
    if not os.path.isfile(log_file):
        with open(log_file, "w") as f:
            json.dump([], f)

    # Read the existing content
    with open(log_file, "r") as f:
        content = json.load(f)

    # Append the new parameters
    content.append(params)

    # Write the updated content back to the file
    with open(log_file, "w") as f:
        json.dump(content, f)

def checkModelParams(file_dict:dict, params:dict) -> bool:
    """
    Used in `checkModelLogs`; Iterates through the each of the logged parameters in a given
    log file. If all of the values in the input parameters are equal to the respective 
    parameters in the log file, and there are the same parameters in each (with the 
    exception of f1 & cutoff), return True; Otherwise False.
    Args
    - file_dict : path/name for log file with logged parameters for a given species
    - params : dictionary of parameters to be compared with log file values
    Output
    - Boolean confirming whether or not the input parameters were already completed for the 
      given species
    """
    for p in file_dict:
        if all(params[key] == p[key] for key in params if key in p):
            if all(k in params.keys() for k in [k_ for k_ in p if k_ != "f1" and k_ != "cutoff"]):
                return True
    return False

# Check if model already run previously
def checkModelLogs(log_path:str, params:dict, species:str) -> bool:
    """
    Check if a model with the given parameter settings has already been run for the given species.
    Args
    - log_path : A file path to the directory containing model log files.
    - params : A dictionary of model parameters.
    - species_name : The formatted name of the species.
    Output
    - True if a model with the given parameters has already been run for the species, False otherwise.
    """
    files = [f for f in os.listdir(log_path) if species in f]
    for file in files:
        file_path = os.path.join(log_path, file)
        with open(file_path, 'r') as f:
            file_dict = json.load(f)
            if checkModelParams(file_dict, params):
                return False
    return True


def getAllCombos(parameter_grid:dict) -> dict:
    """
    Generate a list of all possible combinations of parameter values given a dictionary of
    parameter names and their corresponding lists of values.
    Args
    - parameter_grid : A dictionary where keys are parameter names and values 
                       are lists of possible parameter values.
    Output
    A list of tuples, where each tuple represents a unique combination of parameter values.
    """
    # Generate all combinations of parameters
    if "NO_THINNING" not in parameter_grid["spatial_thinning"]:
        all_combinations = list(itertools.product(*parameter_grid.values()))
    elif "THINNING" not in parameter_grid["spatial_thinning"]:
        # Generate combinations for NO_THINNING
        all_combinations = [
            (None, basis_expansion, weight, knots, "NO_THINNING", link_function, None)
            for basis_expansion, weight, knots, link_function
            in itertools.product(
                parameter_grid["basis_expansion_functions"],
                parameter_grid["relative_weight"],
                parameter_grid["number_knots"],
                parameter_grid["link_function"]
            )
        ]
    else:
        # Generate combinations for NO_THINNING
        no_thinning_combinations = [
            (None, basis_expansion, weight, knots, "NO_THINNING", link_function, None)
            for basis_expansion, weight, knots, link_function
            in itertools.product(
                parameter_grid["basis_expansion_functions"],
                parameter_grid["relative_weight"],
                parameter_grid["number_knots"],
                parameter_grid["link_function"]
            )
        ]
        # Generate combinations for THINNING
        thinning_combinations = list(itertools.product(
            parameter_grid["number_of_iterations"],
            parameter_grid["basis_expansion_functions"],
            parameter_grid["relative_weight"],
            parameter_grid["number_knots"],
            ["THINNING"],
            parameter_grid["link_function"],
            parameter_grid["thinning_distance_band"]
        ))
        # Combine the two lists of combinations
        all_combinations = no_thinning_combinations + thinning_combinations
    return all_combinations

def runMaxEnt(static_params:dict, 
              params:dict, 
              outputs:dict, 
              output:bool = False) -> arcpy.stats.PresenceOnlyPrediction:
    """
    Run the MaxEnt algorithm for species distribution modeling using the given static parameters,
    dynamic parameters, and output file names.
    Args
    - static_params : A dictionary of non-changing parameters for the MaxEnt algorithm.
    - params : A dictionary of dynamic parameters to be tested in the MaxEnt algorithm.
    - outputs : A dictionary of output file names for the MaxEnt algorithm.
    - output : A flag indicating whether to save the model output to the workspace. Defaults to False.
    """
    if not output:
        for k in outputs.keys():
            if k != "output_sensitivity_table":
                outputs[k] = None

    result = arcpy.stats.PresenceOnlyPrediction(
        # Inputs
        input_point_features=static_params['input_point_features'],
        explanatory_variables=static_params['explanatory_variables'],
        distance_features=static_params['distance_features'],
        explanatory_rasters=static_params['explanatory_rasters'],
        study_area_polygon=static_params['study_area_polygon'],
        # Outputs
        output_trained_features=outputs["output_trained_features"], 
        output_trained_raster=outputs["output_trained_raster"],
        output_response_curve_table=outputs["output_response_curve_table"],
        output_sensitivity_table=outputs["output_sensitivity_table"],
        output_pred_features=outputs["output_pred_features"],
        output_pred_raster=outputs["output_pred_raster"],
        # Other parameters
        contains_background=static_params['contains_background'],
        presence_indicator_field=static_params['presence_indicator_field'],
        study_area_type=static_params['study_area_type'],
        presence_probability_cutoff=static_params['presence_probability_cutoff'],
        features_to_predict=static_params['features_to_predict'],
        explanatory_variable_matching=static_params['explanatory_variable_matching'],
        explanatory_distance_matching=static_params['explanatory_distance_matching'],
        explanatory_rasters_matching=static_params['explanatory_rasters_matching'],
        allow_predictions_outside_of_data_ranges=static_params['allow_predictions_outside_of_data_ranges'],
        resampling_scheme=static_params['resampling_scheme'],
        number_of_groups=static_params['number_of_groups'],
        # Params to iterate through 
        basis_expansion_functions=params['basis_expansion_functions'],
        number_knots=params['number_knots'],
        spatial_thinning=params['spatial_thinning'],
        number_of_iterations=params["number_of_iterations"], 
        thinning_distance_band=params["thinning_distance_band"], 
        relative_weight=params["relative_weight"],  #1-100
        link_function=params["link_function"]
    )
    return result

def getMinMaxCellSize() -> dict:

    input_rasters = arcpy.ListRasters()

    # Get the cell sizes of all input rasters
    cell_sizes = []
    for raster_path in input_rasters:
        raster = arcpy.Raster(raster_path)
        cell_size_x = float(raster.meanCellWidth)
        cell_size_y = float(raster.meanCellHeight)
        cell_sizes.append((cell_size_x, cell_size_y))

    # Find the minimum and maximum cell sizes
    min_cell_size = min(min(cell_sizes))
    max_cell_size = max(max(cell_sizes))
    
    return {"MIN":min_cell_size, "MAX":max_cell_size}




def batchMaxEnt(species_df:pd.DataFrame, 
                wspace:str, 
                data_path:str,
                explanatory_rasters:list,
                nc_boundary:str) -> None:
    """
    Run the MaxEnt algorithm for presence-only species distribution modeling on a batch of species,
    given a dataframe of species information, a workspace path, and a data path. The function performs
    a grid search to find the optimal set of parameters for each species model and outputs the best
    model's results to the geodatabase.
    Args
    - species_df : A pandas DataFrame containing species information.
    - wspace : A file path to the working directory/GDB
    - data_path : A file path to the data directory
    - explanatory_rasters : list of rasters saved in GDB to be used as input explanatory rasters;
                            they should be stored in a nested list format, with each inner list 
                            being a length of two. The first item in each "inner list" is the 
                            name of the feature layer, and the second is either "true" or "false"
                            (indicating categorical or continuous data).
    - nc_boundary : boundary of North Carolina, to be used as the STUDY_POLYGON
    """
    # Checks to confirm valid file paths
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path '{data_path}' not found.")
    if not os.path.exists(wspace):
        raise FileNotFoundError(f"Workspace path '{wspace}' not found.")
    
    print("Starting batch presence-only predictions...")
    arcpy.AddMessage("Starting batch presence-only predictions...")
    # Set workspace
    arcpy.env.workspace = wspace
    # Temporarily enable overwriting data
    arcpy.env.overwriteOutput = True

    # Create model output directory
    model_data_path = os.path.join(data_path, "model_data")
    if not os.path.exists(model_data_path):
        os.makedirs(model_data_path)
    log_path = os.path.join(model_data_path, "model_training_logs")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    for species_name in species_df.species_name.unique():
        brd = Bird(species_df, species_name)
        s = brd.formatted_name
        print(f"Modeling {brd.name} distribution in NC using the MaxEnt algorithm...")
        arcpy.AddMessage(f"Modeling {brd.name} distribution in NC using the MaxEnt algorithm...")
        
        # Check if species already in gdb; If yes, just load model 
        if f"{s}_NC_Trained_Features" in arcpy.ListFeatureClasses():
            msg_str = f"Modeling already completed for {brd.name} for this project. " + \
                      "To continue, please delete the trained features output by the model" + \
                      "from the default geodatabase."
            arcpy.AddMessage(msg_str)
            print(msg_str)
        else:
            # Non-changing parameters (written out so that they can be saved)
            static_params = {
                "input_point_features":brd.fc_name,
                "contains_background":"PRESENCE_ONLY_POINTS", 
                "explanatory_variables":None,
                "presence_indicator_field":None,
                "distance_features":None, 
                # T/F -> categorical/continuous
                "explanatory_rasters":explanatory_rasters,
                "study_area_type":"STUDY_POLYGON",
                "study_area_polygon":nc_boundary, 
                "presence_probability_cutoff":0.5, 
                "features_to_predict":None, 
                "explanatory_variable_matching":None, 
                "explanatory_distance_matching":None, 
                "explanatory_rasters_matching":None, 
                "allow_predictions_outside_of_data_ranges":"ALLOWED", 
                "resampling_scheme":"RANDOM", 
                "number_of_groups":5
            }
            # Define parameter settings to test
            parameter_grid = {
                "number_of_iterations": [10, 20],
                "basis_expansion_functions":["HINGE", "LINEAR", "THRESHOLD", "QUADRATIC"], # "PRODUCT"
                "relative_weight": [35, 50, 100],
                "number_knots":[10, 50], 
                "spatial_thinning": ["NO_THINNING", "THINNING"],
                "link_function": ["CLOGLOG"], # "LOGISTIC"
                "thinning_distance_band": ["1000 Meters", "2500 Meters"] # "5000 Meters"
            }
            
            # Get all combinations of parameters (# can vary depending on `spatial_thinning`)
            all_combinations = getAllCombos(parameter_grid)
            
            # Initialize the best combination and its corresponding evaluation metric
            files = os.listdir(model_data_path)
            if f"{s}_model_data.pickle" in files:
                # Read from previously saved model
                try:
                    with open(os.path.join(model_data_path, f"{s}_model_data.pickle"), "rb") as f:
                        cached_model_data = pickle.load(f)
                except IOError as e:
                    print(f"Error reading the file: {e}")
                best_combination = cached_model_data["combination"]
                best_evaluation_metric = cached_model_data["f1"]
            else:
                # Initialize best combo/f1
                best_combination = None
                best_evaluation_metric = 0.0
            
            # Iterate through possible parameter combinations (grid search)
            for i, combination in enumerate(all_combinations, start=1):
                params = dict(zip(parameter_grid.keys(), combination))

                # If model run previously, skip
                if checkModelLogs(log_path, params, s):
                    outputs = {
                        "output_trained_features":f"{s}_NC_Trained_Features", 
                        "output_trained_raster":f"{s}_NC_Trained_Raster",
                        "output_response_curve_table":f"{s}_NC_Response_Curve", 
                        "output_sensitivity_table":f"{s}_NC_Sensitivity_Table",
                        "output_pred_features":None, 
                        "output_pred_raster":None
                    }

                    print(f"Training model for {brd.name} with combination [{i}/{len(all_combinations)}]:")
                    arcpy.AddMessage(f"Training model for {brd.name} with combination [{i}/{len(all_combinations)}]:")
                    for k, v in zip(params.keys(), params.values()):
                        print(f"{k}: {v}")
                        arcpy.AddMessage(f"{k}: {v}")

                    # Run MaxEnt with the current set of parameters
                    runMaxEnt(static_params, params, outputs, output = False)

                    # Calculate F1 score using the output_sensitivity_table
                    score = scoreFromSensitivityTable(f"{s}_NC_Sensitivity_Table")
                    # Remove sensitivity table from gdb (will save final table)
                    arcpy.Delete_management(f"{s}_NC_Sensitivity_Table")
                    
                    # Report scoring
                    f1 = max(score.f1)
                    max_f1_index = score.f1.idxmax()
                    cutoff = score.loc[max_f1_index, 'cutoff']
                    msg_str = "===============================\n" + \
                              f"{brd.name} Combination {i} results:\n" + \
                              "-------------------------------\n" + \
                              f"Max F1: {round(f1, 4)}\n" + \
                              f"Best Cutoff: {round(cutoff, 2)}\n" + \
                              "==============================="
                    print(msg_str)
                    arcpy.AddMessage(msg_str)

                    # Write model logs
                    params.update({"f1":f1, "cutoff":round(cutoff, 2)})
                    log_file = os.path.join(log_path, f"{s}_model_log.json")
                    logModel(params, log_file)

                    # Compare the current F1 score with the best one found so far
                    if f1 > best_evaluation_metric:
                        print(f"Updating results of combination {i} to champion model for {brd.name}...")
                        arcpy.AddMessage(f"Updating results of combination {i} to champion model for {brd.name}...")
                        best_evaluation_metric = f1
                        best_combination = combination
                        # Save model data to a pickle file
                        model_data = {
                            "input_point_features":brd.fc_name,
                            "species":brd.name,
                            "f1":f1,
                            "cutoff":cutoff,
                            "score_table":score,
                            "combination":combination,
                            "params":params,
                            "other_input_values":static_params,
                            "outputs":outputs
                        }
                        out_filename = os.path.join(model_data_path, f"{s}_model_data.pickle")
                        with open(out_filename, "wb") as f:
                            pickle.dump(model_data, f)

            print(f"Best model for {brd.name}: {best_combination}, {best_evaluation_metric}")
            arcpy.AddMessage(f"Best model for {brd.name}: {best_combination}, {best_evaluation_metric}")

            # Output model results to project
            with open(os.path.join(model_data_path, f"{s}_model_data.pickle"), "rb") as f:
                cached_model_data = pickle.load(f)

            # Free up some memory using gc.collect() (Force garbage collect)
            gc.collect()
            # Set cell size to higher resolution (3x smaller than the max)
            arcpy.env.cellSize = getMinMaxCellSize()["MAX"] / 3
            print(f"Outputting best model results for {s}, with trained raster cell size set to {arcpy.env.cellSize}")
            arcpy.AddMessage(f"Outputting best model results for {s}, with trained raster cell size set to {arcpy.env.cellSize}")
            # Update static cutoff to best model cutoff
            cached_model_data["presence_probability_cutoff"] = round(cached_model_data["cutoff"], 2)
            runMaxEnt(
                    static_params=cached_model_data["other_input_values"], 
                    params=cached_model_data["params"], 
                    outputs= {
                        "output_trained_features":f"{s}_NC_Trained_Features", 
                        "output_trained_raster":f"{s}_NC_Trained_Raster",
                        "output_response_curve_table":f"{s}_NC_Response_Curve", 
                        "output_sensitivity_table":f"{s}_NC_Sensitivity_Table",
                        "output_pred_features":None, 
                        "output_pred_raster":None
                    }, 
                    output = True)
            print(f"Saved best model for {brd.name} to geodatabase.")
            arcpy.AddMessage(f"Saved best model for {brd.name} to geodatabase.")
            arcpy.env.cellSize = "MAXOF"

    print("Finished presence-only prediction batch process")
    arcpy.AddMessage("Finished presence-only prediction batch process")
    # Disable overwriting data
    arcpy.env.overwriteOutput = False