from collections import defaultdict
import pandas as pd
import os, re
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
#LOAD LANGUAGE CSVs
print('Loading language metdata...')
lang_data = pd.read_csv(str(parent_dir) + '/Languages_all.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Uralic'}


uralic_lang_data = csv_to_dict('Source/cldf/languages.csv', sep=',')
uralic_ids = {uralic_lang_data[i]['ID']:uralic_lang_data[i]['Name'] 
              for i in uralic_lang_data}

#%%
#LOAD CONCEPTS
print('Loading concepts...')
concept_data = csv_to_dict('Source/cldf/parameters.csv', sep=',')

concept_dict = {concept_data[i]['ID']:concept_data[i]['Concepticon_Gloss']
                for i in concept_data}

#Load mappings of differing labels for the same concept group
all_concepts = pd.read_csv(str(parent_dir) + '/Concepts/concepts.csv', sep='\t')
base_concepts = {list(all_concepts.Concept)[i]:list(all_concepts.BaseConcept)[i] 
                 for i in range(len(all_concepts))}


#%%
#LOAD COGNATE SETS AND BORROWING DATA
print('Loading cognate sets...')
cognate_data = csv_to_dict('Source/cldf/cognates.csv', sep=',')

cognate_dict = {cognate_data[i]['Form_ID']:cognate_data[i]['Cognateset_ID']
                for i in cognate_data}

loan_data = csv_to_dict('Source/cldf/borrowings.csv', sep=',')

loan_list = set(loan_data[i]['Target_Form_ID'] for i in loan_data)

#%%
print('Loading UraLex word form data...')
forms_data = csv_to_dict('Source/cldf/forms.csv', sep=',')

raw_data = csv_to_dict('Source/raw/Data.tsv', sep='\t')
raw_data_dict = {}
for i in raw_data:
    lang_id = strip_ch(raw_data[i]['"lgid3"'], ['"'])
    
    #first check if there is an entry for item_UPA, and if not then try item
    check_field = '"item_UPA"'
    if raw_data[i][check_field] == '':
        check_field = '"item"'
    item = strip_ch(raw_data[i][check_field], ['"'])
    item_IPA = strip_ch(raw_data[i]['"item_IPA"'], ['"'])
    
    #if there is no entry for IPA, skip
    if item_IPA.strip() != '':
        #change a few characters to proper IPA equivalents
        #(in order to ignore these differences when flagging transcription discrepancies later)
        item_IPA = re.sub('g', 'ɡ', item_IPA)
        item_IPA = re.sub('tʃ', 'ʧ', item_IPA)
        item_IPA = re.sub('dz', 'ʣ', item_IPA)
        item_IPA = re.sub('ĭ', 'i̯', item_IPA)
        
        item = item.split(', ')
        item_IPA = item_IPA.split(', ')
        for pair in zip(item, item_IPA):
            item, item_IPA = pair
            raw_data_dict[(lang_id, item)] = item_IPA

