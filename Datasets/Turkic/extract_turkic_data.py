from openpyxl import load_workbook
from collections import defaultdict
import pandas as pd
import os, re
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import strip_ch
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
             if lang_data['Dataset'][i] == 'Turkic'}


turkic_vocab = load_workbook('Source/SI3_Basic_vocabulary_datasets_for_the_Turkic_languages_modified.xlsx')

#%%
#LOAD TURKIC VOCABULARY SPREADSHEET
sh = turkic_vocab['Sheet1']
columns = [i[0].column_letter for i in list(sh.columns)]
rows = list(range(1,len(list(sh.rows))+1))

data_columns = columns[2:columns.index('BM')]

#Extract language labels 
lang_labels = [(sh[f'{c}1'].value, c) for c in data_columns if data_columns.index(c) % 2 == 0]
#(language, column)


#%%
#PROCESS GLOSSES AND MAP TO CONCEPTICON EQUIVALENTS
glosses = [sh[f'A{r}'].value for r in range(3,915)]

concepticon_turkic = pd.read_csv('Source/ConceptIconValues.tsv', sep='\t')
concepticon_conversion = {concepticon_turkic['Name'][i].split(' [')[0]:concepticon_turkic['Parameter'][i]
                          for i in range(len(concepticon_turkic['Name']))}

#%%
#TRANSCRIPTION PRE-PROCESSING

conversion_dict = {#Consonants
                   'č':'ʧ', #Shor and Dolgan, represents affricate /ʧ/
                   'g':'ɡ',
                   'γ':'ɣ',
                   'ǰ':'ʤ',
                   'ʥ':'ʤ',
                   'ʨ':'ʧ', #re-transcribe as post-alveolar to match <ǰ>, <š>, etc.
                   'š':'ʃ',
                   
                   #Vowels
                   'a':'ɑ', #back vowel
                   'ä':'ɛ', #seems to be the common Turkic orthographic form for /ɛ/
                   'ẹ':'e', #unknown, but 'ẹ' seems to correspond with /e/ between Proto-Turkic and Old Turkic
                   'ï':'ɯ', #mistakenly left in common Turkic orthographic form
                   'ụ':'u', #meant to be /u/ according to same word entry in NorthEuraLex for Chuvash (mountain, /tu/)
                   'Ɯ':'ɯ',

                   #Vowel/consonant harmony
                   'V':'ɑ', #vowel harmony with no set features; however, other languages have <A> here, so convert to /ɑ/ to parallel them
                   'A':'ɑ', #back vowel harmony, convert to /ɑ/
                   'E':'e', #front vowel harmony, convert to /e/
                   'O':'o', #Baraba Tatar, unknown but seems to be vowel harmony, convert to /o/
                   'U':'u', #same as above
                   'D':'d', #consonant harmony
                   'T':'t', #consonant harmony
                   'B':'b', #possibly another type of consonant harmony? appear in morpheme for "not" in Chulym
                   
                   
                   #Diacritics
                   'ˁ':'ˤ',
                   ':':'ː',

                   #Language specific corrections
                   ('ḳ', 'Azeri'):'ɡ', #mistake, <q> in Azerbaijani is /ɡ/
                   ('ɢ', 'Azeri'):'ɡ', #change /ɢ/ to /ɡ/
                   ('ɛ', 'Azeri'):'æ', #better transcription in accordance with Illustrations of the IPA
                   ('ĕ', 'BarabaTatar'):'ë', #presumably 
                   ('ŭ', 'BarabaTatar'):'ö', #presumably 
                   ("'", 'CrimeanTatar'):'', #not included in transcriptions at http://turkic.elegantlexicon.com/lxforms.php?lx=ctt; palatalized /l/ doesn't appear in Crimean Tatar's phonological inventory
                   
                   #orthography     NorthEuraLex  	TurkicDataset		Narrow IPA	Example
                   #ӑ			    ə			    ə̈				    ɤ̆ʷ			bird
                   #ӑ			    ə			    ö				    ɤ̆ʷ			bone
                   #ӗ			    ɘ			    ø̈				    ɘ̆ʷ			smoke
                   ('ö', 'Chuvash'):'ɤ̆ʷ', #mistake, IPA and orthography flipped in this case; also see https://en.wikipedia.org/wiki/Chuvash_language#Vowels for narrower transcription
                   
                   ("'", 'Dolgan'):'́',
                   ('ŭ', 'Kazakh'):'ʊ', #according to https://en.wikipedia.org/wiki/Kazakh_language#Phonology
                   ("'", 'Khalaj'):'', #palatalization of the vowel? this character otherwise denotes palatalization, but unsure here. 
                   #written as 'ʹ' at http://turkic.elegantlexicon.com/lxforms.php?lx=klj , but no explanation given to its meaning
                   ("'", 'MiddleChulym'):'', #not listed in any of the entries at http://turkic.elegantlexicon.com/lxforms.php?lx=mch, nor does it seem to have any phonemic equivalent at http://turkic.elegantlexicon.com/transcription.php
                   ("'", 'Salar'):'', #unclear, possibly a typo
                   ('ö', 'Salar'):'ø', #anomalous mistake
                   ("'", 'SarygYugur'):'', #palatalized /l/ doesn't appear in phoneme inventory, not listed at http://turkic.elegantlexicon.com/lxforms.php?lx=yug or at wikipedia page for West Yugur phonology
                   ('s', 'Turkmen'):'θ', #must be mistake, <s> in Turkmen in /θ/
                   ('z', 'Turkmen'):'ð', #must be mistake, <z> in Turkmen is /ð/
                   ('ɢ', 'Turkmen'):'ɡ', #<g> in Turkmen is velar /ɡ/, not uvular /ɢ/
                   ('q', 'Turkish'):'k', #mistake, no /q/ in standard Turkish
                   ('ɣ', 'Turkish'):'ː', #represents <ğ>, a debatable phoneme in Turkish; realized as lengthening of previous vowel
                   ('ḳ', 'Shor'):'q', #mistake
                   
                   
                   #Other characters
                   "'":'ʲ', #elsewhere seems to denote palatalization
                   '?':'',
                   '-':'',
                   '*':'', #unknown, appears in Chulym, Northern Altai, Khalaj
                   'Р':'', #unknown purpose in Northern Altai, seems to be an annotation of some kind
                   '1':'', #unclear why the numbers are there, clearly some kind of annotation
                   '2':'', #unclear why the numbers are there, clearly some kind of annotation
                   '`':'', #seems to be a typo
                   }

