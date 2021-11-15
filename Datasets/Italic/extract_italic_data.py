from openpyxl import load_workbook
import os, re
from collections import defaultdict
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict, strip_ch
from phonetic_distance import *
os.chdir(local_dir)


#%%
#LOAD LANGUAGE CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Italic'}


#%%
#LOAD ROMANCE/ITALIC DATA
romance_file = 'Source/rom_modified.xlsx'
romance_data = load_workbook(romance_file)
sh = romance_data['Sheet1']
columns = [i[0].column_letter for i in list(sh.columns)]
rows = list(range(1,len(list(sh.rows))+1))
data_columns = columns[2:columns.index('DN')+1]
note_columns = columns[columns.index('DO'):]
lang_labels = [(sh[f'{c}1'].value, c) for c in data_columns]
lang_labels = [label for label in lang_labels if '#' not in label[0]]
lang_labels = list(zip(lang_labels, note_columns))
lang_labels = [(item[0][0], item[0][1], item[1]) for item in lang_labels]

#%%
#LOAD LOANWORD ANNOTATIONS
loanword_data = csv_to_dict('Source/loanwords.csv', sep='\t')
loanword_dict = {loanword_data[i]['Word_ID']:int(float(loanword_data[i]['New CognateID']))
                 for i in loanword_data}

#%%
#LOAD CONCEPTICON MAPPING
concepticon_swadesh = csv_to_dict('Source/Swadesh200_Concepticon.csv')
concepticon_swadesh = {concepticon_swadesh[i]['Name'].split(' [')[0]:concepticon_swadesh[i]['Parameter']
                       for i in concepticon_swadesh}
for key in list(concepticon_swadesh.keys()):
    if 'to ' in key:
        concepticon_swadesh[key.split('to ')[1]] = concepticon_swadesh[key]

for key, value in [('all', 'ALL'),
                   ('belly ', 'BELLY'),
                   ('breast', 'BREAST'),
                   ('burn tr.', 'BURN (SOMETHING)'),
                   ('claw(nail)', 'FINGERNAIL'),
                   ('cold', 'COLD (OF WEATHER)'),
                   ('dry', 'DRY'),
                   ('earth', 'EARTH (SOIL)'),
                   ('fat n.', 'FAT (ORGANIC SUBSTANCE)'),
                   ('feather', 'FEATHER'),
                   ('fly v.', 'FLY (MOVE THROUGH AIR)'),
                   ('full', 'FULL'),
                   ('horn', 'HORN (ANATOMY)'),
                   ('knee', 'KNEE'),
                   ('know', 'KNOW (SOMETHING)'),
                   ('man', 'MALE PERSON'),
                   ('meat', 'FLESH OR MEAT'),
                   ('moon', 'MOON'),
                   ('rain', 'RAIN (PRECIPITATION)'), #noun form
                   ('road', 'ROAD'),
                   ('round', 'ROUND'),
                   ('skin', 'SKIN (HUMAN)'),
                   ('smoke', 'SMOKE (EXHAUST)'),
                   ('tooth', 'TOOTH'),
                   ('walk (go)', 'WALK'), #this concept will be removed, see note below
                   ('warm (hot)', 'WARM (OF WEATHER)'),
                   ('what', 'WHAT'),
                   ('who', 'WHO')]:
    concepticon_swadesh[key] = value

missing_glosses = []
    

