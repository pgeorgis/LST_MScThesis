import os, re
from collections import defaultdict
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

#LOAD NEL DATA ABOUT LANGUAGES INCLUDED IN DATASET
language_data = csv_to_dict('Source/northeuralex-0.9-language-data.tsv', sep='\t')

#Families and subfamilies of included languages
NEL_families = set([language_data[i]['family'] for i in language_data])
NEL_subfamilies = set([f"{language_data[i]['family']}, {language_data[i]['subfamily']}" for i in language_data])


#LOAD DATA ABOUT CONCEPTS IN DATASET
concept_data = csv_to_dict('Source/northeuralex-0.9-concept-data.tsv', sep='\t')

#Take Concepticon gloss, unless there isn't one, in which case the proposed Concepticon gloss
#If that also doesn't exist, take the NELEX ID
concept_IDs = {}
for i in concept_data:
    entry = concept_data[i]
    id_nelex = entry['id_nelex']
    concepticon = entry['concepticon']
    if concepticon == '<NA>':
        concepticon = entry['concepticon_proposed']
    if concepticon != '<NA>':    
        concept_IDs[id_nelex] = concepticon
    else:
        concept_IDs[id_nelex] = id_nelex
    

#%%
#LOAD LANGUAGE CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages_all.csv', sep='\t')

#Dictionary of language names and glottocodes
glottocodes = {lang_data['Glottocode'][i]:lang_data['Source Name'][i]
               for i in range(len(lang_data))
               if lang_data['Dataset'][i] == 'NorthEuraLex'}

balto_slavic_langs = []
uralic_langs = []
for i in range(len(lang_data)):
    classification = lang_data['Classification'][i]
    if type(classification) != float:
        if 'Slavic' in classification:
            lang = lang_data['Name'][i]
            balto_slavic_langs.append(lang)
        elif 'Uralic' in classification:
            lang = lang_data['Name'][i]
            uralic_langs.append(lang)

baltoslavic_langs = set([lang_data['Name'][i] for i in range(len(lang_data['Name']))
                         if type(lang_data['Classification'][i]) == str 
                         if 'Slavic' in list(lang_data['Classification'][i])])

lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'NorthEuraLex'}

#LOAD WORD FORM DATA
forms_data = csv_to_dict('Source/northeuralex-0.9-forms.tsv', sep='\t')

#Transform data into different type of dictionary
NEL_data = defaultdict(lambda:{})

conversion_dict = {'à':'a', #Chuvash, unclear why the diacritic is there; just remove it
                   'á':'a', #Abkhaz and Northern Pashto, unclear why the diacritic is there; just remove it 
                   'ē':'eː', #Northern Sami, macron over vowel indicates long vowel
                   'ḥ':'hˑ', #Inari Sami, dot below indicates half-long consonant 
                   'ī':'i', #Bengali, probably a mistakenly used diacritic [নীল, /nil/, blue]
                   'ō':'oː', #Northern Sami, macron over vowel indicates long vowel
                   'ò':'ô', #Lithuanian, one word uses tone orthographic 'ò' instead of 'ô' 
                   'ô':'oː', #Northern Kurdish, <ô> represents long vowel
                   'õ':'õ', #Portuguese, replace with sequence of /o/ with nasal diacritic instead of o with tilde
                   'ž':'ʒ', #Livonian, some 'ž' accidentally in transcription instead of 'ʒ'
                   
                   '-':'', #several languages, seems to be punctuation that wasn't properly removed from transcriptions
                   '|':''} #Russian, marks syllable boundaries in a few words

def fix_transcription(word):
    #remove spaces and secondary stress marking from words
    word = ''.join([conversion_dict.get(ch, ch) for ch in word if ch not in [' ', 'ˌ']])
    
    #fix position of primary stress annotation (make it immediately precede the stress-bearing segment)
    stress_marked = False
    if 'ˈ' in word:
        stress_marked = True
    #elif 'ˌ' in word:
    #    stress_marked = True
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
    
    #equivalent affricate representations, latter versions are cleaner to read
    affricate_conversion = {'t͡s':'ʦ', 'd͡z':'ʣ', 't͡ʃ':'ʧ', 'd͡ʒ':'ʤ', 't͡ɕ':'ʨ', 'd͡ʑ':'ʥ'}
    for affricate in affricate_conversion:
        word = re.sub(affricate, affricate_conversion[affricate], word)
        
                   
    
    return word

