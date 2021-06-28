import os, re
from collections import defaultdict
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent
source_data_dir = 'Source/DravLex/'

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from phonetic_distance import *
from auxiliary_functions import csv_to_dict
os.chdir(local_dir)

#%%
#LOAD LANGUAGE DATA CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Dravidian'}

#%%
#LOAD DRAVIDIAN DATASET
forms_data = csv_to_dict(source_data_dir + 'forms.csv')
dravidian_langs_data = csv_to_dict(source_data_dir + 'languages.csv')
dravidian_langs = {dravidian_langs_data[i]['ID']:(dravidian_langs_data[i]['Name'],
                                                  dravidian_langs_data[i]['Glottocode'],
                                                  dravidian_langs_data[i]['ISO639P3code'])
                   for i in dravidian_langs_data}

#%%
#LOAD COGNATE SET CODES

cognate_data = csv_to_dict(source_data_dir + 'cognates.csv')
cognate_dict = {cognate_data[i]['ID']:cognate_data[i]['Cognateset_ID'] 
                for i in cognate_data}

cognate_sets = set(cognate_dict.values())
cognate_set_dict = defaultdict(lambda:[])
for cognate_set in cognate_sets:
    gloss, letter = cognate_set.split('-')
    cognate_set_dict[gloss].append(letter)
    cognate_set_dict[gloss] = sorted(cognate_set_dict[gloss])

#%%
#LOAD CONCEPTICON MAPPING
concepticon_data = csv_to_dict('Source/Concept_list_Kolipakam_2018_100.csv', sep='\t')
concepticon_dict = {concepticon_data[i]['Name'].split(' [')[0]:concepticon_data[i]['Parameter']
                    for i in concepticon_data}

#%%
conversion_dict = {#Consonants
                   'ḍ':'ɖ', #Kannada, Parji; retroflex
                   'g':'ɡ', #not proper IPA character
                   'ḻ':'ɻ', #Malayalam, Tamil; retroflex
                   'M':'m', #Tulu, probably typo
                   'ṉ':'n', #Tamil; alveolar
                   'ṇ':'ɳ', #Malayalam, Kannada, Tamil; retroflex
                   'ñ':'ɲ', #Parji; palatal
                   'ṅ':'ŋ', #Malayalam, Tamil, Parji; velar
                   'r':'ɾ', #tap -- seems to be default unless marked as trill (but confirm this)
                   'ṟ':'r', #Tamil, Malayalam, Telugu; alveolar trill
                   'ṛ':'ɽ', #Parji; retroflex
                   'ṣ':'ʂ', #Malayalam, Kannada; retroflex
                   'ṭ':'ʈ', #Malayalam, Telugu, Kannada, Parji, Tamil; retroflex
                   
                   #Vowels
                   'ā':'aː', #Parju, Kannada, Malayalam, Tamil, Telugu
                   'ã':'ã', #change from single character to /a/ with nasal diacritic
                   'ē':'ẽ', #change from single character to /е/ with nasal diacritic
                   'ī':'ĩ', #change from single character to /i/ with nasal diacritic
                   'ō':'õ', #change from single character to /o/ with nasal diacritic
                   'ū':'ũ', #change from single character to /u/ with nasal diacritic
                   'Ɛ':'e', #Brahui; seems like it should be /ɛ/, but not so according to https://en.wikipedia.org/wiki/Brahui_language#Phonology
                   
                   #Other symbols
                   ':':'ː', #colon to length symbol
                   '"':'', #spurious quotation marks, remove
                   '/':'', #marks transcription, not needed, remove
                   '-':'' #marks stem/root, remove
                   
    }

def has_parentheses(string):
    if ')' in string:
        return True
    elif '(' in string:
        return True
    else:
        return False

def has_brackets(string):
    if ']' in string:
        return True
    elif '[' in string:
        return True
    else:
        return False

def fix_tr(word):
    #Convert characters using conversion dictionary
    word = ''.join([conversion_dict.get(ch, ch) for ch in word])
    
    #Standard affricates
    ligatures = ['ʦ', 'ʣ', 'ʧ', 'ʤ', 'ʨ', 'ʥ']
    double_ch = ['ts', 'dz', 'tʃ', 'dʒ', 'tɕ', 'dʑ']
    for aff_pair in zip(ligatures, double_ch):
        lig, double = aff_pair
        word = re.sub(double, lig, word)
    
    #Remove parenthetical/bracket annotations
    while has_parentheses(word) == True:
        word = re.sub(r'\([^()]*\)', '', word)
    while has_brackets(word) == True:
        word = re.sub(r'\[[^()]*\]', '', word)
    
    return word

#%%

dravidian_data = defaultdict(lambda:{})
index = 0
for i in forms_data:
    entry = forms_data[i]
    word_id = entry['ID']
    lang_id = entry['Language_ID']

    new_name, glottocode, iso_code = lang_data[lang_id]
    concept = entry['Parameter_ID']
    concepticon_gloss = concepticon_dict[concept]
    
    cognate_id = cognate_dict[word_id]
    gloss, letter = cognate_id.split('-')
    cognate_set_id = cognate_set_dict[gloss].index(letter) + 1
    cognate_id = '_'.join([concepticon_gloss, str(cognate_set_id)])
    
    tr = entry['Form']
    variants = tr.split(' ~ ')
    for variant in variants:
        index += 1
        new_entry = dravidian_data[index]
        new_entry['ID'] = '_'.join([lang_id, str(cognate_id)])
        new_entry['Language_ID'] = new_name
        new_entry['Glottocode'] = glottocode
        new_entry['ISO 639-3'] = iso_code
        new_entry['Parameter_ID'] = concepticon_gloss
        new_entry['Value'] = variant
        new_entry['Form'] = fix_tr(variant)
        new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
        new_entry['Source_Form'] = entry['Form']
        new_entry['Cognate_ID'] = cognate_id
        new_entry['Loan'] = str(entry['status'] == 'LOAN').upper()
        new_entry['Comment'] = entry['source_comment']
        new_entry['Source'] = entry['Source']

#%%
#CHECKING PHONETIC CHARACTERS
dravidian_phones = set([ch for i in dravidian_data
                   for ch in dravidian_data[i]['Form']])

new_chs = set(phone for phone in dravidian_phones 
                  if phone not in all_sounds+diacritics+[' '])

def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(dravidian_data[i]['Language_ID'] for i in dravidian_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in dravidian_data:
        entry = dravidian_data[i]
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
output_file = 'dravidian_data.csv'
print(f'Writing preprocessed Dravidian data to "{output_file}"...')

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
            
write_data(dravidian_data, output_file=output_file)