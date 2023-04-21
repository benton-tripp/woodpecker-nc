# https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-statistics/presence-only-prediction.htm
import itertools
import arcpy 
import pandas as pd
from birds import Bird
import pickle
from math import inf
import os
from datetime import datetime
import json

def getPrecision(TP:float, FP:float) -> float:
    try:
        return TP / (TP + FP)
    except ZeroDivisionError:
        return -inf

def getF1(TP:float, FP:float, recall:float) -> float:
    try:
        return 2 * ((TP / (TP + FP)) * recall) / ((TP / (TP + FP)) + recall)
    except ZeroDivisionError:
        return -inf

def scoreFromSensitivityTable(sensitivity_table: str) -> float:
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

# Check if model already run previously
def checkModelLogs(log_path:str, params:dict, species:str) -> bool:
    files = [f for f in os.listdir(log_path) if species in f]
    for file in files:
        file_path = os.path.join(log_path, file)
        with open(file_path, 'r') as f:
            file_dict = json.load(f)
            del file_dict["f1"]
            del file_dict["cutoff"]
            if file_dict == params:
                return False
    return True

def getAllCombos(parameter_grid:dict) -> dict:
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

def runMaxEnt(static_params:dict, params:dict, outputs:dict, output:bool = False) -> arcpy.stats.PresenceOnlyPrediction:
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

def batchMaxEnt(species_df:pd.DataFrame, wspace:str, data_path:str) -> None:
    print("Starting batch presence-only predictions...")
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
        
        # Check if species already in gdb; If yes, just load model 
        if f"{s}_NC_Trained_Features" in arcpy.ListFeatureClasses():
            print("Modeling already completed for {brd.name} for this project. " + \
                  "To continue, please delete the trained features output by the model" + \
                  "from the default geodatabase.")
        else:
            # Non-changing parameters (written out so that they can be saved)
            static_params = {
                "input_point_features":brd.fc_name,
                "contains_background":"PRESENCE_ONLY_POINTS", 
                "explanatory_variables":None,
                "presence_indicator_field":None,
                "distance_features":None, 
                # T/F -> categorical/continuous
                "explanatory_rasters":[["nc_nlcd2019_Resample_2k", "true"],
                                    ["nc250", "false"],
                                    ["avgPrecip_all_years", "false"],
                                    ["minTemp_all_years", "false"],
                                    ["maxTemp_all_years", "false"]],
                "study_area_type":"STUDY_POLYGON",
                "study_area_polygon":"nc_state_boundary", 
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
                with open(os.path.join(model_data_path, f"{s}_model_data.pickle"), "rb") as f:
                    cached_model_data = pickle.load(f)
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
                    for k, v in zip(params.keys(), params.values()):
                        print(f"{k}: {v}")

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
                    print("===============================")
                    print(f"{brd.name} Combination {i} results:")
                    print("-------------------------------")
                    print(f"Max F1: {round(f1, 4)}")
                    print(f"Best Cutoff: {round(cutoff, 2)}")
                    print("===============================")

                    # Write model logs
                    params.update({"f1":f1, "cutoff":round(cutoff, 2)})
                    log_file = os.path.join(log_path, f"{s}_model_log" + datetime.now().strftime('%Y%m%d%H%M%S') + ".log")
                    with open(log_file, "w") as f:
                        json.dump(params, f)

                    # Compare the current F1 score with the best one found so far
                    if f1 > best_evaluation_metric:
                        print(f"Updating results of combination {i} to champion model for {brd.name}...")
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

            # Output model results to project
            with open(os.path.join(model_data_path, f"{s}_model_data.pickle"), "rb") as f:
                cached_model_data = pickle.load(f)
            # Update static cutoff to best model cutoff
            cached_model_data["presence_probability_cutoff"] = round(cached_model_data["cutoff"], 2)
            cached_model_data["other_input_values"]["presence_probability_cutoff"] = round(cached_model_data["cutoff"], 2)
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

    print("Finished presence-only prediction batch process")
    # Disable overwriting data
    arcpy.env.overwriteOutput = False

with open("C:/Users/bento/final_project/woodpeckerNC/data/species_df.pickle", "rb") as f:
    species_df = pickle.load(f)

wspace="C:/Users/bento/final_project/woodpeckerNC/woodpeckerNC.gdb"
data_path="C:/Users/bento/final_project/woodpeckerNC/data"

batchMaxEnt(species_df, wspace, data_path)