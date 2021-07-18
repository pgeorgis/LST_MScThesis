import os, re
from collections import defaultdict
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict, strip_ch
os.chdir(str(grandparent_dir) + '/Code/Distance_Measures/')
from phonetic_distance import *
os.chdir(local_dir)


#%%
#LOAD LANGUAGE CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Sinitic'}

#%%
#LOAD DATASET
forms_data = csv_to_dict('Source/cldf/forms.csv')
sinitic_data = defaultdict(lambda:{})

sinitic_concepts = csv_to_dict('Source/cldf/parameters.csv')
concept_dict = {sinitic_concepts[i]['ID']:sinitic_concepts[i]['Concepticon_Gloss'] 
                for i in sinitic_concepts}

sinitic_cognates = csv_to_dict('Source/cldf/cognates.csv')
sinitic_cognates = {sinitic_cognates[i]['Form_ID']:sinitic_cognates[i]['Cognateset_ID'] 
                    for i in sinitic_cognates}

liu_sinitic = csv_to_dict('Source/raw/liusinitic.tsv', sep='\t')


cognate_sets = defaultdict(lambda:defaultdict(lambda:[]))
cognate_id_lookup = {}
for i in forms_data:
    entry = forms_data[i]
    word_id = entry['ID']
    gloss = concept_dict[entry['Parameter_ID']]
    cognacy = sinitic_cognates[word_id]
    cognate_sets[gloss][cognacy].append(i)
for gloss in cognate_sets:
    sets = sorted(list(cognate_sets[gloss].keys()))
    for i in range(len(sets)):
        cognate_set = cognate_sets[gloss][sets[i]]
        set_i = i+1
        for j in cognate_set:
            cognate_id_lookup[j] = set_i

#%%
#Sinological symbols with standard IPA equivalents:
#https://en.wikipedia.org/wiki/Sinological_extensions_to_the_International_Phonetic_Alphabet

def fix_tr(tr):
    fix_ch = {'ã':'ã', #vowel with tilde --> vowel + nasal diacritic
              'ẽ':'ẽ', #vowel with tilde --> vowel + nasal diacritic
              'ĩ':'ĩ', #vowel with tilde --> vowel + nasal diacritic
              'õ':'õ', #vowel with tilde --> vowel + nasal diacritic
              'ũ':'ũ', #vowel with tilde --> vowel + nasal diacritic
              'g':'ɡ', #incorrect IPA symbol
              'ʅ':'ɻ̩', #Sinological phonetic character, convert to standard IPA equivalent
              'ɿ':'ɹ̩', #Sinological phonetic character, convert to standard IPA equivalent
              'ʯ':'ɻ̩ʷ',#Sinological phonetic character, convert to standard IPA equivalent
              'ȵ':'ɲ',#Sinological phonetic character, convert to standard IPA equivalent; technically [n̠ʲ], but [ɲ] is close enough 
              'ᴀ':'ä', #Sinological character for open central unrounded vowel /ä/
              'ᴇ':'ɛ', #mapped to /ɛ/ in raw/prepare.py
              
              '+':'', #morpheme segmentation, remove
              '*':'', #unclear purpose, but doesn't appear in segmented IPA, remove
              }
    tr = ''.join([fix_ch.get(ch, ch) for ch in tr])
    
    #convert two-symbol affricates into single symbols
    affricate_conversion = {'ts':'ʦ',
                            'dz':'ʣ',
                            'tʃ':'ʧ',
                            'dʒ':'ʤ',
                            'tɕ':'ʨ',
                            'dʑ':'ʥ'}
    for aff in affricate_conversion:
        tr = re.sub(aff, affricate_conversion[aff], tr)
    
    #not really sure what '⁻' indicates within tones, perhaps alternative realizations?
    #segmented IPA version seems to only include the tone symbols up until this character
    #so also that here
    new_parts = []
    for part in tr.split():
        part = part.split('⁻')
        new_parts.append(part[0])
    tr = ' '.join(new_parts)
    
    return tr


for i in forms_data:
    entry = forms_data[i]
    new_entry = sinitic_data[i]
    word_id = entry['Parameter_ID']
    lang = entry['Language_ID']
    new_name, glottocode, iso_code = lang_data[lang]
    gloss = concept_dict[entry['Parameter_ID']]
    cognate_id = '_'.join([gloss, str(cognate_id_lookup[i])])
    #cognate_id = entry['Parameter_ID'].split('_')[0]
    new_entry['ID'] = '_'.join([lang, str(cognate_id)])
    new_entry['Language_ID'] = new_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code
    new_entry['Parameter_ID'] = gloss
    orth = ''.join(liu_sinitic[i]['CHARACTERS'].split())
    new_entry['Value'] = orth
    #new_entry['Form'] = fix_tr(entry['Form'])
    #new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
    
    #the form and segments fields sometimes have differing transcriptions, 
    #but segments seems to be the better of the two 
    #(doesn't exhibit some of the issues to be fixed with the fix_tr function)
    segments = ' '.join([fix_tr(seg) for seg in entry['Segments'].split()])
    tr = ''.join(segments.split())
    new_entry['Form'] = tr
    new_entry['Segments'] = segments
    new_entry['Source_Form'] = entry['Form']
    new_entry['Cognate_ID'] = cognate_id
    new_entry['Loan'] = entry['Loan']
    new_entry['Comment'] = entry['Comment']
    new_entry['Source'] = entry['Source']
    
#%%
#ISOLATE UNKNOWN CHARACTERS IN TRANSCRIPTIONS

all_new_chs = [ch for i in sinitic_data
               for field in ['Form', 'Segments']
               for ch in sinitic_data[i][field] 
               if ch not in all_sounds + diacritics + [' ', 'ˑ', '̠', '̆', '̈',
                                                       '²', '³', '¹', '⁵', '⁴', '⁰']]

new_chs = list(set(all_new_chs))
new_chs.sort(key= lambda x: all_new_chs.count(x), reverse=True)


def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(sinitic_data[i]['Language_ID'] for i in sinitic_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in sinitic_data:
        entry = sinitic_data[i]
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
#CREATE PROCESSED LANGUAGE DOCUMENTS
def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            values = sep.join([str(data_dict[i][feature]) for feature in features])
            f.write(f'{values}\n')
                    
write_data(sinitic_data, 'sinitic_data.csv')



    
    