import os, re
from collections import defaultdict
from pathlib import Path
import pandas as pd
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent
source_data_dir = 'Source/crossandean/'

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict
from phonetic_distance import *
os.chdir(local_dir)

#%%
#LOAD LANGUAGE DATA CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Quechuan'}

#%%
#LOAD QUECHUAN DATASET
forms_data = pd.read_csv(source_data_dir + 'cldf/forms.csv')
quechuan_langs_data = csv_to_dict(source_data_dir + 'cldf/languages.csv')
quechuan_langs = {quechuan_langs_data[i]['ID']:(quechuan_langs_data[i]['Name'],
                                                quechuan_langs_data[i]['Glottocode'],
                                                quechuan_langs_data[i]['ISO639P3code'])
                   for i in quechuan_langs_data}

#%%
#LOAD COGNATE SET CODES
cognate_data = csv_to_dict(source_data_dir + 'cldf/cognates.csv')
cognate_dict = {cognate_data[i]['Form_ID']:cognate_data[i]['Cognateset_ID'] 
                for i in cognate_data}

cognate_set_dict = defaultdict(lambda:[])
for form_ID in cognate_dict:
    gloss = form_ID.split('_')[1].split('-')[0]
    cognate_set_dict[gloss].append(cognate_dict[form_ID])
    cognate_set_dict[gloss] = list(set(cognate_set_dict[gloss]))
    

#%%
#LOAD CONCEPTICON MAPPING
concept_data = pd.read_csv(source_data_dir + 'cldf/parameters.csv')
concepticon_dict = {concept_data['ID'][i]:concept_data['Concepticon_Gloss'][i] 
                    for i in range(len(concept_data))}
    
#%%
conversion_dict = {'g':'ɡ', #replace with proper IPA character
                   ':':'ː', #long symbol
                   '’':'ʼ', #ejective
                   '+':' ' #replace morphological segmentation with space
                   }

aff_diph_conversion = {#Affricates
                       'ts':'ʦ',
                       'tʃ':'ʧ', 
                       'dʒ':'ʤ', 
                       'dʑ':'ʥ',
                       'ʈʂ':'ʈ͡ʂ',
                       
                       #Diphthongs
                       'ai':'ai̯',
                       'au':'au̯',
                       'ie':'i̯e',
                       'oi':'oi̯',
                       'ue':'u̯e',
                       'ui':'u̯i'}


def fix_tr(tr):
    segments = tr.split()
    fixed = []
    for seg in segments:
        seg = ''.join([conversion_dict.get(ch, ch) for ch in seg])
        
        #Correct affricates and diphthongs
        for seq in aff_diph_conversion:
            seg = re.sub(seq, aff_diph_conversion[seq], seg)
        
        fixed.append(seg)
    
    return ''.join(fixed)

quechuan_data = defaultdict(lambda:{})
index = 0
for index, entry in forms_data.iterrows():
    word_id = entry['ID']
    lang_id = entry['Language_ID']

    #Filter only Quechuan languages in languages.csv
    #(original dataset also includes Quechuan languages without Glottocodes,
    #as well as Aymaran and Uri-Chipaya languages)
    try:
        new_name, glottocode, iso_code = lang_data[lang_id]
    except KeyError:
        continue 
    
    concept = entry['Parameter_ID']
    concepticon_gloss = concepticon_dict[concept]
    
    cognate_id = cognate_dict[word_id]
    cognate_id = '_'.join([concepticon_gloss, str(cognate_id)])
    
    tr = entry['Segments']
    
    #skip nan entries
    if type(entry['Value']) == float:
        continue
    
    index += 1
    
    new_entry = quechuan_data[index]
    new_entry['ID'] = '_'.join([lang_id, str(cognate_id)])
    new_entry['Language_ID'] = new_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code if type(iso_code) != float else ''
    new_entry['Parameter_ID'] = concepticon_gloss
    new_entry['Value'] = entry['Value']
    new_entry['Form'] = fix_tr(tr)
    new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
    new_entry['Source_Form'] = tr
    new_entry['Cognate_ID'] = cognate_id
    new_entry['Loan'] = ''
    new_entry['Comment'] = entry['Comment'] if type(entry['Comment']) != float else ''
    new_entry['Source'] = entry['Source'] if type(entry['Source']) != float else ''

#%%
#CHECKING PHONETIC CHARACTERS
quechuan_phones = set([ch for i in quechuan_data
                   for ch in quechuan_data[i]['Form']])

new_chs = set(phone for phone in quechuan_phones 
              if phone not in all_sounds+diacritics+[' '])

def lookup_segment(segment, data=quechuan_data, langs=None):
    if langs == None:
        langs = set(data[i]['Language_ID'] for i in data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in data:
        entry = data[i]
        lang = entry['Language_ID']
        if lang in langs:
            tr = entry['Form']
            orth = entry['Value']
            gloss = entry['Parameter_ID']
            if segment in tr:
                occurrences[lang][segment].append((orth, tr, gloss))
    for lang in occurrences:
        for segment in occurrences[lang]:
            print(f'Occurrences of <{segment}> in {lang}:')
            for entry in occurrences[lang][segment]:
                orth, tr, gloss = entry
                print(f'<{orth}> /{tr}/ "{gloss}"')
            print('\n')

#%%
output_file = 'quechuan_data.csv'
print(f'Writing preprocessed Quechuan data to "{output_file}"...')

def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            try:
                values = sep.join([data_dict[i][feature] for feature in features])
            except TypeError:
                print(i, data_dict[i])
            f.write(f'{values}\n')
            
write_data(quechuan_data, output_file=output_file)