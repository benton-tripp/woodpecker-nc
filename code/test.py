import os
import pickle
import pandas as pd
from birds import Bird

with open("data/species_df.pickle", "rb") as f:
    species_df = pickle.load(f)

model_data_path = "data/model_data"
# Initialize the best combination and its corresponding evaluation metric
files = os.listdir(model_data_path)

models = dict()
for species_name in species_df.species_name.unique():
    brd = Bird(species_df, species_name)
    s = brd.formatted_name
    if f"{s}_model_data.pickle" in files:
        # Read from previously saved model
        try:
            with open(os.path.join(model_data_path, f"{s}_model_data.pickle"), "rb") as f:
                models.update({s :pickle.load(f)})
        except IOError as e:
            print(f"Error reading the file: {e}")

data = [{k:models[k]["params"]} for k in models.keys()]
df = pd.DataFrame([{"Key": k, **v} for d in data for k, v in d.items()])


        