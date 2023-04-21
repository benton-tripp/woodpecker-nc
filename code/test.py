import itertools
import arcpy 
import pandas as pd
from birds import Bird
import pickle
from contextlib import redirect_stdout
import os


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
                "precision": TP / (TP + FP),
                "f1": 2 * ((TP / (TP + FP)) * recall) / ((TP / (TP + FP)) + recall),
            }
            for (cutoff, FP, TP, FN, TN, recall, specificity) in cursor
        ]
    df = pd.DataFrame.from_dict(vals)
    return(df)

def testBatchMaxEnt(species_df:pd.DataFrame, wspace:str) -> None:
    print("Starting batch presence-only predictions...")
    # Set workspace
    arcpy.env.workspace = wspace
    # Temporarily enable overwriting data
    arcpy.env.overwriteOutput = True

    # Create a null device to redirect the standard output
    null_device = open(os.devnull, "w")
    
    for species_name in species_df.species_name.unique():
        brd = Bird(species_df, species_name)
        s = brd.formatted_name
        print(f"Modeling {brd.name} distribution in NC using the MaxEnt algorithm...")
        
        # Define parameter settings to test
        parameter_grid = {
            "number_of_iterations": [20, 50, 100],
            "relative_weight": [50, 75, 100],
            "spatial_thinning": ["NO_THINNING", "THINNING"],
            "link_function": ["CLOGLOG", "LOGISTIC"],
            "thinning_distance_band": ["2500 Meters", "5000 Meters"]
        }
        
        # Generate all combinations of parameters
        all_combinations = list(itertools.product(*parameter_grid.values()))
        
        # Initialize the best combination and its corresponding evaluation metric
        best_combination = None
        best_evaluation_metric = 0.0
        
        for i, combination in enumerate(all_combinations, start=1):
            params = dict(zip(parameter_grid.keys(), combination))
            print(f"Training model for {brd.name} with combination {i}...")
            # Run MaxEnt with the current set of parameters
            with redirect_stdout(null_device):
                result = arcpy.stats.PresenceOnlyPrediction(input_point_features=brd.fc_name, 
                                            contains_background="PRESENCE_ONLY_POINTS", 
                                            explanatory_variables=None, #TODO
                                            presence_indicator_field=None, 
                                            distance_features=None, 
                                            # T/F -> categorical/continuous
                                            explanatory_rasters=[["nc_nlcd2019_Resample_2k", "true"], 
                                                                ["nc250", "false"],
                                                                ["avgPrecip_all_years", "false"], 
                                                                ["minTemp_all_years", "false"], 
                                                                ["maxTemp_all_years", "false"]], 
                                            basis_expansion_functions="HINGE", 
                                            number_knots=10, 
                                            study_area_type="RASTER_EXTENT", 
                                            study_area_polygon=None, 
                                            spatial_thinning="THINNING", 
                                            thinning_distance_band=params["thinning_distance_band"], 
                                            number_of_iterations=params["number_of_iterations"], 
                                            relative_weight=params["relative_weight"],  #1-100
                                            link_function=params["link_function"], 
                                            presence_probability_cutoff=0.5, 
                                            output_trained_features=f"{s}_NC_Trained_Features_{i}", 
                                            output_trained_raster=f"{s}_NC_Trained_Raster_{i}", 
                                            output_response_curve_table=f"{s}_NC_Response_Curve_{i}", 
                                            output_sensitivity_table=f"{s}_NC_Sensitivity_Table_{i}", 
                                            features_to_predict=None, 
                                            output_pred_features=None, 
                                            output_pred_raster=None, 
                                            explanatory_variable_matching=None, 
                                            explanatory_distance_matching=None, 
                                            explanatory_rasters_matching=None, 
                                            allow_predictions_outside_of_data_ranges="ALLOWED", 
                                            resampling_scheme="RANDOM", 
                                            number_of_groups=5)

            # Calculate F1 score using the output_sensitivity_table
            score = scoreFromSensitivityTable(f"{s}_NC_Sensitivity_Table_{i}")
            f1 = max(score.f1)
            cutoff = round(score.loc[score.f1 == f1].cutoff.iloc[0], 2)
            print("===============================")
            print(f"{brd.name} Combination {i} results:")
            print("-------------------------------")
            print(f"Max F1: {round(f1, 4)}")
            print(f"Best Cutoff: {cutoff}")
            print("===============================")

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
                    "input_values":result.inputValues,
                }
                with open(f"data/model_data/{s}_model_data.pickle", "wb") as f:
                    pickle.dump(model_data, f)

        print(f"Best model for {brd.name}: {best_combination}, {best_evaluation_metric}")

    print("Finished presence-only prediction batch process")
    # Disable overwriting data
    arcpy.env.overwriteOutput = False
