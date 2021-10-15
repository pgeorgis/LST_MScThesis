import os, re
from collections import defaultdict
from pathlib import Path
import pandas as pd
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent
source_data_dir = 'Source/grollemundbantu/'

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
             if lang_data['Dataset'][i] == 'Bantu'}


#%%
#LOAD BANTU DATASET
forms_data = pd.read_csv(source_data_dir + 'cldf/forms.csv')
bantu_langs_data = csv_to_dict(source_data_dir + 'cldf/languages.csv')
bantu_langs_data = {bantu_langs_data[i]['ID']:(bantu_langs_data[i]['Name'], 
                                          bantu_langs_data[i]['Glottocode'], 
                                          bantu_langs_data[i]['ISO639P3code'])
                   for i in bantu_langs_data}
  
#%%
#LOAD CONCEPTICON MAPPING
concept_data = pd.read_csv(source_data_dir + 'cldf/parameters.csv')
concepticon_dict = {concept_data['ID'][i]:concept_data['Concepticon_Gloss'][i] 
                    for i in range(len(concept_data))}

#%%
conversion_dict = {#Consonants
                   'g':'ɡ', #replace with proper IPA character
                   
                   #Implosives: transcribed inconsistently, so turn all implosives into egressive stops
                   'ɓ':'b',
                   'ɗ':'d',
                   
                   #Vowels: tones and nasalized vowels
                   'à':'à', 
                   'á':'á',
                     'â':'â',
                     'ã':'ã',
                     'è':'è',
                     'é':'é',
                     'ê':'ê',
                     'ì':'ì',
                     'í':'í',
                     'î':'î',
                     'ò':'ò',
                     'ó':'ó',
                     'ô':'ô',
                     'õ':'õ',
                     'ù':'ù',
                     'ú':'ú',
                     'û':'û',
                     'ě':'ě',
                     'ń':'ń',
                     'ō':'ō',
                     'ǎ':'ǎ',
                     'ǒ':'ǒ',
                     'ǔ':'ǔ',
                     'ǹ':'ǹ',
                     'ȁ':'ȁ',
                     'ȉ':'ȉ',
                     'ȍ':'ȍ',
                     'ȕ':'ȕ',
                     'ḿ':'ḿ',
                     'ẅ':'ẅ',
                     'ɩ':'ɪ', #uncertain
                   
                   #Affricates
                   'ts':'ʦ',
                   'dz':'ʣ',
                   'tʃ':'ʧ',
                   'dʒ':'ʤ',
                   'tɬ':'t͡ɬ',     
                   
                   #Other
                   '\+':'', 
                   ':':'ː',
                   '´':'́' #high tone
                   
                   }