conversion_dict = {#Consonants
                   'ʙ':'b̥', #Ingrian; according to raw transcription file
                   'č':'ʧ', #Erzya, Meadow Mari, Udmurt, Votic, Nganasan, Selkup, Khanty; see raw transcription file
                   'ć':'ʨ', #Selkup, Komi-Permyak; according to raw transcription file
                   'ᴅ':'d̥', #Ingrian; according to raw transcription file
                   'δ':'ð', #not an IPA character, NorthEuraLex has <ð> for Nganasan and Mari; raw data file also shows <ð>
                   'g':'ɡ', #not the IPA /ɡ/
                   'ɢ':'ɡ̊', #Ingrian; according to raw transcription file, but using correct /ɡ/ character
                   'ʝʲ':'ʝ', #Kildin Saami; no sense in palatalizing an already palatal consonant
                   'j̊ʲ':'j̊', #Kildin Saami; no sense in palatalizing an already palatal consonant
                   'ń':'ɲ', #Erzya, Nganasan, Selkup, Mansi, Khanty; according to their respective Wikipedia phonology descriptions
                   'ŕ':'rʲ', #Erzya, according to raw transcription file
                   'š':'ʃ', #Erzya, Meadow Mari, Udmurt
                   'ś':'ɕ', #Mansi, Komi-Permyak, Nganasan, Komi-Zyrian, Udmurt; according to their respective Wikipedia phonology descriptions
                   #for Nganasan, raw data also shows [ɕ]
                   'ᴢ':'z', #apparently not the proper /z/ character
                   'ž':'ʒ', #Erzya, Meadow Mari, Komi-Zyrian; according to raw data file
                   'ź':'ʑ', #Erzya, Udmurt; both according to raw data file
                   'ˀ':'ʔ', #Nganasan; raw transcription file uses /ʔ/
                   
                   #Vowels
                   'ā':'ɑː', #Ingrian, Nganasan, Selkup, Mansi; according to raw transcription file
                   'ă':'ɑ̆', #Khanty; change vowel quality and change to correct extra short IPA diacritic; also according to raw transcription file
                   'ä':'æ', #Selkup, Khanty, Votic, Ingrian, Erzya; all according to their transcriptions in raw data file
                   'ǟ':'æː', #Ingrian, according to raw transcription file
                   'å':'ɒ', #Mansi, according to raw transcription file
                   'ē':'eː', #Mansi, Selkup, Votic; according to raw transcription file
                   'ī':'iː', #Mansi, Selkup, Ingrian; all according to their transcriptions in raw data file
                   'ō':'oː', #Mansi, Selkup; according to raw transcription file
                   'ö':'ø', #Khanty, Votic, Meadow Mari; all according to their transcriptions in raw data file
                   'ȫ':'øː', #Ingrian, according to raw transcription file
                   'ū':'uː', #Selkup, Mansi, Ingrian, Votic, Nganasan; according to raw transcriptions
                   'ü':'y', #Meadow Mari, Ingrian, Votic, Nganasan; all according to their transcriptions in raw data file
                   'ǖ':'yː', #Selkup, according to raw transcription file
                   
                   #Other characters
                   '_':' ', #marks word boundary instead of space; change to space
                   '̄':'ː', #marks long segment, change to proper IPA symbol
                   '̀':'ˑ', #Votic; raw transcription file shows that this corresponds to half-long symbol
                   '̭':'̆', #Khanty; not totally sure but it seems to be intended to be the extra short diacritic
                   '˳':'ʷ', #raw transcription file shows that this corresponds with /ʷ/ diacritic
                   #'-':'', #some kind of segmentation or marking of compound words, remove from transcription
                   '"':'', #quotation mark, not part of transcription
                   '\xa0':'', #unknown character, does not seem to be there intentionally [nothing in orthography, just shows up as a space]                   
    }

def has_parentheses(string):
    if ')' in string:
        return True
    elif '(' in string:
        return True
    else:
        return False

def standardize_geminates(word):
    #convert sequences of two identical segments to a long segment
    segments = segment_word(word)
    for i in range(1, len(segments)):
        if segments[i] == segments[i-1]:
            segments[i] = 'ː'
    word = ''.join(segments)
    return word
    

