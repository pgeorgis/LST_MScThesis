import os, re
from collections import defaultdict
from pathlib import Path
import pandas as pd
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent
source_data_dir = 'Source/leejaponic/'

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
             if lang_data['Dataset'][i] == 'Japonic'}

#%%
#LOAD JAPONIC DATASET
forms_data = pd.read_csv(source_data_dir + 'cldf/forms.csv')
japonic_langs_data = csv_to_dict(source_data_dir + 'cldf/languages.csv')
japonic_langs = {japonic_langs_data[i]['ID']:(japonic_langs_data[i]['Name'], 
                                              japonic_langs_data[i]['Glottocode'], 
                                              japonic_langs_data[i]['ISO639P3code'])
                   for i in japonic_langs_data}

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
#LOAD SOURCES
source_dict = {'122469':'Hirayama, 1988',
               '476171':'Lee & Hasegawa, 2011',
               'Jodaigojiten1967;YasumotoHonda1978':'Jōdaigo Jiten Henshū Iinkai 上代語辞典編集委員会, 1967; Yasumoto & Honda, 1978',
               'Muromachijidaigo2001':'Muromachi Jidaigo Jiten Henshū Iinkai 室町時代語辞典編修委員会, 2001'}

    
#%%
conversion_dict = {#Consonants 
                   'g':'ɡ', #replace with proper IPA character
                   
                   #Affricates 
                    'ts':'ʦ', 
                    'tʃ':'ʧ',
                    'dʒ':'ʤ',
                   
                   #Vowels
                   'ö':'ø', #according to transcription conventions
                   'ë':'ə', #according to transcription conventions
                   'ă':'ḁ', #presumbly voiceless vowel
                   'ĭ':'i̥', #presumbly voiceless vowel
                   'ŭ':'u̥', #presumbly voiceless vowel
                   }


def fix_tr(tr):
    segments = tr.split()
    fixed = []
    for seg in segments:
        seg = seg.split('/')[-1] #some segments transcribed as, e.g. <ï/ɨ> --> simply take the last part
        
        for seq in conversion_dict:
            seg = re.sub(seq, conversion_dict[seq], seg)
        
        fixed.append(seg)
    
    fixed = ''.join(fixed)
    
    #Convert /dz/ to /ʣ/ (not originally segmented as affricate in source)
    fixed = re.sub('dz', 'ʣ', fixed)
    
    return fixed

japonic_data = defaultdict(lambda:{})
index = 0
for index, entry in forms_data.iterrows():
    word_id = entry['ID']
    lang_id = entry['Language_ID']

    #Filter only languages in languages.csv
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
    
    new_entry = japonic_data[index]
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
    new_entry['Source'] = source_dict[entry['Source']] if type(entry['Source']) != float else ''

#%%
#CHECKING PHONETIC CHARACTERS
japonic_phones = set([ch for i in japonic_data
                   for ch in japonic_data[i]['Form']])

new_chs = set(phone for phone in japonic_phones 
              if phone not in all_sounds+diacritics+[' '])

def lookup_segment(segment, data=japonic_data, langs=None):
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
output_file = 'japonic_data.csv'
print(f'Writing preprocessed Japonic data to "{output_file}"...')

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
            
write_data(japonic_data, output_file=output_file)
