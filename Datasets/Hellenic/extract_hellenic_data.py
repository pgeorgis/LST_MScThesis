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
             if lang_data['Dataset'][i] == 'Hellenic'}

#%%
#LOAD HELLENIC DATA
hellenic_file = 'Source/grk.xlsx'
hellenic_data = load_workbook(hellenic_file)
sh = hellenic_data['Sheet1']
columns = [i[0].column_letter for i in list(sh.columns)]
rows = list(range(1,len(list(sh.rows))+1))
data_columns = columns[2:columns.index('N')+1]
note_columns = columns[columns.index('O'):]
lang_labels = [(sh[f'{c}1'].value, c) for c in data_columns]
lang_labels = [label for label in lang_labels if '#' not in label[0]]
lang_labels = list(zip(lang_labels, note_columns))
lang_labels = [(item[0][0], item[0][1], item[1]) for item in lang_labels]

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
                   ('claw (nail)', 'FINGERNAIL'),
                   ('cold', 'COLD (OF WEATHER)'),
                   ('dry', 'DRY'),
                   ('earth', 'EARTH (SOIL)'),
                   ('fat n.', 'FAT (ORGANIC SUBSTANCE)'),
                   ('feather', 'FEATHER'),
                   ('fly v.', 'FLY (MOVE THROUGH AIR)'),
                   ('full', 'FULL'),
                   ('horn', 'HORN (ANATOMY)'),
                   ('I1 ', 'I'), #subjective form
                   ('I2 ', 'I'), #objective form 
                   ('knee', 'KNEE'),
                   ('know', 'KNOW (SOMETHING)'),
                   ('man', 'MALE PERSON'),
                   ('meat', 'FLESH OR MEAT'),
                   ('moon', 'MOON'),
                   ('rain', 'RAIN (PRECIPITATION)'), #noun form
                   ('road', 'ROAD'),
                   ('round (2D)2', 'CIRCULAR (ROUND IN TWO DIMENSIONS)'),
                   ('round (3D)1', 'SPHERICAL (ROUND IN THREE DIMENSIONS)'),
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

conversion_dict = {#Consonants
                   'ȡ':'ɟ',
                   'ȶ':'c',
                   'g':'ɡ',
                   'c':'ʦ',
                   'č':'ʧ',
                   'ǯ':'ʤ',
                   '\uf2ae':'θ',
                   'š':'ʃ',
                   'y':'j',
                   
                   #Vowels
                   'ä':'æ',
                   'á':'á', #/a/ with high pitch accent
                   'â':'â', #/a/ with falling pitch accent
                   'é':'é', #/e/ with high pitch accent
                   'ê':'ê', #/e/ with falling pitch accent
                   'í':'í', #/i/ with high pitch accent
                   'ô':'ô', #/o/ with falling pitch accent
                   'ú':'ú', #/u/ with high pitch accent
                   'û':'û', #/u/ with falling pitch accent
                   'ü':'y',
                   'ǘ':'ý', #/y/ with high pitch accent
                   '\uf595':'ŷ', #/y/ with falling pitch accent
                   
                   #Diacritics
                   'ʸ':'ʲ',
                   
                   #Other
                   '-':'', #morphological boundary
                   '=':'', #word boundary
                   '"':'', #affix marker
                   
                   #Language-specific
                   ('ó', 'Ancient Attic Greek (Plato)'):'ó', #/o/ with high pitch accent
                   ('ó', 'Ancient Ionic Greek (Herodotus)'):'ó', #/o/ with high pitch accent
                   ('ó', 'Modern Demotic Greek'):'ˈo', #stressed /o/
                   
                   ('y', 'Modern Demotic Greek'):'ʝ',
                   ('y', 'Southern Tsakonian'):'ʝ',
                   
    }

def fix_tr(tr, lang):
    tr = ''.join([conversion_dict.get((ch, lang), ch) for ch in tr])
    tr = ''.join([conversion_dict.get(ch, ch) for ch in tr])
    
    tr = re.sub('j̊', 'ç', tr) #<ẙ> --> <j̊> --> <ç>
    
    if lang in ['Modern Demotic Greek', 'Southern Tsakonian']:
        #Modern Demotic Greek & Southern Tsakonian
        tr = re.sub('ʝ̊', 'ç', tr)
        
        #Modern Demotic Greek
        tr = re.sub('pʝ', 'pç', tr)
        tr = re.sub('tʝ', 'tç', tr)
        
        #Southern Tsakonian
        tr = re.sub('ʦʲ', 'ʨ', tr)
        
    
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
                
                if len(cell_value.split('{')) < 2: #these have only a transcription, no orthography
                    tr = [cell_value]
                    orth = ['']
                
                else:
                    tr, orth = cell_value.split('{')
                    tr = [item.strip() for item in re.split('[,|~]', tr)]
                    orth = [item.strip() for item in re.split('[,|~]', orth.strip()[:-1])]
                for tr, orth in zip(tr, orth):
                    original_tr, tr = tr, fix_tr(tr, lang)
                    
                    #Fix orthography
                    orth = re.sub('\uedc1', '', orth) #unknown character, doesn't seem to represent anything
                    orth = re.sub('\uedd1', '̂', orth) #circumflex accent in Tsakonian, Pharasa, and Cappadocian
                    
                    
                    lang_dict[gloss].append((orth, tr, original_tr, cognate_id, sources, notes))
                    
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
                orth, tr, original_tr, cognate_id, sources, notes = entry
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
            entry['Cognate_ID'] = '_'.join([concepticon_gloss, str(cognate_id)])
            if int(cognate_id) < 1:
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

write_data(family_data, 'hellenic_data.csv')
    