#%%
conversion_dict = {#Nasal segments
                   'ã':'ã',
                   'ẽ':'ẽ',
                   '\ue96b':'ɛ̃',
                   'ĩ':'ĩ',
                   'õ':'õ',
                   '\ue975':'ɔ̃',
                   'ũ':'ũ',
                   '\ue077':'w̃',
                   '\uedc3':'̃', #nasal diacritic
                   
                   #Segmentation
                   '-':'', #morphological boundary
                   '=':'', #word boundary
                   #' ':'', #space

                   
                   #LANGUAGE-SPECIFIC CHARACTERS
                   
                   ('ĭ', 'Aromanian'):'ĭ', #extra short
                   ('ŭ', 'Aromanian'):'ŭ', #extra short
                   
                   #According to transcription notes on Starling Romance dataset description page
                   #Combined with Omniglot: https://www.omniglot.com/writing/ligurian.htm
                   #Corresponds to orthographic <æ>
                   ('ä', 'Stella Ligurian'):'ɛː', 
                   ('ä', 'Genoese Ligurian'):'ɛː', 
                   ('ä', 'Rapallo Ligurian'):'ɛː', 
                   
                   #According to transcription notes on Starling Romance dataset description page
                   #Combined with Omniglot: https://www.omniglot.com/writing/istro-romanian.htm
                   #Corresponds to orthographic <ę>
                   ('ä', 'Istro Romanian'):'æ',
                   
                   #SPANISH
                   #e.g. <y> in Spanish, /ɟ͡ʝ/~/ʝ/ is the typical transcription
                   #Here it only appears in <yo>, so we assign the relevant allophone /ɟ͡ʝ/
                   ('ʑ', 'Castilian Spanish'):'ɟ͡ʝ',
                   
                   #Spanish has no vowel /ɑ/, likely a typo
                   ('ɑ', 'Castilian Spanish'):'a', 
                   
                   #PORTUGUESE
                   #Portuguese /ə/ --> /ɨ/ (more typical and phonetically accurate transcription)
                   ('ə', 'Standard Portuguese'):'ɨ',
                   
                   #Typo: no trill /r/ in Portuguese (likely typo as it appears only once)
                   ('r', 'Standard Portuguese'):'ɾ',
                   
                   #OCCITAN
                   #Occitan has 1-2 rhotic sounds, either all tap /ɾ/ or /ɾ/ and /r/~/ʀ/ (but not all 3)
                   #Here: convert /ʁ/ to /ʀ/; 
                   #All instances of /r/ in transcription should actually be /ɾ/
                   #Except for in the word <rusco> /rˈysko/ 'BARK' --> /ʀˈysko/, so target it individually in fix_tr function below using regexp
                   ('ʁ', 'Provençal Occitan'):'ʀ',
                   ('r', 'Provençal Occitan'):'ɾ',
                   
                   #SICILIAN (PALERMITAN & SOUTHEASTERN)
                   #Palermitan: seems to be a typo as trill /r/ only appears in <abbruciari> /abːruʧˈaɾi/ 'BURN (SOMETHING)'
                   #Southeastern: similar; appears in <abbrusciari>, <stinnirisi>, <brancu>, but we would expect taps in all these positions
                   #otherwise Palermitan/Southeastern Sicilian has tap /ɾ/ everywhere
                   ('r', 'Palermitan Sicilian'):'ɾ',
                   ('r', 'South-Eastern Sicilian'):'ɾ',
                   
                   
                   #GENERAL REPLACEMENTS
                   'c':'ʦ',
                   'č':'ʧ',
                   'ȡ':'ɟ', #technically [ɟ̟]
                   'ε':'ɛ',
                   'g':'ɡ',
                   'ö':'ø',
                   'š':'ʃ',
                   'ʆ':'ɕ',
                   'ȶ':'c', #technically [c̟]
                   'ü':'y',
                   'y':'j',
                   'ʸ':'ʲ',
                   'ž':'ʒ',
                   'ǯ':'ʤ',
                   '͂':'̃',
                   ':':'ː', #colon --> long diacritic
                   '\ue099':'ə̯',
                   '\uedef':'̯', #non-syllabic diacritic
                   '\xa0':'' #extra space character
                   }

