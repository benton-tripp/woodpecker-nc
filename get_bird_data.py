# import libraries
import pandas as pd
import numpy as np
import os

# Data from https://feederwatch.org/explore/raw-dataset-requests/

def get_species_codes(data_path:str) -> pd.DataFrame:
    """
    This function queries the Species Codes sheet from the FeederWatch Data Dictionary. The
    data is available through an excel sheet provided in the data website. This data will be 
    used to access the corresponding names and families of the different species codes.
    Returns a pandas dataframe of species (Fields: species_code, species_name, family)
    """
    print("Getting Species codes...")
    out_file_name = "species_codes.csv"
    outFile = os.path.join(data_path, out_file_name)
    if out_file_name in os.listdir(data_path):
        species = pd.read_csv(outFile)
    else:
        # First, set up the url for the data dictionary (Google Drive).
        # Credit goes to the following StackOverflow answer for re-formatting the url:
        # https://stackoverflow.com/questions/56611698/pandas-how-to-read-csv-file-from-google-drive-public
        url = 'https://drive.google.com/file/d/1kHmx2XhA2MJtEyTNMpwqTQEnoa9M7Il2/view?usp=sharing'
        url = 'https://drive.google.com/uc?id=' + url.split('/')[-2]
        # Read the Excel Sheet with the Species Codes
        species = pd.read_excel(url, sheet_name='Species Codes', header=1)
        # Filter and rename columns
        species = species[['SPECIES_CODE', 'PRI_COM_NAME_INDXD', 'FAMILY']]\
            .rename(columns={'SPECIES_CODE':'species_code', 
                            'PRI_COM_NAME_INDXD':'species_name',
                            'FAMILY':'family'})
        species.to_csv(outFile, index=False)
        print("Completed species code retrieval")
    return species

def clean_fw_data(data:pd.DataFrame, 
                  birds:pd.DataFrame, 
                  sub_national_code:list=[]) -> pd.DataFrame:
    """
    This function cleans the FeederWatch data so that it only contains 
    relevent fields, accurate (valid) data, specified birds, and specified locations.
    Args:
    - data: a pandas dataframe; raw data downloaded from FeederWatch site
    - birds: species data - output of get_species_codes(). 
             * Note: It can be a subset of this data (e.g., a specific family)
    - sub_national_code: list of `subnational1_code` fields to filter to 
    Returns a subset of the original data input, with cleaned field names.
    """
    # All available names of fields in dataset
    all_names = ['loc_id', 'latitude', 'longitude', 'subnational1_code', 
                 'entry_technique', 'sub_id', 'obs_id', 'month', 'day',
                 'year', 'proj_period_id', 'species_code', 'how_many',
                 'valid', 'reviewed', 'plus_code', 'day1_am', 'day1_pm',
                 'day2_am', 'day2_pm', 'effort_hrs_atleast', 
                 'snow_dep_atleast', 'data_entry_method']
    # Output names of fields in dataset (to be kept)
    out_names = ['species_code', 'species_name', 'how_many', 'latitude', 
                 'longitude', 'subnational1_code', 'date']
    # Preprocessing (fix column names, include/exclude fields)
    data.rename(columns=str.lower, inplace=True)
    other_names = [n for n in all_names if n not in data.columns]
    data = data.assign(**{name:np.nan for name in other_names if len(other_names) > 0})
    # Filter Data by valid, no plus_code, species, optional location
    data = data.query(f'valid == 1 & plus_code != 1 & species_code == @birds.species_code.to_list()')
    if sub_national_code is not None:
        data = data.loc[data.subnational1_code.isin(sub_national_code)]
    # Join with species (to get species name)
    data = pd.merge(data, birds, how='left', on='species_code')
    # Date formatting
    data['date'] = pd.to_datetime(dict(year=data.year, 
                                       month=data.month, 
                                       day=data.day))
    
    # Return, Ensuring correct order, specific output columns, sorted
    return data[out_names].sort_values(by=['date', 'species_name'], ascending=[True, True])

def getFeedWatcherData(outfile:str,
                       tfs:list, 
                       birds:pd.DataFrame, 
                       sub_national_code:list=[], 
                       out_dir:str='data', 
                       file_suffix:str='',
                       save_:bool=True,
                       min_year:int=2017,
                       max_year:int=2019) -> pd.DataFrame:
    """
    Gets FeederWatch data from website. When reading directly from the URLs 
    and saving the output, this can take a while (depending on internet speed).
    Each independent query (by date range) is saved to a gzipped .csv file,
    so if the process is interrupted or re-run, it can be read directly from
    that file instead of re-downloaded. Data is also cleaned/filtered (using 
    `clean_fw_data()`), then concatenated and saved to a final .csv file.
    Args: 
    - outfile: Final output file name
    - tfs: Time-frames to get data for
    - birds: Species data (Optionally) pre-filtered (e.g., by family)
    - sub_national_code: (Optionally) filter by subnational1_code (e.g., U.S. State)
    - out_dir: Directory in which to save data
    - file_suffix: Suffix of file names
    - save_: Whether or not to save the output to a gzipped file
    - min_year: minimum year to filter data
    - max_year: maximum year to filter data
    Returns a pandas dataframe of the selected FeederWatch bird data
    """
    print("Getting FeederWatch data...")
    final_out_file = os.path.join(out_dir, outfile)
    # First check if the file already exists
    if os.path.isfile(final_out_file):
        print("Data already exists; Reading from csv...")
        out = pd.read_csv(final_out_file)
        out['date'] = pd.to_datetime(out.date)
    else:
        print("Unable to find previously downloaded data; Querying data source by time frame...")
        df_lis = list()
        for i in np.arange(0, len(tfs)):
            # Read Data (either from URL, or from previously saved data if available)
            tf = tfs[i]
            out_file = os.path.join(out_dir, f'FW_{tf}_{file_suffix}.csv.gz')
            if not os.path.isfile(out_file):
                url = 'https://clo-pfw-prod.s3.us-west-2.amazonaws.com/data/PFW_' + tf + \
                    '_public.csv'
                print(f"Getting {tf} data from {url}")
                # Read/Clean data
                data = clean_fw_data(data=pd.read_csv(url), 
                                    birds=birds, 
                                    sub_national_code=sub_national_code)
                if save_:
                    # If not previously cached, save as gzip
                    print(f"Saving {tf} data to {out_file}")
                    data.to_csv(out_file, compression='gzip', index=False)
            else:
                print(f"Reading {tf} data from {out_file}")
                data = pd.read_csv(out_file, compression='gzip')
                data['date'] = pd.to_datetime(data.date)
            # Append to list
            df_lis.append(data)
        # Combine list into single dataframe
        print("Concatenating list of dataframes")
        out = pd.concat(df_lis)
        # Filter by date
        out = out[out['date'].dt.year >= min_year]
        out = out[out['date'].dt.year <= max_year]
        # Save to file
        out.to_csv(final_out_file, index=False)
    print("Completed FeederWatch data retrieval")
    return out

# Timeframes available in FeederWatch:
# '1988_1995', '1996_2000', '2001_2005', '2006_2010', 
# '2011_2015', '2016_2020', '2021'
