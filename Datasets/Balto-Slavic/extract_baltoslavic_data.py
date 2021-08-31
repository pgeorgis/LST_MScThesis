import os, re
from pathlib import Path
from openpyxl import load_workbook
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#%%
#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict, strip_ch
os.chdir(local_dir)

#%%
#Load Balto-Slavic data from NorthEuraLex
bs_NEL_data = csv_to_dict('Source/balto_slavic_NEL_data.csv', sep='\t')


#Load Balto-Slavic data from Global Lexicostatistical Database
bs_GLD_data = csv_to_dict('Source/balto_slavic_gld_data.csv', sep='\t')


#Get lists of the languages in each dataset
NEL_langs = set(bs_NEL_data[i]['Language_ID'] for i in bs_NEL_data)
GLD_langs = set(bs_GLD_data[i]['Language_ID'] for i in bs_GLD_data)

#%%
#Combine datasets
#Lithuanian and Latvian are the only languages which overlap; take them from GLD
combined_BaltoSlav_data = {}
index = 0
for i in bs_NEL_data:
    if bs_NEL_data[i]['Language_ID'] not in ['Latvian', 'Lithuanian']:
        index += 1
        combined_BaltoSlav_data[index] = bs_NEL_data[i]
for i in bs_GLD_data:
    index += 1
    combined_BaltoSlav_data[index] = bs_GLD_data[i]

#%%
#Load gold cognate annotations
gold_cognates = load_workbook('Source/baltoslavic_gold_cognate_classes.xlsx')
gold_cognates = gold_cognates['Sheet']
gold_rows = list(range(1,len(list(gold_cognates.rows))+1))
gold_columns = [i[0].column_letter for i in list(gold_cognates.columns)][:-3] #only include until column Q, which is the last row of data; beyond that is annotation key

#Dictionary of language labels with the column they appear in
language_columns = {gold_cognates[f'{c}1'].value:c for c in gold_columns[1:]}

def fix_tr(tr):
    """Corrects transcription of gold cognate entry"""
    #Remove '\ufeff' character and spaces
    tr = strip_ch(tr, ['\ufeff', ' '])
    
    #Convert characters back to IPA, which were distorted when running LingPy/LexStat
    #for preliminary cognate clustering
    tr_fixes = {'à':'à',
                'á':'á',
                'â':'â',
                'ǎ':'ǎ',
                'ā':'ā',
                'ǣ':'ǣ',
                'é':'é',
                'ê':'ê',
                'ě':'ě',
                'ì':'ì',
                'í':'í',
                'î':'î',
                'ī':'ī',
                'ǐ':'ǐ',
                'ó':'ó',
                'ô':'ô',
                'ǒ':'ǒ',
                'ř':'ř',
                'ù':'ù',
                'ú':'ú',
                'û':'û',
                'ū':'ū',
                'ǔ':'ǔ',
                '̩̂':'̩̂',
                }
    
    for non_ipa_ch in tr_fixes:
        tr = re.sub(non_ipa_ch, tr_fixes[non_ipa_ch], tr)
    
    return tr
    

def get_color(sheet, cell):
    """Returns the hexadecimal color value of a particular cell, e.g. cell 'K44'"""
    return str(sheet[cell].fill.start_color.index) #hexadecimal


#Create a dictionary with word forms and their cognate classes
cognate_IDs = {}
for language in language_columns:
    c = language_columns[language]
    
    #Split by '~' for doublets, fix transcription, index by cognate ID
    #Skip cognate sets marked in red, which have not been corrected
    forms_ID = {gold_cognates[f'A{r}'].value:[fix_tr(form) for form in gold_cognates[f'{c}{r}'].value.split('~')]
        for r in gold_rows[1:]
        if gold_cognates[f'{c}{r}'].value != None
        if get_color(gold_cognates, f'A{r}') != 'FFFF0000'}
    
    #Add to cognate_IDs dict such that keys are (language, IPA, concept) and the values are the cognate ID
    for cognate_ID in forms_ID:
        concept = '_'.join(cognate_ID.split('_')[:-1])
        for form in forms_ID[cognate_ID]:
            cognate_IDs[(language, form, concept)] = cognate_ID

#%%
issues = []
red_i = []

#Iterate through combined datasets and relabel cognate IDs as those from gold annotations  
for i in combined_BaltoSlav_data:
    entry = combined_BaltoSlav_data[i]
    language, tr, concept = entry['Language_ID'], entry['Form'], entry['Parameter_ID']
    try:
        cognate_ID = cognate_IDs[(language, fix_tr(tr), concept)]
        entry['Cognate_ID'] = cognate_ID
    except KeyError:
        print(f"Couldn't find cognate class for {language} /{tr}/ '{concept}'!")
        issues.append((language, tr, concept))
        red_i.append(i)

#Delete entries from unannotated cognate sets
for i in red_i:
    del combined_BaltoSlav_data[i]


#%%
#Get list of languages in resulting combined dictionary
combined_langs = set(combined_BaltoSlav_data[i]['Language_ID'] for i in combined_BaltoSlav_data)

#%%
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
   