def fix_tr(tr, lang):
    tr = ''.join([conversion_dict.get(ch, ch) for ch in tr])
    tr = ''.join([conversion_dict.get((ch, lang), ch) for ch in tr])
    
    #Correct instances of double length/non-syllabic diacritics
    tr = re.sub('ːː', 'ː', tr)
    tr = re.sub('̯̯', '̯', tr)
    
    #Other reg exp modifications
    if lang == 'Provençal Occitan':
        #see Occitan section in conversion dict for explanation
        tr = re.sub('ɾˈy', 'ʀˈy', tr)
    
    elif lang in ['Central Catalan', 'North-Western Catalan']:
        #<rel> /ɾeɫ/ 'ROOT' --> /reɫ/ (should be trill /r/ as it is word-initial, cf. also <arrel> with same meaning)
        tr = re.sub('ɾeɫ', 'reɫ', tr)
        
    elif lang == 'Castelló de la Plana Catalan':
        #targeting <crosta> /krˈɔsta/ 'BARK', which should have tap /ɾ/ in this position
        tr = re.sub('kr', 'kɾ', tr)
    
    elif lang == 'Catanian Sicilian':
        #targeting <bruciari> /bruʧˈaɾi/ 'BURN (SOMETHING)', which should have tap /ɾ/ in this position
        tr = re.sub('br', 'bɾ', tr)
    
    elif lang == 'Neapolitan':
        #<r> between vowels in Neapolitan is a tap, not a trill (trilled word-initially and when preceded or followed by a consonant)
        for vowel1 in ['u', 'ə', 'ɛ', 'e', 'ɔ', 'a', 'o', 'i', 'ˈ']: #Neapolitan vowels plus stress marker
            for vowel2 in ['u', 'ə', 'ɛ', 'e', 'ɔ', 'a', 'o', 'i', 'ˈ']:
                tr = re.sub(f'{vowel1}r{vowel2}', f'{vowel1}ɾ{vowel2}', tr)
            
    
    #fix position of primary stress annotation (make it immediately precede the stress-bearing segment)
    stress_marked = 'ˈ' in tr
    if stress_marked == True:
        segments = segment_word(tr)
        stress_is = []
        for i in range(len(segments)):
            for stress_mark in ['ˈ', 'ˌ']:
                if stress_mark in segments[i]:
                    stress_is.append((i, stress_mark))
        offset = 0
        for entry in stress_is:
            i, stress_mark = entry
            new_i = i
            while strip_diacritics(segments[new_i])[0] not in vowels:
                if '̩' in segments[new_i]:
                    break
                elif '̍' in segments[new_i]:
                    break
                else:
                    new_i += 1
            if new_i != i:
                segments[i] = ''.join([ch for ch in segments[i] if ch != stress_mark])
                segments[new_i] = stress_mark + segments[new_i]
        tr = ''.join(segments)
    
    #Change geminate consonants into sequences of identical consonants
    tr = list(tr)
    for i in range(len(tr)):
        if tr[i] == 'ː':
            if tr[i-1] in consonants:
                tr[i] = tr[i-1]
    tr = ''.join(tr)
    
    
    return tr

problems = []
family_vocab = {}
for lang, c, notes_c in lang_labels:
    lang_dict = defaultdict(lambda:[])
    for r in range(3, rows[-1]+1):
        gloss = sh[f'B{r}'].value
        cell = sh[f'{c}{r}']
        cell_value = cell.value
        
        if cell_value != None:
            if len(cell_value.strip()) > 0:
                cognate_id_c = columns[columns.index(c)+1]
                cognate_id = sh[f'{cognate_id_c}{r}'].value
                
                sources_notes = sh[f'{notes_c}{r}'].value
                if sources_notes == None:
                    sources_notes = '.'
                if '\t' in sources_notes: #remove tabs from sources/notes
                    sources_notes = re.sub('\t', '', sources_notes)
                sources_notes = re.split('\. *', sources_notes, maxsplit=1)
                sources, notes = sources_notes
                
                variants = cell_value.split('~')
                variants = [variant.strip() for variant in variants]
                for variant in variants:
                    if variant.count('{') == 1:
                        variant = re.split(' *{', variant)
                        tr = variant[0]
                        original_tr, tr = tr, fix_tr(tr, lang)
                        orth = variant[1][:-1]
                        if tr == '': #skip if there is no transcription
                            problems.append((lang, c, r, ' {'.join(variant), cell_value, 'missing transcription'))
                            pass
                        else:
                            lang_dict[gloss].append((orth, tr, original_tr, cognate_id, sources, notes))
                            
                        
                    elif variant.count('{') == 0: #these ones only have transcriptions, no orthographic form
                        tr = variant
                        original_tr, tr = tr, fix_tr(tr, lang)
                        orth = ''
                        lang_dict[gloss].append((orth, tr, original_tr, cognate_id, sources, notes))
                        
                    
                    else:
                        problems.append((lang, c, r, variant, cell_value, variant.count('{'), 'too many { brackets in variant'))
    family_vocab[lang] = lang_dict

transcription_ch = set([ch for lang in family_vocab 
                    for gloss in family_vocab[lang]
                    for entry in family_vocab[lang][gloss]
                    for ch in entry[1]])