def has_parentheses(string):
    if ')' in string:
        return True
    elif '(' in string:
        return True
    else:
        return False   
    
def strip_parentheses(string):
    while has_parentheses(string) == True:
        string = re.sub(r'\([^()]*\)', '', string)
    return string

def fix_tr(word, lang):
    if word != None:
        #Strip parenthetical annotations
        word = strip_parentheses(word)
            
        #strip 'etc.' annotation
        word = re.sub('etc\.*', '', word)
        
        #strip 'dial.' annotation (dialectal)
        word = re.sub('dial\.', '', word)
        
        #strip '3SG' annotation
        word = re.sub('3SG', '', word)
        
        #strip 'inf.' annotation
        word = re.sub('inf\.', '', word)
        
        #strip anything after '+' (e.g. "+ motion verb")
        word = re.sub('\+.*', '', word)
        
        #Regular expression correction
        word = re.sub('tɕ', 'ʨ', word)
        word = re.sub('nń', 'ɲɲ', word) #according to https://en.wikipedia.org/wiki/Dolgan_language#/media/File:Dolgan.gif
        word = re.sub('ń', 'ɲ', word)
        word = re.sub('ń', 'ɲ', word) #2 characters, n with acute accent
        #given that 'ń' represents a palatal sound, 
        #also note that the words in Northern Altai with these characters have equivalents beginning with /j/ in Turkish
        #we can assume that 'd́' and 't́' likewise correspond to palatal stops; note similarity to <t'> and <d'> in SouthAltai, which are transcribed as palatal stops
        #similar use in Dolgan
        word = re.sub('d́', 'ɟ', word)
        word = re.sub('t́', 'c', word)
        word = re.sub('gj', 'gʲ', word) #Azerbaijani
        word = re.sub('gʲ', 'ɟ', word) #Azerbaijani
        
        if lang == 'Gagauz':
            word = re.sub("s'", 'z', word)
            #see http://turkic.elegantlexicon.com/lxforms.php?lx=gag
            #also note that /z/ is the reflex of Proto-Turkic /ŕ/ in all other cases
        elif lang == 'Tofa':
            word = re.sub("n'", 'ɲ', word) 
            #see http://turkic.elegantlexicon.com/lxforms.php?lx=tof
        
        elif lang in ['Turkish', 'Azeri']:
            front_vowels = ['e', 'i', 'ø', 'y', 'æ', 'ɛ']
            back_vowels = ['a', 'ɯ', 'o', 'u'] #/a/ not changed to /ɑ/ until conversion dict
            velar_palatalization = {'k':'c', 'g':'ɟ'} #not changed to /ɡ/ until conversion dict
            
            #Palatalization of velars adjacent to front vowels
            for velar_stop in velar_palatalization: 
                palatalized = velar_palatalization[velar_stop]
                for front_vowel in front_vowels:
                    word = re.sub(f'{velar_stop}{front_vowel}', f'{palatalized}{front_vowel}', word)
                    word = re.sub(f'{front_vowel}{velar_stop}', f'{front_vowel}{palatalized}', word)
            
            if lang == 'Turkish':
                #/ɫ/ adjacent to back vowels, /lʲ/ adjacent to front vowels
                for back_vowel in back_vowels:
                    word = re.sub(f'l{back_vowel}', f'ɫ{back_vowel}', word)
                    word = re.sub(f'{back_vowel}l', f'{back_vowel}ɫ', word)
                word = re.sub('l', 'lʲ', word)
                
                word = re.sub('yʃtynde', 'ystynde', word) #mistranscribed word in Turkish
            
            elif lang == 'Azeri':
                word = re.sub('bɛrk', 'bɛrc', word) #palatalized velar which would not be captured by above rules
                
            
        
        #Chuvash notes:
        #orthography     NorthEuraLex  	TurkicDataset		Narrow IPA	Example
        #ӑ			    ə			    ə̈				    ɤ̆ʷ			bird
        #ӑ			    ə			    ö				    ɤ̆ʷ			bone
        #ӗ			    ɘ			    ø̈				    ɘ̆ʷ			smoke
        word = re.sub('ə̈', 'ɤ̆ʷ', word)
        word = re.sub('ø̈', 'ɘ̆ʷ', word)
        
        #Conversion dict correction -- needs to come after reg exp
        word = ''.join([conversion_dict.get(ch, ch) for ch in word])
        word = ''.join([conversion_dict.get((ch, lang), ch) for ch in word])
        
        
        #strip any remaining white space
        word = word.strip()
        
        return word
    else:
        return word
    

    
