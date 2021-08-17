from openpyxl import load_workbook
from collections import defaultdict
import os, glob
import pandas as pd
from pathlib import Path
current_dir = Path(str(os.getcwd()))
parent_dir = current_dir.parent
grandparent_dir = parent_dir.parent

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict, strip_ch
os.chdir(str(grandparent_dir) + '/Code/Distance_Measures/')
from phonetic_distance import *
os.chdir(current_dir)

#%%
#LOAD LANGUAGE CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] in ['Slavic', 'Baltic']}

#%%
#LOAD CONCEPTICON MAPPING
concepticon_swadesh = csv_to_dict('Source/Concepticon/Concept_list_Starostin_1991_110.csv', sep='\t')
concepticon_swadesh = {concepticon_swadesh[i]['Name'].split(' [')[0]:concepticon_swadesh[i]['Parameter']
                       for i in concepticon_swadesh}
for key, value in [('claw(nail)', 'CLAW OR NAIL'),
                   ('nail', 'CLAW OR NAIL'),
                   ('walk (go)', 'WALK'),
                   ('go', 'WALK'),
                   ('warm (hot)', 'WARM')]:
    concepticon_swadesh[key] = value

#Load mappings of differing labels for the same concept group
all_concepts = pd.read_csv(str(parent_dir) + '/Concepts/concepts.csv', sep='\t')
base_concepts = {list(all_concepts.Concept)[i]:list(all_concepts.BaseConcept)[i] 
                 for i in range(len(all_concepts))}

for concept in concepticon_swadesh:
    concepticon_swadesh[concept] = base_concepts[concepticon_swadesh[concept]]

#%%
#LOAD BALTO-SLAVIC DATASETS BY SUBGROUP

datasets = ['Source/Baltic.xlsx', 'Source/Slavic.xlsx'] #glob.glob('Source/*.xlsx')

new_baltoslav_ch = defaultdict(lambda:[])


baltoslav_subfamilies = {}

