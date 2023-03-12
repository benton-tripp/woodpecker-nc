import pandas as pd
import numpy as np
import re

class Species():
    def __init__(self, dataframe:pd.DataFrame) -> None:
        self.species_code = dataframe.species_code.to_list()
        self.species_name = dataframe.species_name.to_list()
        self.family = dataframe.family.to_list()

class Bird(Species):
    def __init__(self, dataframe:pd.DataFrame, bird_name:str) -> None:
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
        self.fc_name = f"FW_{self.formatted_name}_NC"