#%%
turkic_data = defaultdict(lambda:{})
index = 0
missing_glosses = []
for row in range(3, 915): #word entries go from lines 3-914 in Excel dataset
    go_back = 0
    while glosses[row-3-go_back] == None:
        go_back += 1
    
    #Get gloss and convert to Concepticon gloss
    gloss = glosses[row-3-go_back]
    concepticon_gloss = concepticon_conversion[gloss]
    if type(concepticon_gloss) == float: #nan (N/A)
        concepticon_gloss = gloss.upper()
        missing_glosses.append(gloss)
    parameter_ID = concepticon_gloss
    
    #Create cognate ID for row
    cognacy_ID = parameter_ID + '_' + str(go_back+1)
    
    #Iterate through columns to get each language's reflex of the cognate set
    for lang, c in lang_labels:
        orth_c, tr_c = c, data_columns[data_columns.index(c)+1]
        orth = sh[f'{orth_c}{row}'].value
        tr = sh[f'{tr_c}{row}'].value
        
        if tr != None:
            if orth == None:
                orth = ''
            
            #first strip parentheses to avoid confounding annotations
            tr, orth = strip_parentheses(tr), strip_parentheses(orth)
            
            #same with quotation mark annotations
            tr = re.sub("'.*'", '', tr)
            orth = re.sub("'.*'", '', orth)
            
            #same with bracket annotations
            tr = re.sub("\[.*\]", '', tr)
            orth = re.sub("\[.*\]", '', orth)
            
            #same with annotations within < >
            tr = re.sub("<.*>", '', tr)
            orth = re.sub("<.*>", '', tr)
            
            #variants/reflexes of the same cognate entry separated by ',' or ';' or '~' or '/' or '>' or '>' or '='
            variant_tr = [word.strip() for word in re.split(',|~|\/|>|<|;|=', tr)]
            variant_orth = [word.strip() for word in re.split(',|~|\/>|<|;|=', orth)]
            variants = list(zip(variant_orth, variant_tr))
            
            #preprocess/fix the transcription for all variants
            fixed_variants = []
            for i in range(len(variants)):
                orth, tr = variants[i]
                original_tr = tr[:]
                fixed_tr = fix_tr(tr, lang)
                fixed_variants.append((orth, fixed_tr, original_tr))
            
            for variant in fixed_variants:
                orth, tr, fixed_tr = variant
                if len(fixed_tr.strip()) > 0:
                    index += 1
                    new_entry = turkic_data[index]
                    segments = ' '.join(segment_word(tr))
    
                    lang_name, glottocode, iso_code = lang_data[lang]
                    if type(glottocode) == float: #nan
                        glottocode = ''
                    if type(iso_code) == float: #nan
                        iso_code = ''
                        
                    new_entry['ID'] = '_'.join([strip_ch(lang_name, [' ']), cognacy_ID])
                    new_entry['Language_ID'] = lang_name
                    new_entry['Glottocode'] = glottocode
                    new_entry['ISO 639-3'] = iso_code
                    new_entry['Parameter_ID'] = parameter_ID
                    new_entry['Value'] = orth
                    new_entry['Form'] = tr
                    new_entry['Segments'] = segments
                    new_entry['Source_Form'] = original_tr
                    new_entry['Cognate_ID'] = cognacy_ID
                    new_entry['Loan'] = ''
                    new_entry['Comment'] = ''
                    new_entry['Source'] = 'Savelyev & Robeets, 2020'


#%%
#ISOLATE PROBLEMS AND UNKNOWN CHARACTERS

new_chs = set([ch for i in turkic_data
               for ch in turkic_data[i]['Segments'] 
               if ch not in all_sounds + diacritics + [" "]])

def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(turkic_data[i]['Language_ID'] for i in turkic_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in turkic_data:
        entry = turkic_data[i]
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

def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            try:
                values = sep.join([data_dict[i][feature] for feature in features])
            except TypeError:
                print(data_dict[i])
            f.write(f'{values}\n')
            
write_data(turkic_data, output_file='turkic_data.csv')

    
    