digraphs = []
slashes = []
def fix_tr(tr, lang, orth, gloss):
    segments = tr.split()
    fixed = []
    for seg in segments:
        if '/' in seg:
            slashes.append(seg)
            seg = seg.split('/')[0] #some segments transcribed as, e.g. <ú/u> to denote tone --> simply take the first part
        
        for seq in conversion_dict:
            seg = re.sub(seq, conversion_dict[seq], seg)
        if len(seg) > 1: 
            digraphs.append(seg)
        
        fixed.append(seg)
    
    fixed = ''.join(fixed)
    
    if lang == 'Swahili':
        #Swahili <j> mistranscribed as /j/ --> /ʄ/
        if 'j' in orth:
            fixed = re.sub('j', 'ʄ', fixed)
        
        #Certain Swahili words transcribed wrong (e.g. without prefix although it is transcribed in other Bantu languages)
        tr_fixed = {'yumba':('ɲumba', 'nyumba'),  #<nyumba> 'HOUSE' 
                    'ywele':('ɲwele', 'nywele'), #<nywele> 'HAIR' 
                    'yoka':('ɲoka', 'nyoka'), #<nyoka> 'SNAKE'
                    'kono':('mkono', 'mkono'), #<mkono> 'ARM'
                    'dege':('ndeɡe', 'ndege'), #<ndege> 'BIRD'
                    'fupa':('mfupa', 'mfupa'), #<mfupa> 'BONE'
                    'mande':('umande', 'umande'), #<umande> 'DEW'
                    'bwa':('mbwa', 'mbwa'), #<mbwa> 'DOG'
                    'dovu':('ndovu', 'ndovu'), #<ndovu> 'ELEPHANT'
                    'so':('uso', 'uso'), #<uso> 'FACE',
                    'futa':('mafuta', 'mafuta'), #<mafuta> 'ORGANIC FAT OR OIL'
                    'ɲoya':('uɲoja', 'unyoya'), #<unyoya> 'FEATHER'
                    'kucha':('ukuʧa', 'ukucha'), #<ukucha> 'FINGERNAIL'
                    'oto':('moto', 'moto'), #<moto> 'FIRE'
                    'buzi':('mbuzi', 'mbuzi'), #<mbuzi> 'GOAT'
                    'dongo':('udonɡo', 'udongo'), #<udongo> 'EARTH (SOIL)'
                    'chwa':('kiʧwa', 'kichwa'), #<kichwa> 'HEAD'
                    'oyo':('mojo', 'moyo'), #<moyo> 'HEART'
                    'su':('kisu', 'kisu'), #<kisu> 'KNIFE'
                    'guu':('mɡuu', 'mguu'), #<mguu> 'LEG'
                    'wanamume':('mwanamume', 'mwanamume'), #<mwanamume> 'MAN'
                    'wezi':('mwezi', 'mwezi'), #<mwezi> 'MOON'
                    'tovu':('kitovu', 'kitovu'), #<kitovu> 'NAVEL'
                    'siku':('usiku', 'usiku'), #<usiku> 'NIGHT'
                    'tu':('mtu', 'mtu'), #<mtu> 'PERSON'
                    'vua':('mvua', 'mvua'), #<mvua> 'RAIN (PRECIPITATION)'
                    'jia':('nʄia', 'njia'), #<njia> 'ROAD'
                    'zizi':('mzizi', 'mzizi'), #<mzizi> 'ROOT'
                    'changa':('mʧanɡa', 'mchanga'), #<mchanga> 'SAND'
                    'gozi':('nɡozi', 'ngozi'), #<ngozi> 'SKIN'
                    'bingu':('uwinɡu', 'uwingu'), #<uwingu> 'SKY' (<mbingu> is plural)
                    'oʃi':('moʃi', 'moshi'), #<moshi> 'SMOKE'
                    'kuki':('mkuki', 'mkuki'), #<mkuki> 'SPEAR'
                    'kia':('mkia', 'mkia'), #<mkia> 'TAIL'
                    'limi':('ulimi', 'ulimi'), #<ulimi> 'TONGUE'
                    'ti':('mti', 'mti'), #<mti> 'TREE'
                    'bili':('wili', '-wili'), #<-wili> 'TWO' (<mbili> is form in N-class)
                    'jiji':('kiʄiʄi', 'kijiji'), #<kijiji> 'VILLAGE'
                    'ta':('kita', 'kita'), #<kita> 'WAR'
                    'ji':('maʄi', 'maji'), #<maji> 'WATER'
                    'pepo':('upepo', 'upepo'), #<upepo> 'WIND'
                    'wanamke':('mwanamke', 'mwanamke'), #<mwanamke> 'WOMAN'
                    }
        
        fixed, orth = tr_fixed.get(orth, (fixed, orth))
        if gloss == 'MOUTH':
            fixed, orth = 'kiɲwa', 'kinywa'
    
    
    return fixed, orth

skipped = []
skipped_cognates = []
bantu_data = defaultdict(lambda:{})
index = 0
for index, entry in forms_data.iterrows():
    word_id = ''.join(entry['ID'].split('-')[:-1]) + '-1-1'
    lang_id = entry['Language_ID']

    #Filter only languages in languages.csv
    try:
        new_name, glottocode, iso_code = lang_data[lang_id]
    except KeyError:
        skipped.append(lang_id)
        continue 
    
    concept = entry['Parameter_ID']
    concepticon_gloss = concepticon_dict[concept]
    
    cognate_id = concepticon_gloss + '_' + entry['Cognacy'].split('-')[-1]
    
    tr = entry['Segments']
    
    #skip nan entries
    if type(entry['Value']) == float:
        continue
    if type(entry['Segments']) == float:
        continue
    
    index += 1
    
    new_entry = bantu_data[index]
    new_entry['ID'] = '_'.join([re.sub('-', '_', new_name), str(cognate_id)])
    new_entry['Language_ID'] = new_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code if type(iso_code) != float else ''
    new_entry['Parameter_ID'] = concepticon_gloss
    tr, orth = fix_tr(tr, new_name, entry['Value'], concepticon_gloss)
    new_entry['Value'] = orth
    new_entry['Form'] = tr
    new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
    new_entry['Source_Form'] = tr
    new_entry['Cognate_ID'] = cognate_id
    new_entry['Loan'] = entry['Comment'].upper() if type(entry['Comment']) != float else ''
    new_entry['Comment'] = entry['Comment'] if type(entry['Comment']) != float else ''
    new_entry['Source'] = entry['Source'] if type(entry['Source']) != float else ''

#%%
#CHECKING PHONETIC CHARACTERS
bantu_phones = set([ch for i in bantu_data
                   for ch in bantu_data[i]['Form']])

new_chs = set(phone for phone in bantu_phones 
              if phone not in all_sounds+diacritics+[' '])

def lookup_segment(segment, data=bantu_data, langs=None):
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
output_file = 'bantu_data.csv'
print(f'Writing preprocessed Bantu data to "{output_file}"...')

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
            
write_data(bantu_data, output_file=output_file)
