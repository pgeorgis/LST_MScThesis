import pandas as pd
import os, re
from collections import defaultdict
from wiktionaryparser import WiktionaryParser #for extracting Maltese IPA from Wiktionary
parser = WiktionaryParser()
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
#Scrape tables from Wiktionary
link = 'https://en.wiktionary.org/w/index.php?title=Appendix:Varieties_of_Arabic_Swadesh_lists&oldid=62250595'
tables = pd.read_html(link,header=0)[:-1] #don't include the last table (not part of dataset)

#Some tables use different names/headers for the same dialect
#Standardize the dialect names
renamed_columns = {'Tunisian':'Tunisian (Tunis)',
                   'Sudanese':'Sudanese (Khartoum)',
                   'Najdi (KSA/Riyadh)':'Najdi (Riyadh)',
                   'Cypriot':'Cypriot (Kormakitis)',
                   "Sanaani (Sana'a/Yemeni)":"Sanaani (Sana'a)",
                   "Baghdadi (Central Iraq)":'Iraqi (Southern Iraq/Baghdad)',
                   'Dhofari (Dhofar)':'Dhofari (Oman)',
                   'Egyptian (Delta)':'Egyptian (Lower Egyptian)',
                   'North Levantine (Central/Beirut)':'Levantine (Central/Syro-Lebanese)'
                   }
for i in range(len(tables)):
    table = tables[i]
    tables[i] = table.rename(columns=renamed_columns)

#Concatenate the tables
df = pd.concat(tables)
df.to_csv('Source/arabic_dialects_swadesh_wiktionary.csv', sep='\t')

#%%
#LOAD LANGUAGE CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Arabic'}

#%%
#LOAD CONCEPTICON MAPPING
concept_data = csv_to_dict('Source/Concepticon Wiktionary-2003-207.csv', sep='\t')
concept_dict = {strip_ch(concept_data[i]['Name'].split(' [')[0], [' ']):concept_data[i]['Parameter']
                for i in concept_data}

concept_dict['you(singular)'] = 'THOU'
concept_dict['you(plural)'] = 'YOU'
concept_dict['man(human being)'] = 'PERSON'
concept_dict['bark(of tree)'] = 'BARK'
concept_dict['rain'] = 'RAIN (PRECIPITATION)'
concept_dict['ash'] = 'ASH'
concept_dict['rotten(asalog)'] = 'ROTTEN'


#%%
#Load the csv file
arabic_data = csv_to_dict('Source/arabic_dialects_swadesh_wiktionary.csv', sep='\t')

#%%

conversion_dict = {#Vowels
                   'e':'ɛ',
                   'o':'ɔ',
                   'â':'ɒː',
                   'é':'e',
                   'ă':'ʌ',
                   'ā':'aː',
                   'ɑ̄':'ɑː',
                   'ē':'ɛː',
                   'ī':'iː',
                   'ō':'ɔː',
                   'ū':'uː',
                   'ǝ':'ə',
                   'ɘ':'ə', #most likely intended to be schwa 
                   
                   #Vowels with breve 
                   #"Vowels with a breve are brought to a low-mid articulation."
                   'ǎ':'ʌ',
                   'ě':'ɛ',
                   'ĕ':'ɛ',
                   'ǐ':'ɛ',
                   'ĭ':'ɛ',
                   'ŏ':'ɔ', #already low-mid
                   'ŭ':'ɔ',
                   
                   
                   #Cypriot Arabic uses acute accents
                   #presumably marks stress but it's unclear, so just remove the accent marks
                   'á':'a',
                   'ó':'o',
                   'ú':'u',
                   
                   #Consonants
                   'ḅ':'bˤ',
                   'č':'ʧ',
                   'ḍ':'dˤ',
                   'g':'ɡ',
                   'ğ':'ɡʲ',
                   'ġ':'ɣ',
                   'ḥ':'ħ',
                   'j':'ʤ',
                   'ḷ':'lˤ',
                   'ṃ':'mˤ',
                   'ṇ':'nˤ',
                   'ṛ':'rˤ',
                   'š':'ʃ',
                   'ṣ':'sˤ',
                   'ṡ':'sˤ',
                   'ṭ':'tˤ',
                   'ṿ':'vˤ',
                   'ẉ':'wˤ',
                   'y':'j',
                   'ỵ':'jˤ',
                   'ž':'ʒ',
                   'ẓ':'zˤ',
                   'ˁ':'ʕ',
                   '̣':'ˤ',
                   
                   #Language-Specific Conversions
                   ('g', 'Sudanese (Khartoum)'):'ɢ',
                   ('g', "Sanaani (Sana'a)"):'ɢ', #https://en.wikipedia.org/wiki/Voiced_uvular_plosive#Occurrence
                   ('ɣ', "Sanaani (Sana'a)"):'ʁ', 
                   ('ħ', 'Iraqi (Southern Iraq/Baghdad)'):'ʜ',
                   ('ḥ', 'Iraqi (Southern Iraq/Baghdad)'):'ʜ',
                   ('í', 'Cypriot (Kormakitis)'):'i',
                   ('θ', 'Hassaniya (Mauritanian)'):'θ̬',
                   ('x', 'Sudanese (Khartoum)'):'χ',
                   ('x', "Sanaani (Sana'a)"):'χ',
                   ('ʕ', 'Egyptian (Lower Egyptian)'):'ʕ̞',
                   ('ʕ', 'Iraqi (Southern Iraq/Baghdad)'):'ʢ',
                   
                   #Other
                   '́':'', #Moroccan Arabic, probably marks stress, remove it
                   '.':' ', #used in context of <...>, replace with a space
                   '-':'', #used to mark word stems/affixes, remove it
                   
                   }