#%%
problems = []
missing = []
for i in forms_data:
    entry = forms_data[i]
    lang = glottocodes[entry['Glottocode']]
    try:
        new_name, glottocode, iso_code = lang_data[lang] 
    except KeyError:
        missing.append((lang, entry['Glottocode']))
        new_name, glottocode, iso_code = '', '', ''
    gloss = concept_IDs[entry['Concept_ID']]
    if gloss == '<NA>':
        print(i, entry['Concept_ID'])
    orth = entry['Word_Form']
    try:
        original_tr, tr = entry['rawIPA'], entry['rawIPA']
        
        #in Northern Khanty, "lˈ" seems to be used to represent "ɭ"
        if lang == 'Northern Khanty':
            if 'lˈ' in tr:
                new_tr = [tr[0]]
                offset = 0
                for i in range(1, len(tr)):
                    if tr[i] == 'ˈ':
                        assert tr[i-1] == 'l'
                        new_tr[i-1-offset] = 'ɭ'
                        offset += 1

                    else:
                        new_tr.append(tr[i])
                tr = ''.join(new_tr)
        
        #in Burushaski, letters with a dot diacritic '̇' need to be converted to IPA
        #conversions taken from Burushaski language Wikipedia page
        elif lang == 'Burushaski':
            dot = '̇'
            dot_dict = {'ɡ':'ʁ','n':'ŋ','s':'ʂ'}
            if dot in tr:
                new_tr = [tr[0]]
                offset = 0
                for i in range(1, len(tr)):
                    if tr[i] == dot:
                        dotted = tr[i-1]
                        new_tr[i-1-offset] = dot_dict[dotted]
                        if dotted == 's':
                            new_tr[i-3-offset] = 'ʈ'
                        offset += 1
                    else:
                        new_tr.append(tr[i])
                tr = ''.join(new_tr)
        
        #in Northern Sami, <í> presumably represents a long vowel, as analogous to <á> /aː/
        #in Aleut, it's unclear, but probably marks stress (and we can just remove it), since <ii> marks long /iː/
        elif lang == 'Northern Sami':
            fix = {'í':'iː'}
            tr = ''.join([fix.get(ch, ch) for ch in tr])

        
        #in Catalan, reflexive verbs ending in <'s> have an unneeded stress marking, e.g. <caure's>	/kəwɾəˈs/
        #same for the single verb <anar-se'n>	/ənəɾzəˈn/
        elif lang == 'Catalan':
            if 'ˈs' in tr:
                tr = ''.join([ch for ch in tr if ch != 'ˈ'])
            elif 'ˈn' in tr:
                tr = ''.join([ch for ch in tr if ch != 'ˈ'])
        
        #mistake in Italian transcription of "un po'" /un poˈ/ (has extra stress marking)
        elif lang == 'Italian':
            if tr == 'un poˈ':
                tr = 'un po'
                
        #similar transcription issue in Aleut, <an'g> /anˈɡ/
        #plus fix to issue described above for Northern Sami
        elif lang == 'Aleut':
            fix = {'í':'i'}
            tr = ''.join([fix.get(ch, ch) for ch in tr])
            if tr == 'anˈɡ':
                tr = 'anɡ'
                
        #mistake in Hindi, <शेल्फ़> /sélf/ (shelf) --> /ɕeːlf/
        elif lang == 'Hindi':
            if tr == 'sélf':
                tr = 'ɕeːlf'
                
        elif lang == 'Russian':
            #Russian: palatalized /l/ <ль> or <л> followed by soft vowel transcribed
            #as /l/ instead of /lʲ/
            #simply changing all instances of /l/ to /lʲ/ isn't a problem because 
            #the non-palatalized version is transcribed as /ɫ/
            tr = re.sub('l', 'lʲ', tr)
            
            #Russian: <щ> transcribed as /ʃʃ/ instead of /ɕː/
            tr = re.sub('(?<!͡)ʃʃ', 'ɕː', tr)
            
            #and <ч> as <t͡ʃʲ> instead of <ʨ>
            tr = re.sub('t͡ʃʲ', 'ʨ', tr)
        
        tr = fix_transcription(tr)
        
        
    except IndexError:
        print(lang, entry['rawIPA'])
        problems.append((lang, entry['rawIPA']))
        
    
    new_entry = NEL_data[i]
    new_entry['ID'] = '_'.join([strip_ch(new_name, [' ']), gloss])
    new_entry['Language_ID'] = new_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code
    new_entry['Parameter_ID'] = gloss
    new_entry['Value'] = orth
    new_entry['Form'] = tr
    new_entry['Segments'] = ' '.join(segment_word(tr))
    new_entry['Source_Form'] = original_tr
    new_entry['Cognate_ID'] = gloss
    new_entry['Loan'] = ''
    new_entry['Comment'] = ''
    new_entry['Source'] = ''
    
    
    #NEL_data[lang][gloss].append((orth, tr))
    #NEL_data[lang][gloss] = list(set(NEL_data[lang][gloss]))

#%%
#CHECKING PHONETIC CHARACTERS
NEL_phones = set([ch for i in NEL_data 
                  for ch in NEL_data[i]['Form']])

new_NEL_phones = [phone for phone in NEL_phones 
                  if phone not in all_sounds+diacritics]

def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(NEL_data[i]['Language_ID'] for i in NEL_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in NEL_data:
        entry = NEL_data[i]
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
#CREATE PROCESSED LANGUAGE FAMILY DOCUMENT
def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            values = sep.join([str(data_dict[i][feature]) for feature in features])
            f.write(f'{values}\n')

 


balto_slavic_NEL_data = {i:NEL_data[i] for i in NEL_data 
                         if NEL_data[i]['Language_ID'] in balto_slavic_langs}
uralic_NEL_data = {i:NEL_data[i] for i in NEL_data 
                   if NEL_data[i]['Language_ID'] in uralic_langs}


if len(problems) == 0:
    write_data(NEL_data, 'northeuralex_data.csv')
    write_data(balto_slavic_NEL_data, str(parent_dir) + '/Balto-Slavic/balto_slavic_data.csv')
    write_data(uralic_NEL_data, str(parent_dir) + '/Uralic/uralic_NEL_data.csv')
        
        
        