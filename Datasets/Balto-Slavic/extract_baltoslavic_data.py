import os
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict
os.chdir(local_dir)

#Load Balto-Slavic data from NorthEuraLex
bs_NEL_data = csv_to_dict('balto_slavic_NEL_data.csv', sep='\t')


#Load Balto-Slavic data from Global Lexicostatistical Database
bs_GLD_data = csv_to_dict('balto_slavic_gld_data.csv', sep='\t')


#Get lists of the languages in each dataset
NEL_langs = set(bs_NEL_data[i]['Language_ID'] for i in bs_NEL_data)
GLD_langs = set(bs_GLD_data[i]['Language_ID'] for i in bs_GLD_data)


#Lithuanian and Latvian are the only languages which overlap; take them from NEL
combined_BaltoSlav_data = {}
index = 0
for i in bs_NEL_data:
    index += 1
    combined_BaltoSlav_data[index] = bs_NEL_data[i]
for i in bs_GLD_data:
    if bs_GLD_data[i]['Language_ID'] not in ['Latvian', 'Lithuanian']:
        index += 1
        combined_BaltoSlav_data[index] = bs_GLD_data[i]
        
#Get list of languages in resulting combined dictionary
combined_langs = set(combined_BaltoSlav_data[i]['Language_ID'] for i in combined_BaltoSlav_data)

#CREATE PROCESSED DATA FILE
def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[1]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            values = sep.join([str(data_dict[i][feature]) for feature in features])
            f.write(f'{values}\n')

write_data(combined_BaltoSlav_data, 'balto_slavic_data.csv')    