def fix_tr(word, lang):
    #use conversion dict to convert individual segments
    word = ''.join([conversion_dict.get(ch, ch) for ch in word])

    
    if lang not in ['Hungarian', 'Kildin Saami']:
        #seems to be [ɑ] in all languages except for these; 
        #occasionally mistranscribed as [a] in Estonian, so change this back to [ɑ] there too
        word = re.sub('a', 'ɑ', word) 
    
    #needs to precede reg exp conversions in order to escape changing <ḱ> --> <c> --> <ʦ>
    if lang not in ['Hungarian']:#, 'Votic']: #why was Votic previously excluded? seems to need this conversion too
        word = re.sub('c', 'ʦ', word)
    
    #Hungarian transcriptions of <r> use both tap /ɾ/ and trill /r/, change all to trills (Szende, 1994)
    #<rr> is transcribed as geminate /rː/, so that's not the issue
    if lang == 'Hungarian':
        word = re.sub('ɾ', 'r', word) 
        
        #One word, 'fiúunoka', /fiʲuːunokɒ/ uses segment /iʲ/ -- change to /ij/
        word = re.sub('iʲ', 'ij', word)

    #reg exp conversions
    word = re.sub('dʹ', 'dʲ', word) #Nganasan, Erzya; according to their raw file transcriptions
    word = re.sub('tʹ', 'tʲ', word) #Erzya, Khanty, Komi-Zyrian; according to their raw file transcriptions
    word = re.sub('lʹ', 'ʎ', word) #Mansi, Erzya, Votic, Khanty, Nganasan; according to their raw file transcriptions
    word = re.sub('ṇ', 'ɳ', word) #Khanty; according to raw transcription
    word = re.sub('ḱ', 'c', word) #Erzya; according to raw transcription
    word = re.sub('ʒ́', 'ʥ', word) #Udmurt, Komi-Zyrian, Komi-Permyak; according to raw transcription
    word = re.sub('ŏ', 'ŏ', word) #Khanty; changes to correct extra short IPA diacritic
    word = re.sub('ə̑', 'ə̠', word) #Meadow Mari, Selkup; according to raw transcription file
    word = re.sub('e̮', 'ɤ', word) #Komi-Zyrian, Komi-Permyak, Selkup, Votic; according to raw transcription file
    word = re.sub('i̮', 'ɯ', word) #Komi-Zyrian, Komi-Permyak, Udmurt, Nganasan, Selkup, Khanty; all according to raw data file
    word = re.sub('ĭ', 'i̯', word) #Ingrian; meant to be non-syllabic diacritic
    word = re.sub('tʃ', 'ʧ', word) #change to a single affricate symbol
    word = re.sub('t͡ʃ', 'ʧ', word) #change to a single affricate symbol
    word = re.sub('dʒ', 'ʤ', word) #change to a single affricate symbol
    word = re.sub('ts', 'ʦ', word) #change to a single affricate symbol
    word = re.sub('t͡s', 'ʦ', word) #change to a single affricate symbol
    word = re.sub('dz', 'ʣ', word) #change to a single affricate symbol
    word = re.sub('ːʲ', 'ʲː', word) #reverse ordering of length and palatalizing symbols
    
    #convert double vowels to long vowels; but not consonants
    #(some sequences of non-identical in some Uralic languages correspond with sequences of identical consonants in others, cf. Italian)
    word = standardize_geminates(word)
    
    #correct any double long symbols
    word = re.sub('ːː', 'ː', word)
    
    #after converting double consonants, remove '-' segmentation 
    #(otherwise e.g. Mansi /lɑp-pɑnti/ would become /lɑpːɑnti/ instead of /lɑppɑnti/)
    #probably irrelevant if we don't convert consonants, see above note
    word = re.sub('-', '', word)
    
    #remove parenthetical annotations/alternatives
    while has_parentheses(word) == True:
        word = re.sub(r'\([^()]*\)', '', word)
    
    return word

def transcribe_voro(word):
    """Grapheme-to-phoneme transcription tool for the Võro language
    #Based on: https://www.omniglot.com/writing/voro.htm
    #https://en.wikipedia.org/wiki/V%C3%B5ro_language#Orthography
    #https://www.thefreelibrary.com/Grade+alternation+in+Voro+South+Estonian.-a0243043467
    https://eurphon.info/languages/html?lang_id=285
    """
    voro_ipa_dict = {'a':'ɑ',
                'b':'p',
                'c':'ʦ',
                'd':'t',
                'e':'e',
                'f':'f',
                'g':'k',
                'h':'h',
                'i':'i',
                'j':'j',
                'k':'kˑ',
                'l':'l',
                'm':'m',
                'n':'n',
                'o':'o',
                'p':'pˑ',
                'q':'ʔ',
                'r':'r',
                's':'sˑ',
                't':'tˑ',
                'u':'u',
                'v':'v',
                'w':'v',
                'x':'ks',
                'y':'ɨ',
                'z':'s',
                'ä':'æ',
                'õ':'ɤ',
                'ö':'ø',
                'ü':'y',
                'š':'ʃˑ',
                'ž':'ʃ',
                '’':'ʲ',
                "'":"ʲ"}
    #Note: transcription in UraLex seems not to use <c, w, x, y, z>
    #<ts> --> /ʦ/ rather than <c>
    
    
    #First convert two-character sequences
    tr = re.sub('ng', 'ŋ', word) #phoneme according to Wikipedia description
    tr = re.sub('ts', 'ʦ', word)
    
    #Then convert all single characters
    tr = [voro_ipa_dict.get(ch, ch) for ch in tr]
    
    #Convert sequences of two identical vowels to a long vowel
    voro_vowels = ['ɑ', 'e', 'i', 'o', 'u', 'ɨ', 'æ', 'ɤ', 'ø', 'y']
    if len(tr) > 1:
        for i in range(1, len(tr)):
            ch = tr[i]
            if ch in voro_vowels:
                prev_ch = tr[i-1]
                if prev_ch == ch:
                    tr[i] = 'ː'
    tr = ''.join(tr)
    
    #Then fix doubles letters / Q3 (quantity 3)
    #single <p, t, k, s> represent Q2 (quantity 2), transcribed as half-long /pˑ, tˑ, kˑ, sˑ/
    #double <pp, tt, kk, ss> represent overlong (Q3) consonants (Iva, 2010)
    #they will be mistakenly be written as sequences of two half-long consonants,
    #so change these to Q3, transcribed as fully-long consonants
    tr = re.sub('pˑpˑ', 'pː', tr)
    tr = re.sub('tˑtˑ', 'tː', tr)
    tr = re.sub('kˑkˑ', 'kː', tr)
    tr = re.sub('sˑsˑ', 'sː', tr)
    
    #Change ordering of palatalization and length marking
    tr = re.sub('ˑʲ', 'ʲˑ', tr)
    tr = re.sub('ːʲ', 'ʲː', tr)
    
    return tr