for dataset in datasets:
    sh = load_workbook(dataset)['Sheet1']
    subfamily = dataset.split('.')[0].split('/')[1]
    
    columns = [i[0].column_letter for i in list(sh.columns)]
    rows = list(range(1,len(list(sh.rows))+1))
    
    end_column_i = 0
    while ' notes' not in sh[f'{columns[end_column_i]}{1}'].value.lower():
        end_column_i += 1
    
    data_columns = columns[2:end_column_i]
    notes_columns = columns[end_column_i:]
    
    lang_labels = [(sh[f'{c}1'].value, c) for c in data_columns]
    lang_labels = [label for label in lang_labels if '#' not in label[0]]
    if len(lang_labels) > 2: #Slavic
        lang_labels = [(lang_labels[i][0], lang_labels[i][1], notes_columns[int(i/2)]) 
                       for i in range(0,len(lang_labels),2)]
    else: #Baltic
        lang_labels = [(lang_labels[i][0], lang_labels[i][1], notes_columns[i]) 
                       for i in range(0,len(lang_labels))]
    
    conversion_dict = {#Consonants
                       'c':'ʦ',
                       'č':'ʧ',
                       'ȡ':'ɟ',
                       'g':'ɡ',
                       'š':'ʃ',
                       'ȶ':'c',
                       'y':'j',
                       'ž':'ʒ',
                       'ǯ':'ʤ',
                       
                       #Vowels
                       'ä':'æ',
                       '\ue25b':'ɛ', #Latvian
                       '\ue254':'ɔ', #Latvian
                       
                       
                       #Vowels with tones: convert from single character with accent
                       #to vowel with IPA tone diacritic
                       'ǎ':'ǎ',
                       'â':'â',
                       'ě':'ě',
                       'ê':'ê',
                       'î':'î',
                       'ǐ':'ǐ',
                       'ǒ':'ǒ',
                       'ô':'ô',
                       'û':'û',
                       'ǔ':'ǔ',
                       'ā':'ā', #mid level tone (Latvian)
                       'ǟ':'ǣ', #mid level tone (Latvian)
                       'ī':'ī', #mid level tone (Latvian)
                       'ū':'ū', #mid level tone (Latvian)
                       '\ue5e5':'ɔ̌', #open /ɔ/ with rising tone (Orlec Chakavian, Devinska Nova Ves Chakavian [only in diphthongs], Lithuanian, Latvian (krītošā intonācija))
                       '\ue585':'ě', #/e/ with rising tone
                       '\ue94b':'ê', #/e/ with falling tone
                       '\ue955':'ô', #/o/ with falling tone
                       
                       #Diacritics
                       'ʸ':'ʲ',
                       
                       #Language-specific fixes
                       ('ʒ', 'Standard Latvian'):'ʣ',
                       ('ʒ', 'Dihovo Macedonian'):'ʣ',
                       
                       #Other
                       '=':'', #morphemic segmentation, remove
                       '-':'', #morphemic segmentation, remove
                       '\xa0':'', #extra space character, remove
                       '\uede8':'', #seems to be an ogonek following an /l/ (Burgenland Kajkavian & Orlec Chakavian), not meant to be part of IPA transcription
                       } 
    
    def fix_tr(word, lang):

        word = ''.join([conversion_dict.get((ch, lang), ch) for ch in word])
        word = ''.join([conversion_dict.get(ch, ch) for ch in word])
        
        #Fix diphthong <o> in Latvian, /wo/ or /wɔ/ --> /uɔ̯/
        if lang == 'Standard Latvian':
            word = re.sub('w[o|ɔ]', 'uɔ̯', word)
        
        #Do a similar fix in Lithuanian
        elif lang == 'Standard Lithuanian':
            word = re.sub('w[o|ɔ]', 'uə', word)
        
        #Do a similar fix in Kajkavian and Chakavian
        else:
            word = re.sub('wɔ', 'u̯ɔ', word)
            word = re.sub('wo', 'u̯o', word)
            
        #fix position of primary stress annotation (make it immediately precede the stress-bearing segment)
        stress_marked = 'ˈ' in word
        if stress_marked == True:
            segments = segment_word(word)
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
            word = ''.join(segments)
        
        return word
    
    def fix_orth(word): #fix orthographic characters which don't show up properly
        orth_conversion = {'\uf80f':'l', #<l> in Latvian not showing up properly
                           '\ue016':'l', #<l> in Latvian/Lithuanian not showing up properly
                           '\ue00b':'ė',
                           '\ue009':'ė́',
                           '\ue022':'ū',
                           '\ue16b':'ū́',
                           '\ue201':'r', #syllabic <r> in Burgenland Chakavian
                           '\ue981':'ā',
                           '\ue9e1':'ā',
                           '\ue987':'ē',
                           '\ue9e7':'ē',
                           '\ue98d':'ī',
                           '\ue9ed':'ī',
                           '\ue997':'ū',
                           '\uf591':'ū',
                           '\uedc0':'', #probably meant to be an orthographic tonal diacritic in Latvian, but I can't figure out which one -- just remove since it's not necessary
                           '\uedc1':'́', #Lithuanian acute accent tonal diacritic
                           '\uee2d':'i̯',
                           '\uee77':'u̯'
                           #'':'ȇ'
                           }
        
        return ''.join([orth_conversion.get(ch, ch) for ch in word])
    
    problems = []
    family_vocab = defaultdict(lambda:{})
    index = 0
    for lang, c, notes_c in lang_labels:
        cognate_c = columns[columns.index(c)+1]
        try:
            new_name, glottocode, iso_code = lang_data[lang]
        except KeyError: #only extract data for the selected languages
            continue
        for r in range(3, rows[-1]+1):
            try:
                gloss = sh[f'B{r}'].value.strip()
            except AttributeError:
                x = r
                while sh[f'B{x}'].value == None:
                    x -= 1
                gloss = sh[f'B{x}'].value
            concepticon_gloss = concepticon_swadesh[gloss]
            cell = sh[f'{c}{r}']
            cell_value = cell.value
            if cell_value != None:
                variants = cell_value.split('~')
                variants = [variant.strip() for variant in variants]
                for variant in variants:
                    if variant.count('{') == 1:
                        variant = re.split(' *{', variant)
                        tr = variant[0]
                        original_tr, tr = tr, fix_tr(tr, lang)
                        orth = variant[1][:-1]
                        orth = fix_orth(orth)
                        if tr == '': #skip if there is no transcription
                            problems.append((lang, c, r, ' {'.join(variant), cell_value, 'missing transcription'))
                            pass
                        
                    elif variant.count('{') == 0: #these ones only have transcriptions, no orthographic form
                        tr = variant
                        original_tr, tr = tr, fix_tr(tr, lang)
                        orth = ''
                        
                    else:
                        problems.append((lang, c, r, variant, cell_value, variant.count('{'), 'too many { brackets in variant'))
                    
                    #Latvian-specific: change final /ʦ/ in IPA to /ts/, where orthography has <ts> or <ds>, not <c>
                    if new_name == 'Latvian':
                        if tr[-1] == 'ʦ':
                            if orth[-2:] in ['ts', 'ds']:
                                tr = tr[:-1]
                                tr += 'ts'
                        elif tr[-2:] == 'ʦː': #same here, <cs> should be /ʦs/
                            if orth[-2:] == 'cs':
                                tr = tr[:-1]
                                tr += 's'
                        elif tr[-2:] == 'sː': #same here, <ss>, <zs> should be /ss/
                            if orth[-2:] in ['ss', 'zs']:
                                tr = tr[:-1]
                                tr += 's'
                    
                    cognate_index = sh[f'{cognate_c}{r}'].value
                    cognate_id = '_'.join([concepticon_gloss, str(cognate_index)])
                    
                    index += 1
                    new_entry = family_vocab[index]
                    new_entry['ID'] = '_'.join([strip_ch(lang, ' '), str(cognate_id)])
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
                    #clean the notes a bit
                    notes = re.sub('_x0015_', '', notes)
                    new_entry['Comment'] = fix_orth(notes)
                    new_entry['Source'] = sources
    
                        
    baltoslav_subfamilies[subfamily] = family_vocab

