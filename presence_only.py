# https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-statistics/presence-only-prediction.htm
import arcpy 

def batchMaxEnt(species:list) -> None:
    print("Starting batch presence-only predictions...")
    for s in species:
        print(f"Modeling {s} distribution in NC using the MaxEnt algorithm")
        arcpy.stats.PresenceOnlyPrediction(input_point_features=f"FW_{s}_NC", 
                                        contains_background="PRESENCE_ONLY_POINTS", 
                                        explanatory_variables=None, #TODO
                                        presence_indicator_field=None, 
                                        distance_features=None, 
                                        explanatory_rasters=[["nc_nlcd2019_Resample_1k", "true"], 
                                                            ["nc250", "false"]], 
                                        basis_expansion_functions="HINGE", 
                                        number_knots=10, 
                                        study_area_type="RASTER_EXTENT", 
                                        study_area_polygon=None, 
                                        spatial_thinning="THINNING", 
                                        thinning_distance_band="2500 Meters", 
                                        number_of_iterations=20, 
                                        relative_weight=100,  #1-100
                                        link_function="CLOGLOG", 
                                        presence_probability_cutoff=0.5, 
                                        output_trained_features=f"{s}_NC_Trained_Features", 
                                        output_trained_raster=f"{s}_NC_Trained_Raster", 
                                        output_response_curve_table=f"{s}_NC_Response_Curve", 
                                        output_sensitivity_table=f"{s}_NC_Sensitivity_Table", 
                                        features_to_predict=None, 
                                        output_pred_features=None, 
                                        output_pred_raster=None, 
                                        explanatory_variable_matching=None, 
                                        explanatory_distance_matching=None, 
                                        explanatory_rasters_matching=None, 
                                        allow_predictions_outside_of_data_ranges="ALLOWED", 
                                        resampling_scheme="RANDOM", 
                                        number_of_groups=5)
    print("Finished presence-only prediction batch process")