#%%
#PREPROCESS URALEX DATA TRANSCRIPTION

print('Preprocessing data from UraLex dataset...')
#list of corrected transcriptions which don't match the raw transcription file
mismatched = []

cognate_sets = defaultdict(lambda:[])
uralic_data = defaultdict(lambda:{})
missing_transcriptions = defaultdict(lambda:[])
for i in forms_data:
    entry = forms_data[i]
    
    #remove spurious quotation marks from all fields
    for field in entry:
        entry[field] = strip_ch(entry[field], ['"'])
    globals().update(entry)
    
    #skip entries with these values
    if Value not in {'[Form not found]', '[No equivalent]', '[Not reconstructable]'}:
        lang_name, glottocode, iso_code = lang_data[uralic_ids[Language_ID]]
        if type(glottocode) == float: #nan
            glottocode = ''
        if type(iso_code) == float: #nan
            iso_code = ''
        concepticon_gloss = concept_dict[Parameter_ID]
        base_concept = base_concepts[concepticon_gloss]
        cognacy_ID = cognate_dict[ID]
        cognate_sets[base_concept].append(cognacy_ID)
        
        tr = item_IPA.strip()
        original_tr = tr[:]
        
        #if the language is Võro, use the Võro G2P on the orthography instead
        if lang_name == 'Võro':
            tr = transcribe_voro(Value)
        
        #if the IPA transcription is missing, try to find it in the raw data file
        if tr == '':
            try: 
                tr = raw_data_dict[(Language_ID, Value)].strip()
                original_tr = tr[:]
            except KeyError: #if not found, skip this entry
                missing_transcriptions[lang_name].append((i, Language_ID, Form))
                continue
        
        #fix the IPA transcription
        tr = fix_tr(tr, lang_name)
        
        #Check whether IPA value matches the transcription in the raw data
        try: 
            raw_tr = raw_data_dict[(Language_ID, Value)].strip()
            variants = raw_tr.split(', ')
            mismatch = True
            for variant in variants:
                variant = strip_ch(variant.strip(), ['-'])
                if tr == variant:
                    mismatch = False
                elif original_tr == variant:
                    mismatch = False
            if mismatch == True:
                mismatched.append([lang_name, str(i), original_tr, tr, raw_tr])
        except KeyError:
            pass
        
        #skip transcriptions which are still empty
        if tr != '':
        
            #split variants by <~> and <,>
            variant_tr = re.split('~|, ', tr)
            variant_original_tr = re.split('~|, ', original_tr)
            variant_value = re.split('~|, ', Value)
            
            #add each variant separately
            variants = zip(variant_tr, variant_original_tr, variant_value)
            for variant in variants:
                tr, original_tr, Value = variant
                tr = tr.strip()
                original_tr = original_tr.strip()
                Value = Value.strip()
                
                #remove 'etc.' annotation from Value (only found in 1 entry, i=6672)
                Value = re.sub(' etc.', '', Value)
                
                #add data to new dict
                new_entry = uralic_data[i]
                new_entry['ID'] = '_'.join([strip_ch(lang_name, [' ']), cognacy_ID])
                new_entry['Language_ID'] = lang_name
                new_entry['Glottocode'] = glottocode
                new_entry['ISO 639-3'] = iso_code
                new_entry['Parameter_ID'] = base_concept
                new_entry['Value'] = Value
                new_entry['Form'] = tr
                new_entry['Segments'] = ' '.join(segment_word(tr))
                new_entry['Source_Form'] = original_tr
                new_entry['Cognate_ID'] = '_'.join([base_concept, cognacy_ID])
                if ID in loan_list:
                    new_entry['Loan'] = 'TRUE' 
                else:
                    new_entry['Loan'] = 'FALSE'
                new_entry['Comment'] = Comment
                new_entry['Source'] = 'De Heer et al.; Syrjänen'

