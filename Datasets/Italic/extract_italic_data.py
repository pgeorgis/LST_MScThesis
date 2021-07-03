from openpyxl import load_workbook
import os, re
from collections import defaultdict
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from phonetic_distance import *
from auxiliary_functions import csv_to_dict, strip_ch
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
                   ('walk (go)', 'WALK'),
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
            i += 1
            orth, tr, original_tr, cognate_id, sources, notes = item
            entry = family_data[i]
            new_name, glottocode, iso_code = lang_data[lang]
            try: 
                concepticon_gloss = concepticon_swadesh[gloss]
            except KeyError:
                if gloss not in missing_glosses:
                    missing_glosses.append(gloss)
                concepticon_gloss = gloss
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

write_data(family_data, 'italic_data.csv')