def has_parentheses(string):
    if ')' in string:
        return True
    elif '(' in string:
        return True
    else:
        return False

to_transcribe = []
def transcribe_maltese(word, gloss):
    word_entry = parser.fetch(word, 'Maltese')
    if len(word_entry) > 0:
        word_entry = word_entry[0]
        pronunciation = word_entry['pronunciations']['text']
        if len(pronunciation) > 0:
            pronunciation = pronunciation[0] #if more than one pronunciation, take the first listed one as default
            tr_start = pronunciation.index('/') + 1
            tr_end = pronunciation[tr_start:].index('/') + tr_start
            tr = pronunciation[tr_start:tr_end]
            original_tr = tr[:]
            
            #strip stress and syllable segmentation
            tr = strip_ch(tr, ['ˈ', '.'])
            
            #Strip parenthetical annotations
            while has_parentheses(dialect_entry) == True:
                tr = re.sub(r'\([^()]*\)', '', tr)
            
            #convert any other characters
            maltese_conversion = {'a':'ɐ',
                                  'e':'ɛ',
                                  'o':'ɔ',
                                  'u':'ʊ',
                                  'g':'ɡ'}
            tr = ''.join([maltese_conversion.get(ch, ch) for ch in tr])
            
            #and some regular expressions
            tr = re.sub('i(?!ː)', 'ɪ', tr) #change all short /i/ to /ɪ/
            tr = re.sub('t͡ʃ', 'ʧ', tr)
            tr = re.sub('d͡*ʒ', 'ʤ', tr)
            tr = re.sub('t͡s', 'ʦ', tr)
            tr = re.sub('d͡z', 'ʣ', tr)
            
            print(f'<{word}> /{tr}/ "{gloss}"')
            return original_tr, tr
            
        else:
            to_transcribe.append((word, gloss))
            return None
    
    else:
        to_transcribe.append((word, gloss))
        return None
    
    

def fix_tr(word, lang, gloss):
    if lang == 'Maltese':
        return transcribe_maltese(word, gloss)
    
    else:
        #Fix words using conversion dict
        word = ''.join([conversion_dict.get((ch, lang), ch) for ch in word])
        word = ''.join([conversion_dict.get(ch, ch) for ch in word])
        
        #Fix words using regular expressions (multiple characters)
        word = re.sub('t͡s', 'ʦ', word)
        word = re.sub('d͡*ʒ', 'ʤ', word)
        word = re.sub('ɑ̄', 'ɑː', word)
        word = re.sub('[ìí][eɛ]', 'ɪe̯', word)
        
        return word


dialects = ['Arabic (MSA)',
 'Najdi (Riyadh)',
 'Gulf (Emirati)',
 'Levantine (Central/Syro-Lebanese)',
 #'Basra (Southern Iraq)',
 'Iraqi (Southern Iraq/Baghdad)',
 'Moslawi (Northern Iraq)',
 "Sanaani (Sana'a)",
 'Dhofari (Oman)',
 'Cypriot (Kormakitis)',
 'Egyptian (Lower Egyptian)',
 'Sudanese (Khartoum)',
 'Chadian (Western Sudanic)',
 'Tunisian (Tunis)',
 'Moroccan (Casablanca)',
 #'Moroccan (Northern pre-Hilalian)',
 'Hassaniya (Mauritanian)',
 'Maltese']

processed_arabic_data = defaultdict(lambda:{})

j = 0
for i in arabic_data:
    entry = arabic_data[i]
    for dialect in dialects:
        new_name, glottocode, iso_code = lang_data[dialect]
        if len(entry[dialect].strip()) > 0:
            dialect_entry = entry[dialect]
            
            #If there are masculine and feminine forms for a given word entry, take only the masculine as default
            dialect_entry = dialect_entry.split(' (m),')[0]
            
            #Strip parenthetical annotations
            while has_parentheses(dialect_entry) == True:
                dialect_entry = re.sub(r'\([^()]*\)', '', dialect_entry)
            
            words = re.split('\s*[,;~/]\s*', dialect_entry) #split by ',', ';', or '~'
            for word in words:
                original_tr = word.strip()
                orth = original_tr[:]
                gloss = strip_ch(entry['English'], [' '])
                concepticon_gloss = concept_dict[gloss]
                tr = fix_tr(original_tr, dialect, gloss)
                if type(tr) == tuple: #separate out the original and fixed transcription for Maltese, which is returned as a tuple
                    original_tr, tr = tr
                if tr != None:
                
                    j += 1
                    new_entry = processed_arabic_data[j]
                    
                    new_entry['ID'] = '_'.join([strip_ch(new_name, [' ']), concepticon_gloss])
                    new_entry['Language_ID'] = new_name
                    new_entry['Glottocode'] = glottocode
                    new_entry['ISO 639-3'] = iso_code
                    new_entry['Parameter_ID'] = concepticon_gloss
                    new_entry['Value'] = orth
                    new_entry['Form'] = tr
                    new_entry['Segments'] = ' '.join(segment_word(tr))
                    new_entry['Source_Form'] = original_tr
                    new_entry['Cognate_ID'] = concepticon_gloss
                    new_entry['Loan'] = ''
                    new_entry['Comment'] = ''
                    new_entry['Source'] = 'Wiktionary'

#%%
#ISOLATE UNKNOWN CHARACTERS IN TRANSCRIPTIONS

new_chs = set([ch for i in processed_arabic_data
               for ch in processed_arabic_data[i]['Segments'] 
               if ch not in all_sounds + diacritics])

def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(processed_arabic_data[i]['Language_ID'] for i in processed_arabic_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in processed_arabic_data:
        entry = processed_arabic_data[i]
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

write_data(processed_arabic_data, 'arabic_data.csv')   

                   
            