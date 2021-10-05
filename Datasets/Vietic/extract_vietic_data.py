import os, re
from collections import defaultdict
from pathlib import Path
import pandas as pd
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent
source_data_dir = 'Source/sidwellvietic/'

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
             if lang_data['Dataset'][i] == 'Vietic'}


#%%
#LOAD VIETIC DATASET
forms_data = pd.read_csv(source_data_dir + 'cldf/forms.csv')
vietic_langs_data = csv_to_dict(source_data_dir + 'cldf/languages.csv')
vietic_langs_data = {vietic_langs_data[i]['ID']:(vietic_langs_data[i]['Name'], 
                                                 vietic_langs_data[i]['Glottocode'], 
                                                 vietic_langs_data[i]['ISO639P3code'])
                   for i in vietic_langs_data}

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
conversion_dict = {#Consonants
                   'g':'ɡ', #convert to proper IPA character
                   'dʑ':'ʥ',
                   'dʒ':'ʤ',
                   'kp':'k͡p',
                   'tɕ':'ʨ',
                   'ŋm':'ŋ͡m',
                   
                   
                   #Vowels
                   'ă':'ă', #/a/ with extra short diacritic
                   'ḛ':'ḛ', #/e/ with creaky diacritic
                   'ḭ':'ḭ', #/i/ with creaky diacritic
                   'ĭ':'ĭ', #/i/ with extra short diacritic
                   'õ':'õ', #/o/ with nasal diacritic
                   'ŏ':'ŏ', #/o/ with extra short diacritic
                   'ṵ':'ṵ', #/u/ with creaky diacritic
                   'ŭ':'ŭ', #/u/ with extra short diacritic
                   'ᵊ':'ə̯', #presumably schwa onset to diphthong
                   
                   #Diphthongs
                   # 'ae':'a̯e',
                   # 'aə':'a̯ə',
                   # 'ao':'a̯o',
                   # 'ei':'ei̯',
                   
                   #Other
                   '\+':'',
                   }

digraphs = []
slashes = []
def fix_tr(tr, lang):
    segments = tr.split()
    fixed = []
    for seg in segments:
        if '/' in seg:
            slashes.append(seg)
            seg = seg.split('/')[-1] #some segments transcribed as, e.g. <δ/ð> to denote tone --> simply take the last part
        
        for seq in conversion_dict:
            seg = re.sub(seq, conversion_dict[seq], seg)
        seg = re.sub('̯̯', '̯', seg) #remove double non-syllabic diacritics
        if len(seg) > 1: 
            digraphs.append(seg)
        
        fixed.append(seg)
    
    fixed = ''.join(fixed)
    
    if lang == 'Vietnamese':
        fixed = re.sub('ð', 'ɗ', fixed) #typo mistake in source
        
        if fixed == 'ɗuoi': #this word was not properly transcribed into IPA in source
            fixed = 'ɗuəi̯'
            fixed += '³³' #tone mising in this word
        
    
    return fixed

skipped = []
skipped_cognates = []
vietic_data = defaultdict(lambda:{})
index = 0
for index, entry in forms_data.iterrows():
    word_id = entry['ID']
    lang_id = entry['Language_ID']

    #Filter only languages in languages.csv
    try:
        new_name, glottocode, iso_code = lang_data[lang_id]
    except KeyError:
        skipped.append(lang_id)
        continue 
    
    concept = entry['Parameter_ID']
    concepticon_gloss = concepticon_dict[concept]
    
    cognate_id = cognate_dict[word_id]
    cognate_id = '_'.join([concepticon_gloss, str(cognate_id)])
    
    tr = entry['Segments']
    
    #skip nan entries
    if type(entry['Value']) == float:
        continue
    if type(entry['Segments']) == float:
        continue
    
    index += 1
    
    new_entry = vietic_data[index]
    new_entry['ID'] = '_'.join([re.sub('-', '_', new_name), str(cognate_id)])
    new_entry['Language_ID'] = new_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code if type(iso_code) != float else ''
    new_entry['Parameter_ID'] = concepticon_gloss
    new_entry['Value'] = entry['Value']
    new_entry['Form'] = fix_tr(tr, new_name)
    new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
    new_entry['Source_Form'] = tr
    new_entry['Cognate_ID'] = cognate_id
    new_entry['Loan'] = entry['Comment'].upper() if type(entry['Comment']) != float else ''
    new_entry['Comment'] = entry['Comment'] if type(entry['Comment']) != float else ''
    new_entry['Source'] = entry['Source'] if type(entry['Source']) != float else ''

#%%
#CHECKING PHONETIC CHARACTERS
vietic_phones = set([ch for i in vietic_data
                   for ch in vietic_data[i]['Form']])

new_chs = set(phone for phone in vietic_phones 
              if phone not in all_sounds+diacritics+tonemes+[' '])

def lookup_segment(segment, data=vietic_data, langs=None):
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
output_file = 'vietic_data.csv'
print(f'Writing preprocessed Vietic data to "{output_file}"...')

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
            
write_data(vietic_data, output_file=output_file)