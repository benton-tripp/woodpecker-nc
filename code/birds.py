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
