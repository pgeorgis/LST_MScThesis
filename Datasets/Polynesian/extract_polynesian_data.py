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
             if lang_data['Dataset'][i] == 'Polynesian'}


#%%
#LOAD DATASET
polynesian_data = csv_to_dict('Source/raw/polynesian-aligned_22112018_corrected.tsv', sep='\t')
poly_forms = csv_to_dict('Source/cldf/forms.csv')

poly_langs = csv_to_dict('Source/cldf/languages.csv')
poly_lang_dict = {poly_langs[i]['Name']:poly_langs[i]['ID'] for i in poly_langs}

poly_cognates = csv_to_dict('Source/cldf/cognates.csv')
cognate_dict = {poly_cognates[i]['Form_ID']:poly_cognates[i]['Cognateset_ID'] 
                for i in poly_cognates}

poly_concepts = csv_to_dict('Source/cldf/parameters.csv')
concept_dict = {poly_concepts[i]['Concepticon_ID']:poly_concepts[i]['Concepticon_Gloss'] 
                for i in poly_concepts}

#concepts missing from Polynesian concept data
for key, value in [('1094', 'FASTEN'), #'to tie up, fasten'
                   ('1156', 'OPEN'), #'to open, uncover'
                   ('1292', 'BAD OR EVIL'), #'bad, evil'
                   ('1410', 'KNOW (SOMETHING)'), #'to know, be knowledgeable'
                   ('1422', 'BE ALIVE'), #'to live, be alive'
                   ('1432', 'CUT OR HACK'), #'to cut, hack'
                   ('1434', 'STAB'), #'to stab, pierce'
                   ('1460', 'IN'), #'in, inside'
                   ('1586', 'SMELL (PERCEIVE)'), #'to sniff, smell'
                   ('1725', 'CORRECT (RIGHT)'), #'correct, true'
                   ('2101', 'BE DEAD OR DIE'), #'to die, be dead'
                   ('2103', 'PAINFUL OR SICK'), #'painful, sick'
                   ('2279', 'NO OR NOT'), #'no, not'
                   ('354', 'POUND'), #'to pound, beat'
                   ('379', 'BLUNT'), #'dull, blunt'
                   ('487', 'SHY OR ASHAMED'), #'shy, ashamed'
                   ('602', 'HIDE'), #'to hide'
        ]:
    concept_dict[key] = value
missing_glosses = []
 
#Generate cognate set indices
cognate_sets = defaultdict(lambda:defaultdict(lambda:[]))
cognate_id_lookup = {}
for i in polynesian_data:
    entry = polynesian_data[i]
    concepticon_id = entry['CONCEPTICON_ID']
    if concepticon_id != '':
        gloss = concept_dict[concepticon_id]
        cognacy = entry['COG']
        cognate_sets[gloss][cognacy].append(i)
for gloss in cognate_sets:
    sets = sorted(list(cognate_sets[gloss].keys()))
    for i in range(len(sets)):
        cognate_set = cognate_sets[gloss][sets[i]]
        set_i = i+1
        for j in cognate_set:
            cognate_id_lookup[j] = set_i


#%%
conversion_dict = {'g':'ɡ',
                   '_':'', #unknown purpose, segmentation?
                   '+':''} #morphemic segmentation?
                   
