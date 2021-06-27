from openpyxl import load_workbook
from collections import defaultdict
import os, glob
import pandas as pd
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
             if lang_data['Dataset'][i] == 'Hokan'}

#%%
#LOAD CONCEPTICON MAPPING
concepticon_swadesh = csv_to_dict('Source/Concepticon/Concept_list_Starostin_1991_110.csv', sep='\t')
concepticon_swadesh = {concepticon_swadesh[i]['Name'].split(' [')[0]:concepticon_swadesh[i]['Parameter']
                       for i in concepticon_swadesh}

for key, value in [('I1', 'I'), #subjective form 
                ('I2', 'I'), #objective form 
                ('claw(nail)', 'CLAW OR NAIL'), 
                ('round (2D)2', 'CIRCULAR (ROUND IN TWO DIMENSIONS)'), 
                ('round (3D)1', 'SPHERICAL (ROUND IN THREE DIMENSIONS)'), 
                ('thin (1D)2', 'THIN (OF LEAF AND CLOTH)'), 
                ('thin (2D)1', 'THIN (OF HAIR AND THREAD)'), 
                ('walk (go)', 'WALK'), 
                ('warm (hot)', 'WARM')]:
    concepticon_swadesh[key] = value


#%%
#LOAD HOKAN DATASETS BY SUBGROUP

hokan_datasource = 'Source/'
os.chdir(hokan_datasource)
datasets = glob.glob('*.xlsx')

new_hokan_ch = defaultdict(lambda:[])


hokan_subfamilies = {}

for dataset in datasets:
    sh = load_workbook(dataset)['Sheet1']
    subfamily = dataset.split('.')[0]
    
    columns = [i[0].column_letter for i in list(sh.columns)]
    rows = list(range(1,len(list(sh.rows))+1))
    
    end_column_i = 0
    while ' notes' not in sh[f'{columns[end_column_i]}{1}'].value:
        end_column_i += 1
    
    data_columns = columns[2:end_column_i]
    notes_columns = columns[end_column_i:]
    
    lang_labels = [(sh[f'{c}1'].value, c) for c in data_columns]
    lang_labels = [label for label in lang_labels if '#' not in label[0]]
    lang_labels = [(lang_labels[i][0], lang_labels[i][1], notes_columns[i]) 
                   for i in range(len(lang_labels))]
    
    conversion_dict = {'â':'â', #falling tone [Yavapai, Karuk]
                       'á':'á', #high tone [Yavapai, Karuk, Shasta]
                       'g':'ɡ',
                       'c':'ʦ', #all?
                       'č':'ʧ',
                       'é':'é', #high tone [Yavapai, Karuk, Shasta]
                       'ê':'ê', #falling tone [Yavapai, Karuk]
                       'î':'î', #falling tone [Yavapai, Karuk]
                       'í':'í', #high tone [Yavapai, Karuk, Shasta, Kashaya]
                       'ƛ':'t͡ɬ',
                       'ó':'ó', #high tone [Yavapai]
                       'š':'ʃ',
                       'û':'û', #falling tone [Yavapai, Karuk]
                       'ú':'ú', #high tone [Yavapai, Karuk, Shasta]
                       'y':'j',
                       'ʸ':'ʲ',
                       ':':'ː',
                       '-':'', #morphological boundary
                       '=':'', #word boundary
                       '#':'', #boundary?
                       '"':'',
                       ' ':'',
                       '(':'', #should parentheses be removed?
                       ')':'',
                       '.':'',
                       '\ue26c':'t͡ɬ',
                       '\ue81d':'t̪', #
                       '\ue817':'n̪',
                       '\uee47':'n̥',
                       '\uee37':'l̥',
                       '\uf2af':'χ',
                       '\uede5':'̥' #voiceless diacritic
                       } 
    
    problems = []
    family_vocab = defaultdict(lambda:{})
    index = 0
    for lang, c, notes_c in lang_labels:
        cognate_c = columns[columns.index(c)+1]
        new_name, glottocode, iso_code = lang_data[lang]
        for r in range(3, rows[-1]+1):
            gloss = sh[f'B{r}'].value.strip()
            concepticon_gloss = concepticon_swadesh[gloss]
            cell = sh[f'{c}{r}']
            cell_value = cell.value
            if cell_value != None:
                variants = cell_value.split('~')
                variants = [variant.strip() for variant in variants]
                for tr in variants:
                    orth = tr[:]
                    original_tr = tr[:]
                    tr = ''.join([conversion_dict.get(ch, ch) for ch in tr])
                    cognate_index = sh[f'{cognate_c}{r}'].value
                    cognate_id = '_'.join([concepticon_gloss, subfamily, str(cognate_index)])
                    
                    index += 1
                    new_entry = family_vocab[index]
                    new_entry['ID'] = '_'.join([strip_ch(lang, ' '), concepticon_gloss, str(cognate_id)])
                    new_entry['Language_ID'] = new_name
                    new_entry['Glottocode'] = glottocode
                    new_entry['ISO 639-3'] = iso_code
                    new_entry['Parameter_ID'] = concepticon_gloss
                    new_entry['Value'] = orth
                    new_entry['Form'] = tr
                    new_entry['Segments'] = ' '.join(segment_word(tr))
                    new_entry['Source_Form'] = original_tr
                    new_entry['Cognate_ID'] = cognate_id
                    if int(cognate_index) < 1:
                        new_entry['Loan'] = 'TRUE'
                    else:
                        new_entry['Loan'] = 'FALSE'
                    
                    sources_notes = sh[f'{notes_c}{r}'].value
                    if sources_notes == None:
                        sources_notes = '.'
                    if '\t' in sources_notes: #remove tabs from sources/notes
                        sources_notes = re.sub('\t', '', sources_notes)
                    sources_notes = re.split('\. *', sources_notes, maxsplit=1)
                    sources, notes = sources_notes
                    new_entry['Comment'] = notes
                    new_entry['Source'] = sources
    
                        
    hokan_subfamilies[subfamily] = family_vocab

#%%
#COMBINE DATA FROM EACH SUBGROUP INTO A SINGLE DICTIONARY
combined_hokan_data = {}
index = 1
for subgroup in hokan_subfamilies:
    for i in hokan_subfamilies[subgroup]:
        entry = hokan_subfamilies[subgroup][i]
        index +=1
        combined_hokan_data[index] = entry
    

#%%
#ISOLATE UNKNOWN CHARACTERS IN TRANSCRIPTIONS
print('')
all_new_chs = [ch for i in combined_hokan_data  
               for ch in combined_hokan_data[i]['Segments'] 
               if ch not in all_sounds + diacritics + [' ', 'ˑ', '̠', '̆']]

new_chs = list(set(all_new_chs))
new_chs.sort(key= lambda x: all_new_chs.count(x), reverse=True)


def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(combined_hokan_data[i]['Language_ID'] for i in combined_hokan_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in combined_hokan_data:
        entry = combined_hokan_data[i]
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


#CREATE PROCESSED DATA FILE
def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[1]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            values = sep.join([str(data_dict[i][feature]) for feature in features])
            f.write(f'{values}\n')

os.chdir(local_dir)
write_data(combined_hokan_data, 'hokan_data.csv')    