#%%
#COUNT NUMBERS OF INCLUDED WORD FORMS THUS FAR
words = defaultdict(lambda:[])

for i in uralic_data:
    entry = uralic_data[i]
    lang = entry['Language_ID']
    words[lang].append(entry['Form']) 

uralic_langs = [item[0] for item in lang_data.values()]
wordcounts = [(lang, len(words[lang])) for lang in uralic_langs]
wordcounts.sort(key=lambda x: x[1], reverse=True)
lang_no_tr = defaultdict(lambda:[])
for item in wordcounts:
    lang_name, count = item
    if count == 0:
        for i in forms_data:
            entry = forms_data[i]
            for field in entry:
                entry[field] = strip_ch(entry[field], ['"'])
            globals().update(entry)
            name, glottocode, iso_code = lang_data[uralic_ids[Language_ID]]
            if name == lang_name:
                lang_no_tr[lang_name].append(i)

#%%
#MAP MISSING TRANSCRIPTIONS TO NORTHEURALEX FOR LANGUAGES WITH 0 TRANSCRIPTIONS
#AND DIRECT EQUIVALENTS IN NORTHEURALEX DATASET
print('\nLoading preprocessed NorthEuraLex data...')

path_to_NEL = 'uralic_NEL_data.csv'
NEL_data = csv_to_dict(path_to_NEL, sep='\t')
uralex_NEL_mapping = {'South Saami':'Southern Sami', 
                      #'Ume Saami', 
                      #'Pite Saami', 
                      'North Saami':'Northern Sami', 
                      #'Inari Saami':'', 
                      'Skolt Saami':'Skolt Sami', 
                      'Karelian':'North Karelian', 
                      'Veps':'Veps', 
                      'Livonian':'Livonian', 
                      'Tundra Nenets':'Tundra Nenets'}

not_included = []
included = []
NEL_data_dict = defaultdict(lambda:[])
for i in NEL_data:
    if NEL_data[i]['Language_ID'] in uralex_NEL_mapping.values():
        lang_id = NEL_data[i]['Language_ID']
        gloss = NEL_data[i]['Parameter_ID']
        base_concept = base_concepts[gloss]
        value = NEL_data[i]['Value']
        form = NEL_data[i]['Form']
        source_form = NEL_data[i]['Source_Form']
        NEL_data_dict[(lang_id, base_concept)].append((value, form, source_form))
        included.append(lang_id)
    else:
        not_included.append(NEL_data[i]['Language_ID'])