#%%
#COMBINE DATA FROM EACH SUBGROUP INTO A SINGLE DICTIONARY
combined_baltoslav_data = {}
index = 1
for subgroup in baltoslav_subfamilies:
    for i in baltoslav_subfamilies[subgroup]:
        entry = baltoslav_subfamilies[subgroup][i]
        index +=1
        combined_baltoslav_data[index] = entry
    

#%%
#ISOLATE UNKNOWN CHARACTERS IN TRANSCRIPTIONS
print('')
all_new_chs = [ch for i in combined_baltoslav_data  
               for ch in combined_baltoslav_data[i]['Segments'] 
               if ch not in all_sounds + diacritics + [' ', 'ˑ', '̠', '̆']]

new_chs = list(set(all_new_chs))
new_chs.sort(key= lambda x: all_new_chs.count(x), reverse=True)


def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(combined_baltoslav_data[i]['Language_ID'] for i in combined_baltoslav_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in combined_baltoslav_data:
        entry = combined_baltoslav_data[i]
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

#Extract orthographic forms for Macedonian when available,
#saved in comments field as Skopje Macedonian

for i in combined_baltoslav_data:
    if combined_baltoslav_data[i]['Language_ID'] == 'Macedonian':
        form = combined_baltoslav_data[i]['Form']
        comment = combined_baltoslav_data[i]['Comment']
        if comment != '':
            if '{' in comment:
                skopje_orth = comment.split('{')[1]
                end_index = skopje_orth.index('}')
                skopje_orth = skopje_orth[:end_index]
                combined_baltoslav_data[i]['Value'] = skopje_orth
                combined_baltoslav_data[i]['Comment'] += ' Orthographic value extracted automatic from Skopje form, may differ from Dihovo form.'
                #print(i, form, skopje_orth)


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

os.chdir(current_dir)
write_data(combined_baltoslav_data, 'balto_slavic_gld_data.csv')    