old_conversion_dict = {'g':'ɡ',
                   "'":'ʔ',
                   'ʻ':'ʔ',
                   
                   #Long vowels with macrons
                   'ā':'aː',
                   'ē':'eː',
                   'ī':'iː',
                   'ō':'oː',
                   'ū':'uː',
                   
                   #Glottal stop + vowel, marked with grave accent
                   'à':'ʔa',
                   #'ì':'ʔi', #East Futuna, Luangiua, North Marquesan, Rapanui, Rarotongan, RennellBellona, Wallisian
                   
                   #Language-specific characters
                   ('ì', 'Futuna-Aniwa'):'i', #not the glottal stop sequence as in other languages
                   
                   #Rapanui, according to IPA field in polynesian-aligned_22112018_corrected.tsv file
                   'â':'aː',
                   'î':'iː',
                   'ô':'o',
                   'û':'uː',
                   
                   #Austral A
                   'G':'ɡ',
                   
                   #Mele-Fila
                   'č':'ʨ',
                   
                   #Punctuation, segmentation, mistakes
                   '0':'o', #most likely a typo
                   '|':'', #unknown purpose, just remove it
                   '_':'', #unknown purpose, only appears in one word, just remove it
                   '.':'', #probably mistake or for word segmentation
                   '-':'', #probably segmentation of compound words and/or affixes/roots
                   '+':'', #seems to represent segmentation of words composed of >1 word
                   '·':'', #some form of segmentation
                   #' ':'', #get rid of spaces
                   
                   #Reconstructed forms
                   '*':'', #* represents reconstructed word in Proto-Polynesian
                   '?':'' #? probably represents uncertain form in Proto-Polynesian
                   } 


def fix_tr(word, lang, conversion):
    word = ''.join([conversion.get((ch, lang), ch) for ch in word])
    word = ''.join([conversion.get(ch, ch) for ch in word])
    
    #convert 'ts' to 'ʦ'
    word = re.sub('ts', 'ʦ', word)
    
    #convert long vowels to VV sequences
    chs = list(word)
    word = [chs[0]]
    j = 1
    for i in range(1, len(chs)):
        ch = chs[i]
        while chs[i-j] in diacritics:
            j += 1
        prev_ch = chs[i-j]
        prev_seg = ''.join(chs[i-j:i])
        if ch == 'ː':
            if prev_ch in vowels:
                word.append(prev_seg)
            else:
                word.append(ch)
        else:
            word.append(ch)
    word = ''.join(word)
    
    #remove annotation contained between "‘’"
    word = re.sub('‘\w*’', '', word)

    return word

poly_data = defaultdict(lambda:{})
for i in polynesian_data:
    entry = polynesian_data[i]
    lang_id = entry['DOCULECT']
    if lang_id != '':
        new_entry = poly_data[i]
        lang = poly_lang_dict[lang_id]
        new_name, glottocode, iso_code = lang_data[lang]
        concepticon_id = entry['CONCEPTICON_ID']
        concept = entry['CONCEPT']
        try:
            gloss = concept_dict[concepticon_id]
        except KeyError:
            missing_glosses.append((concepticon_id, concept))
            gloss = concept 
        cognate_id = '_'.join([gloss, str(cognate_id_lookup[i])])
        new_entry['ID'] = '_'.join([lang, str(cognate_id)])
        new_entry['Language_ID'] = new_name
        new_entry['Glottocode'] = glottocode
        new_entry['ISO 639-3'] = iso_code
        new_entry['Parameter_ID'] = gloss
        new_entry['Value'] = entry['VALUE']
        new_entry['Form'] = fix_tr(entry['IPA'], lang, conversion_dict)
        new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
        new_entry['Source_Form'] = entry['IPA']
        new_entry['Cognate_ID'] = cognate_id
        new_entry['Loan'] = entry['LOAN'].upper()
        new_entry['Comment'] = entry['COMMENT']
        new_entry['Source'] = entry['SOURCE']

if len(missing_glosses) > 0:
    print(f'Number of missing glosses: {len(set(missing_glosses))}')

#%%
#CHECKING PHONETIC CHARACTERS
poly_phones = set([ch for i in poly_data
                   for ch in poly_data[i]['Form']])

new_poly_phones = [phone for phone in poly_phones 
                  if phone not in all_sounds
                  if phone not in diacritics]

poly_phones_langs = defaultdict(lambda:[])
for phone in poly_phones:
    for i in poly_data:
        entry = poly_data[i]
        if phone in entry['Form']:
            poly_phones_langs[phone].append((entry['Language_ID'],
                                                entry['Parameter_ID'],
                                                entry['Form']))

                    
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

write_data(poly_data, 'polynesian_data.csv')
        