#%%    
print('Searching for equivalent word entries between UraLex and NorthEuraLex...')
found_in_NEL = defaultdict(lambda:[])  
not_found_in_NEL = defaultdict(lambda:[])                                               
note = 'Word form and IPA transcription taken from NorthEuraLex, cognate set and borrowing data taken from UraLex 2.0'
for uralex_lang in uralex_NEL_mapping:
    NEL_lang = uralex_NEL_mapping[uralex_lang]
    for i in lang_no_tr[uralex_lang]:
        entry = forms_data[i]
        #remove spurious quotation marks from all fields
        for field in entry:
            entry[field] = strip_ch(entry[field], ['"'])
        globals().update(entry)
        
        #skip entries with these values
        if Value not in {'[Form not found]', '[No equivalent]', '[Not reconstructable]'}:
            lang_name, glottocode, iso_code = lang_data[uralic_ids[Language_ID]]
            if type(glottocode) == float: #nan
                glottocode = ''
            if type(iso_code) == float: #nan
                iso_code = ''
            concepticon_gloss = concept_dict[Parameter_ID]
            base_concept = base_concepts[concepticon_gloss]
            cognacy_ID = cognate_dict[ID]
            cognate_sets[base_concept].append(cognacy_ID)
            found = False
            #NEL_data_dict is a default dict, no need for try/except KeyError
            NEL_entries = NEL_data_dict[(NEL_lang, base_concept)]
            for NEL_entry in NEL_entries:
                if ((Value in NEL_entry) or (Form in NEL_entry)):
                    found = NEL_entry
                    break
                    
                elif ((fix_tr(Value, lang_name) in NEL_entry) or (fix_tr(Form, lang_name) in NEL_entry)):
                    found = NEL_entry
                    break

            if found != False:
                NEL_value, NEL_form, NEL_source_form = found
                NEL_fix_dict = {'tʦ':'ʦː',
                        'dʣ':'ʣː',
                        'tʧ':'ʧː',
                        'dʤ':'ʤː',
                        'cc͡ç':'c͡çː',
                        'ɟɟ͡ʝ':'ɟ͡ʝː',
                        'd͡s':'ʣ'}
                for to_fix in NEL_fix_dict:
                    NEL_form = re.sub(to_fix, NEL_fix_dict[to_fix], NEL_form)
                #and two more fixes which MUST follow 
                NEL_form = re.sub('ːʲ', 'ʲː', NEL_form)
                NEL_form = standardize_geminates(NEL_form)
                
                new_entry = uralic_data[i]
                new_entry['ID'] = '_'.join([strip_ch(lang_name, [' ']), cognacy_ID])
                new_entry['Language_ID'] = lang_name
                new_entry['Glottocode'] = glottocode
                new_entry['ISO 639-3'] = iso_code
                new_entry['Parameter_ID'] = base_concept
                new_entry['Value'] = NEL_value
                new_entry['Form'] = NEL_form
                new_entry['Segments'] = ' '.join(segment_word(NEL_form))
                new_entry['Source_Form'] = NEL_source_form
                new_entry['Cognate_ID'] = '_'.join([base_concept, cognacy_ID])
                if ID in loan_list:
                    new_entry['Loan'] = 'TRUE' 
                else:
                    new_entry['Loan'] = 'FALSE'
                if Comment.strip() != '':
                    new_entry['Comment'] = '; '.join([Comment, note])
                else:
                    new_entry['Comment'] = note
                new_entry['Source'] = 'Dellert et al., 2019; De Heer et al.; Syrjänen'                    
                found_in_NEL[lang_name].append((forms_data[i], found))
            else:
                for NEL_entry in NEL_entries:
                    value, form, source_form = NEL_entry
                    not_found_in_NEL[lang_name].append((i, lang_name,
                                                        forms_data[i]['Form'], 
                                                        forms_data[i]['Value'],
                                                        form, value, source_form))

#%%
#IMPORT MANUALLY ANNOTATED 
#IF ANNOTATED FILE IS FOUND, WRITE CSV FILE TO BE ANNOTATED
print('Importing manually matched word forms between UraLex and NorthEuraLex...')
annotated_file = 'Missing Transcriptions with NEL Equivalents_annotated.csv'

try:
    NEL_equivalents = csv_to_dict(annotated_file, sep='\t')

except FileNotFoundError:
    from nltk import edit_distance
    def nz_lev_dist(str1, str2):
        """Calculates the length-normalized Levenshtein distance between two strings"""
        return edit_distance(str1, str2)/max(len(str1), len(str2))
    
    #Write possible matches between UraLex and NorthEuraLex to csv file
    with open('Missing Transcriptions with NEL Equivalents.csv', 'w') as f:
        f.write('\t'.join(['UraLex_Index', 'Language', 
                           'UraLex_Form', 'UraLex_Value', 
                           'NEL_Form', 'NEL_Value', 'NEL_Source_Form',
                           'LevenshteinDist']))
        f.write('\n')
        for lang in not_found_in_NEL:
            not_found_list = set(not_found_in_NEL[lang])
            for item in not_found_list:
                i, lang, uralex_form, uralex_value, nel_form, nel_value, nel_source_form = item
                ld = min(nz_lev_dist(uralex_form, nel_form), nz_lev_dist(uralex_form, nel_value))
                f.write('\t'.join([str(i) for i in item]+[str(ld)]))
                f.write('\n')
    
    print(f'Error: no annotated file "{annotated_file}" found.\nManual annotation of accepted word pair equivalencies is required before proceeding.')
    raise FileNotFoundError