new_ch = [ch for ch in transcription_ch 
          if ch not in all_sounds
          if ch not in diacritics]

def show_examples(ch, langs=None):
    if langs == None:
        langs = list(family_vocab.keys())
    for lang in langs:
        for gloss in family_vocab[lang]:
            for entry in family_vocab[lang][gloss]:
                orth, tr, original_tr, cognate_id = entry
                if ch in tr:
                    print(f'{lang}: {orth} /{tr}/ ({gloss})')
     
#%%
family_data = defaultdict(lambda:{})
family_langs = list(family_vocab.keys())
loanwords = defaultdict(lambda:[])
i = 0
for lang in family_langs:
    for gloss in family_vocab[lang]:
        for item in family_vocab[lang][gloss]:
            orth, tr, original_tr, cognate_id, sources, notes = item
            new_name, glottocode, iso_code = lang_data[lang]
            try: 
                concepticon_gloss = concepticon_swadesh[gloss]
            except KeyError:
                if gloss not in missing_glosses:
                    missing_glosses.append(gloss)
                concepticon_gloss = gloss
            
            if concepticon_gloss != 'WALK': #excluded due to forms given in different tenses (e.g. some in imperfect, some in future, etc.)
                i += 1
                entry = family_data[i]
                entry['ID'] = '_'.join([strip_ch(lang, ' '), concepticon_gloss, str(cognate_id)])
                entry['Language_ID'] = new_name
                entry['Glottocode'] = glottocode
                entry['ISO 639-3'] = iso_code
                entry['Parameter_ID'] = concepticon_gloss
                entry['Value'] = orth
                entry['Form'] = tr
                entry['Segments'] = ' '.join(segment_word(tr))
                entry['Source_Form'] = original_tr
                if entry['ID'] in loanword_dict:
                    entry['Cognate_ID'] = '_'.join([concepticon_gloss, str(abs(loanword_dict[entry['ID']]))])
                else:
                    entry['Cognate_ID'] = '_'.join([concepticon_gloss, str(cognate_id)])
                if int(cognate_id) < 1:
                    entry['Loan'] = 'TRUE'
                    loanwords[entry['Cognate_ID']].append((new_name, entry['ID'], entry['Form'], notes))
                elif entry['Cognate_ID'] == 'SMALL_2': #words belonging to this class are borrowings from Greek <μικρός>, the same class as some others marked as loans. these were mistakenly not marked as loans
                    entry['Loan'] = 'TRUE'
                    loanwords[entry['Cognate_ID']].append((new_name, entry['ID'], entry['Form'], notes))
                else:
                    entry['Loan'] = 'FALSE'
                entry['Comment'] = notes
                entry['Source'] = sources

#CREATE PROCESSED DATA FILE
def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            values = sep.join([str(data_dict[i][feature]) for feature in features])
            f.write(f'{values}\n')

#%%
orth_correction = {'\ueff9':'', #unclear what character it's meant to be, only appears in Aromanian; just delete it
                   '\uedc7':'', #unclear what character it's meant to be, only appears one entry of Dalmatian; just delete it
                   '\uedef':'', #unclear what character it's meant to be, only appears one entry of Dalmatian; just delete it
                   '\uee2d':'i̯', #Dalmatian, Istro-Romanian, Megleno-Romanian
                   '\uee77':'u̯', #Dalmatian
                   }

def lookup_orth(ch):
    ch_instances = defaultdict(lambda:[])
    for i in family_data:
        if ch in family_data[i]['Value']:
            lang = family_data[i]['Language_ID']
            gloss = family_data[i]['Parameter_ID']
            orth = family_data[i]['Value']
            tr = family_data[i]['Form']
            ch_instances[lang].append(f'{gloss.upper()} <{orth}> /{tr}/')
    
    for lang in ch_instances:
        print(lang.upper())
        for entry in ch_instances[lang]:
            print('\t', entry)
        print('\n')
        
#Fix orthographic entries        
for i in family_data:
    for ch in orth_correction:
        family_data[i]['Value'] = re.sub(ch, orth_correction[ch], family_data[i]['Value'])

orth_ch = set(ch for i in family_data for ch in family_data[i]['Value'])

#%%
write_data(family_data, 'italic_data.csv')