#Inspect the imported matches, fix transcriptions, sort out duplicate entries
NEL_equivalent_dict = defaultdict(lambda:defaultdict(lambda:[]))
imported_counts = defaultdict(lambda:0)
imported_LevDists = defaultdict(lambda:[])
index_dict = {}
for i in NEL_equivalents:
    entry = NEL_equivalents[i]
    acceptance = entry['Accepted?'].strip() != ''
    if acceptance == True:
        lang = entry['Language']
        UraLex_index = int(entry['UraLex_Index'])
        NEL_form = entry['NEL_Form']
        #fix some things in the NEL transcription
        NEL_fix_dict = {'tʦ':'ʦː',
                        'dʣ':'ʣː',
                        'tʧ':'ʧː',
                        'dʤ':'ʤː',
                        'cc͡ç':'c͡çː',
                        'ɟɟ͡ʝ':'ɟ͡ʝː'}
        for to_fix in NEL_fix_dict:
            NEL_form = re.sub(to_fix, NEL_fix_dict[to_fix], NEL_form)
        #and two more fixes which MUST follow
        NEL_form = re.sub('ːʲ', 'ʲː', NEL_form)
        NEL_form = standardize_geminates(NEL_form)
        
        NEL_equivalents[i]['NEL_Form'] = NEL_form
        
        NEL_value = entry['NEL_Value']
        NEL_source = entry['NEL_Source_Form']
        UraLex_entry = forms_data[UraLex_index]        
        concepticon_gloss = concept_dict[UraLex_entry['Parameter_ID']]
        cognacy_ID = cognate_dict[UraLex_entry['ID']]
        if (NEL_value, NEL_form, NEL_source) not in NEL_equivalent_dict[lang][(concepticon_gloss, cognacy_ID)]:
            NEL_equivalent_dict[lang][(concepticon_gloss, cognacy_ID)].append((NEL_value,
                                                                               NEL_form,
                                                                               NEL_source))
            LevDist = float(entry['LevenshteinDist'])
            imported_LevDists[lang].append(LevDist)
            imported_counts[lang] += 1
            index_dict[i] = UraLex_index
print('\n')
print(' | '.join(['Language', 'Automatic Matches', 'Manual Matches', 
                   'Total Matches', 'Mean LevDist']))
for lang in imported_counts:
    auto_matches = len(found_in_NEL[lang])
    manual_matches = imported_counts[lang]
    total_matches = auto_matches + manual_matches
    mean_lev_dist = sum(imported_LevDists[lang]) / len(imported_LevDists[lang])
    print(' | '.join([str(i) for i in [lang, auto_matches, manual_matches, total_matches,
                       round(mean_lev_dist, 2)]]))
print('\n')

#%%
#COMBINE MANUALLY MATCHED WORD FORMS WITH URALEX DATA

print('Combining NorthEuraLex and UraLex data...')
for j in index_dict:
    uralex_index = index_dict[j]
    uralex_entry = forms_data[uralex_index]
    new_entry = uralic_data[uralex_index]
    imported_entry = NEL_equivalents[j]
    lang_id = uralex_entry['Language_ID']
    lang_name, glottocode, iso_code = lang_data[uralic_ids[lang_id]]
    cognacy_ID = cognate_dict[uralex_entry['ID']]
    concepticon_gloss = concept_dict[uralex_entry['Parameter_ID']]
    base_concept = base_concepts[concepticon_gloss]
    cognate_sets[base_concept].append(cognacy_ID)
    NEL_value = imported_entry['NEL_Value']
    NEL_form = imported_entry['NEL_Form']
    NEL_source = imported_entry['NEL_Source_Form']
    comment = uralex_entry['Comment']
    
    new_entry['ID'] = '_'.join([strip_ch(lang_name, [' ']), cognacy_ID])
    new_entry['Language_ID'] = lang_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code
    new_entry['Parameter_ID'] = base_concept
    new_entry['Value'] = NEL_value
    new_entry['Form'] = NEL_form
    new_entry['Segments'] = ' '.join(segment_word(NEL_form))
    new_entry['Source_Form'] = NEL_source
    new_entry['Cognate_ID'] = '_'.join([base_concept, cognacy_ID])
    if uralex_entry['ID'] in loan_list:
        new_entry['Loan'] = 'TRUE' 
    else:
        new_entry['Loan'] = 'FALSE'
    if comment.strip() != '':
        new_entry['Comment'] = '; '.join([Comment, note])
    else:
        new_entry['Comment'] = note 
    new_entry['Source'] = 'Dellert et al., 2019; De Heer et al.; Syrjänen'  

#%%
#RENAME COGNATE SETS
print('Renaming cognate sets...')
for i in cognate_sets:
    cognate_sets[i] = list(set(cognate_sets[i]))

new_cognate_sets = {}
for concept in cognate_sets:
    for i in range(len(cognate_sets[concept])):
        old_id = concept + '_' + cognate_sets[concept][i]
        new_id = concept + '_' + str(i+1)
        new_cognate_sets[old_id] = new_id
        
for i in uralic_data:
    uralic_data[i]['Cognate_ID'] = new_cognate_sets[uralic_data[i]['Cognate_ID']]

#%%
#ISOLATE UNKNOWN CHARACTERS IN TRANSCRIPTIONS
print('')
all_new_chs = [ch for i in uralic_data  
               for ch in uralic_data[i]['Segments'] 
               if ch not in all_sounds + diacritics + [' ', 'ˑ', '̠', '̆']]

new_chs = list(set(all_new_chs))
new_chs.sort(key= lambda x: all_new_chs.count(x), reverse=True)


def lookup_segment(segment, langs=None):
    if langs == None:
        langs = set(uralic_data[i]['Language_ID'] for i in uralic_data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in uralic_data:
        entry = uralic_data[i]
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
#RECOUNT WORD FORMS ONCE AGAIN
print('Counting word forms...')
words = defaultdict(lambda:[])

for i in uralic_data:
    entry = uralic_data[i]
    lang = entry['Language_ID']
    words[lang].append(entry['Form']) 

uralic_langs = [item[0] for item in lang_data.values()]
wordcounts = [(lang, len(words[lang])) for lang in uralic_langs]
wordcounts.sort(key=lambda x: x[1], reverse=True)
lang_no_tr = defaultdict(lambda:[])
for item in wordcounts:
    lang_name, count = item
    if count == 0:
        for i in forms_data:
            entry = forms_data[i]
            for field in entry:
                entry[field] = strip_ch(entry[field], ['"'])
            globals().update(entry)
            name, glottocode, iso_code = lang_data[uralic_ids[Language_ID]]
            if name == lang_name:
                lang_no_tr[lang_name].append(i)
for item in wordcounts:
    lang, count = item
    if count != 1:
        print(f'{lang}: {count} forms')
    else:
        print(f'{lang}: {count} form')
print('\n')
                
#%%
#CHECK MISMATCHES
def is_ipa(word):
    for ch in word:
        if ch not in set(all_sounds + diacritics + [' ', 'ˑ', '̠', '̆']):
            return False
    return True

print('Checking for non-recognized (non-IPA) characters...')
not_ipa = {lang:[word for word in words[lang] if is_ipa(word) == False] for lang in uralic_langs}
ipa_issues = 0
for lang in not_ipa:
    not_ipa_len = len(not_ipa[lang])
    if not_ipa_len > 0:
        ipa_issues += not_ipa_len
        print(f'{not_ipa_len} words found in {lang} with non-IPA characters!')
if ipa_issues == 0:
    print('No problems found.')
print('\n')

if len(mismatched) > 0:
    mismatched.sort(key=lambda x: x[0])
    print('Words whose transcription do not match the raw transcription IPA file:')
    print('LANGUAGE | INDEX (forms_data) | ORIGINAL | FIXED | RAW')
    for item in mismatched:
        print(' | '.join(item))
print('\n')
        
#%%
output_file = 'uralic_data.csv'
print(f'Writing preprocessed Uralic data to "{output_file}"...')

def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            try:
                values = sep.join([str(data_dict[i][feature]) for feature in features])
            except TypeError:
                print(i, data_dict[i])
            f.write(f'{values}\n')
            
write_data(uralic_data, output_file=output_file)
        