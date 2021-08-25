import os, re
from collections import defaultdict
import pandas as pd
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

#LOAD NEL DATA ABOUT LANGUAGES INCLUDED IN DATASET
language_data = csv_to_dict('Source/northeuralex-0.9-language-data.tsv', sep='\t')

#Families and subfamilies of included languages
NEL_families = set([language_data[i]['family'] for i in language_data])
NEL_subfamilies = set([f"{language_data[i]['family']}, {language_data[i]['subfamily']}" for i in language_data])


#LOAD DATA ABOUT CONCEPTS IN DATASET
concept_data = csv_to_dict('Source/northeuralex-0.9-concept-data.tsv', sep='\t')

#Take Concepticon gloss, unless there isn't one, in which case the proposed Concepticon gloss
#If that also doesn't exist, take the NELEX ID
#Update: only take words with concepticon glosses
concept_IDs = {}
excluded_concepts = []
for i in concept_data:
    entry = concept_data[i]
    id_nelex = entry['id_nelex']
    concepticon = entry['concepticon']
    if concepticon == '<NA>':
    #    concepticon = entry['concepticon_proposed']
        excluded_concepts.append(entry['concepticon_proposed'])
    elif concepticon != '<NA>':    
        concept_IDs[id_nelex] = concepticon
    else:
    #    concept_IDs[id_nelex] = id_nelex
        excluded_concepts.append(id_nelex)

#Load lists of concepts: only extract concepts from these lists, in order to reduce manual annotation
#Load Swadesh lists
swadesh_215 = pd.read_csv(str(parent_dir) + '/Concepts/Concept_list_Swadesh_1950_215.csv', sep='\t')
swadesh_100 = pd.read_csv(str(parent_dir) + '/Concepts/Concept_list_Swadesh_1955_100.csv', sep='\t')
swadesh = set(list(swadesh_215.Parameter) + list(swadesh_100.Parameter))

#Load mappings of differing labels for the same concept group
all_concepts = pd.read_csv(str(parent_dir) + '/Concepts/concepts.csv', sep='\t')
base_concepts = {list(all_concepts.Concept)[i]:list(all_concepts.BaseConcept)[i] 
                 for i in range(len(all_concepts))}

#Load common concepts list
common_concepts_data = pd.read_csv(str(parent_dir) + '/Concepts/common_concepts.csv', sep='\t')
common_concepts = list(common_concepts_data.Concept)
for i in range(len(common_concepts_data)):
    alternates = list(common_concepts_data.Alternate_Labels)[i].split('; ')
    common_concepts.extend(alternates)
common_concepts = set(common_concepts)

#Get set of all allowed meanings
concepts_to_extract = set(list(swadesh) + list(common_concepts))


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
            source_name = lang_data['Source Name'][i]
            balto_slavic_langs.extend([lang, source_name])
        elif 'Uralic' in classification:
            lang = lang_data['Name'][i]
            uralic_langs.append(lang)
balto_slavic_langs = set(balto_slavic_langs)
uralic_langs = set(uralic_langs)

lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'NorthEuraLex'}

#%%
#LOAD WORD FORM DATA
forms_data = csv_to_dict('Source/northeuralex-0.9-forms.tsv', sep='\t')



#%%
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

def adjust_stress(word):
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

def standardize_affricates(word):
    #equivalent affricate representations, latter versions are cleaner to read
    affricate_conversion = {'t͡s':'ʦ', 'd͡z':'ʣ', 't͡ʃ':'ʧ', 'd͡ʒ':'ʤ', 't͡ɕ':'ʨ', 'd͡ʑ':'ʥ'}
    for affricate in affricate_conversion:
        word = re.sub(affricate, affricate_conversion[affricate], word)
    return word

def fix_transcription(word):
    #remove spaces and secondary stress marking from words
    word = ''.join([conversion_dict.get(ch, ch) for ch in word if ch not in [' ', 'ˌ']])
    
    #Adjust position of stress marking
    word = adjust_stress(word)
    
    #Standardize affricates
    word = standardize_affricates(word)

    return word


#%%
#LOAD TOOLS FOR CORRECTING TRANSCRIPTIONS

#Load automatic G2P transcription tools
os.chdir(str(grandparent_dir) + '/Code/Automatic_Transcription/')
from transcribe_czech import *
from transcribe_slovak import *
from transcribe_polish import *
from transcribe_ukrainian import *
from transcribe_belarusian import *
from transcribe_bulgarian import *
os.chdir(local_dir)


def correct_ru(tr):
    """Adjusts the transcription from Russian Wiktionary"""
    
    #Remove parentheses and any unintentional characters from Excel sheet
    tr = strip_ch(tr, ['(', ')', '\ufeff'])
    
    #Correct position of stress
    tr = adjust_stress(tr)
    
    #Adjust transcription of affricates
    tr = standardize_affricates(tr)
    
    #Change /ɕː/ --> /ɕɕ/
    #tr = re.sub('ɕː', 'ɕɕ', tr) 
    #decision: don't do this, as this is actually a separate phoneme in modern Russian
    
    #Change /ʦː/ (<-ться>, <двадцать>) to /tʦ/ and /nː/ to /nn/
    tr = re.sub('ʦː', 'tʦ', tr)
    tr = re.sub('nː', 'nn', tr)
    
    #Change /j/ in diphthongs <ый>, <ий>, and <ой> to /ɪ̯/ when appearing word-finally
    tr = re.sub('ɪj$', 'ɪɪ̯', tr)
    tr = re.sub('ɨj$', 'ɨɪ̯', tr)
    tr = re.sub('oj$', 'oɪ̯', tr)
    
    return tr

#%%
#Load BE, BG, RU, UK word forms annotated with stress, and transcriptions in RU
stress_annotation_data = csv_to_dict(str(parent_dir) + '/Balto-Slavic/Source/stress_annotations_be_bg_ru_uk.csv', sep=',')
stress_annotations = defaultdict(lambda:{})
bulgarian_verbs = []
for i in stress_annotation_data:
    entry = stress_annotation_data[i]
    lang = entry['Language']
    orth = entry['Orthography']
    stress_anno = entry['StressAnnotation']
    correct_word = entry['CorrectWord']
    
    #For Russian, import the form with annotated stress and the transcribed form
    if lang == 'Russian':
        tr = entry['Transcription']
        if correct_word.strip() == '':
            stress_annotations[lang][orth] = (stress_anno, correct_ru(tr))
        else:
            stress_annotations[lang][orth] = (correct_word, correct_ru(tr))
    
    #Mark the verbs in Bulgarian to change the final vowels
    if lang == 'Bulgarian':
        bg_verb_anno = entry['BG_Verb']
        if bg_verb_anno != '':
            bulgarian_verbs.append(orth)
    
    if lang != 'Russian': #don't do this for Russian, as it would override was was done a few lines earlier
        #If there is no corrected word, take the stress-annotated word
        if correct_word.strip() == '':
            stress_annotations[lang][orth] = (stress_anno, '')
            
        #If there is a corrected version of the word, take instead the corrected
        #word and mark that it has been corrected
        else:
            stress_annotations[lang][orth] = (correct_word, '*')
    





#%%
problems = []
missing = []
for i in forms_data:
    entry = forms_data[i]
    lang = glottocodes[entry['Glottocode']]
    
    #Only extract data for Balto-Slavic and Uralic languages
    if lang in list(balto_slavic_langs)+list(uralic_langs):
    
        try:
            new_name, glottocode, iso_code = lang_data[lang] 
        except KeyError:
            missing.append((lang, entry['Glottocode']))
            new_name, glottocode, iso_code = '', '', ''
        
        #Only extract data for Swadesh 215 list items for Balto-Slavic in order to facilitate manual annotations
        #No such restriction for Uralic as the manual cognate set annotation is not necessary
        #Ignore concepts without a concepticon ID
        gloss = concept_IDs.get(entry['Concept_ID'], None)
        if gloss == None:
            continue
        gloss = re.sub('_', ' ', gloss)
        
        #Convert gloss to base concept: change to base concept for Slavic languages only
        base_concept = base_concepts[gloss]
        if lang in balto_slavic_langs:
            gloss = base_concept
        
        if (((lang in balto_slavic_langs) and ((gloss in concepts_to_extract) or (base_concept in concepts_to_extract))) or (lang in uralic_langs)):
            orth = entry['Word_Form']
            source_orth = entry['Word_Form']
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
     
                  
                #CORRECTIONS IN SLAVIC LANGUAGES
                elif lang == 'Russian':
                    if orth in ['наполненный', 'пожилой', 'затылок', 'волос',
                                'коготь', 'кушать']:
                        #skip "наполненный", better equivalent "полный" already in list
                        #skip "пожилой", because "старый" is already included
                        #skip "затылок", because "шея" is already included
                        #skip "волос", because more usual plural form "волосы" is already included
                        #skip "коготь", because "ноготь" is already included
                        #skip "кушать", because "есть" is already included
                        continue
                    
                    stress_anno = stress_annotations['Russian'][orth]
                    stress_anno, tr = stress_anno
                    #The transcription will already have been fixed when imported
                    #In case the original orthography was modified, use this
                    orth = strip_ch(stress_anno, ['́']) #remove stress mark
                    
                    
                elif lang == 'Bulgarian':
                    if orth in ['китка', 'тояга', 'изгоря', 'почва', 'фин',
                                'пътека', 'древен', 'тил', 'умъртвя', 'косъм',
                                'нога', 'хвърча', 'сражение']: #skip these translations
                    #skip "китка", not correct translation for HAND; use already present "ръка" instead
                    #skip "тояга", although valid translation, it is a Turkic loanword and a better translation "прът" is already listed
                    #skip "изгоря", because "горя" is already included
                    #skip "почва", because "земя" is already included
                    #skip "фин", because better translation "тънък" is already included
                    #skip "пътека", because "път" is already included
                    #skip "древен", because "стар" is already included
                    #skip "тил", because "врат" is already included
                    #skip "умъртвя", because "убия" is already included
                    #skip "косъм", because "коса" is already included
                    #skip 'нога' -- outdated/dialectal, and 'крак' is included already
                    #skip "хвърча", because "летя" is already included
                    #skip "сражение", FIGHT as noun rather than verb; verb already included (via correction)
                        continue
                    
                    #Check whether the word is a verb
                    is_verb = orth in bulgarian_verbs
                    
                    #Then extract the stress-annotated orthography
                    stress_orth = stress_annotations['Bulgarian'][orth]
                    stress_orth, note = stress_orth
                    
                    
                    #Check whether the orthography was modified, if so take the new orthography
                    if note != '': 
                        orth = strip_ch(stress_orth, ['́']) #remove stress mark                        
                    
                    #Automatically transcribe
                    tr = transcribe_bg(stress_orth)
                    
                    #Correct the final vowel in verbs stressed on final syllable
                    #/a/ --> /ɤ/
                    if is_verb == True:
                        words = tr.split() #need to split into words because of entries like <боя́ се>
                        for k in range(len(words)):
                            word = words[k]
                            word = list(word)
                            if word[-1] == 'a': #if unstressed it would have been reduced to [ɐ], and monosyllabic verbs won't have stress marked
                                word[-1] = 'ɤ'
                            words[k] = ''.join(word)
                        tr = ' '.join(words)
                    
                    
                elif lang == 'Croatian':
                    if orth in ['uski', 'put', 'pseto', 'bio', 'bridak', 'guja', 
                                'sagorjeti', 'spaliti', 'papak', 'fin',
                                'zatiljak', 'daljnji', 'nečist', 'kopkati']: 
                        #skip "uski", because "uzak" (same lemma) is already included for "NARROW"
                        #skip "put", not a correct translation for "SKIN"
                        #skip "papak", not a correct translation for "CLAW" (means HOOF)
                        #skip "pseto", not a correct translation of "DOG" (means "dog" in the sense of a detestable person)
                        #skip "bio", this is not the standard Ijekavian form for WHITE ("bijel" is correct)
                        #skip "bridak", more general translation for SHARP oštar is already in list and bridak doesn't have any cognate equivalents in other languages
                        #skip "guja", more general translation for SNAKE is zmija, which is already in list (guja is literary)
                        #skip "sagorjeti" and "spaliti", because "gorjeti" is already included
                        #skip "papak", intended to be "kandža" for CLAW but confused somehow with FINGERNAIL in glossing...just skip
                        #skip "fin", because better translation 'tanak' is already included
                        #skip "zatiljak", because "vrat" is already included
                        #skip "daljnji", not quite right meaning of FAR; "dalek(o)" is already included
                        #skip "nečist", because it really means IMPURE and also "prljav" is already included (after replacement)
                        #skip "kopkati", because "kopati" is already present
                        continue
                    
                    #Standard (Serbo-)Croatian has /e, o/, not /ɛ, ɔ/
                    tr = re.sub('ɛ', 'e', tr)
                    tr = re.sub('ɔ', 'o', tr)
                    
        
                    #<ije> is not /ije/ or /ie/, but /jeː/ -- it is the long version of <je>
                    #(i.e., the orthographic <i> is present only to mark the length)
                    #Several steps required to fix this
                    
                    #Step 1: fix /ije/ without tone marking
                    tr = re.sub('ije', 'jeː', tr)
                    
                    #Step 2: fix /ije/ with tone marking
                    #Some mistakenly have a pitch accent on the <i> instead of on the <e>
                    tones = re.compile(r'̂|̌') #rising and falling tone diacritics
                    ije_tones = re.compile(r'i[̂|̌]je') 
                    if ije_tones.search(tr):
                        #Distinguish between <iTONEje> within and at the end of a word (e.g. <prije>)
                        #Don't change anything if this sequence is at the end of the word
                        ije_end = re.compile(r'i[̂|̌]je($| )')
                        if ije_end.search(tr):
                            pass
                        
                        else:
                            tone = tones.findall(tr)[0]
                            indices = [(m.start(0), m.end(0)) for m in re.finditer(ije_tones, tr)][0]
                            start, end = indices
                            new_tr = tr[:start] + 'je'
                            if tr[start+4] == 'ː':
                                new_tr += tr[start+4] + tone + tr[start+5:]
                            else:
                                new_tr += 'ː' + tone + tr[start+4:]
                            tr = new_tr
                    
                    #Step 3: fix /ie/
                    if 'ie' in tr:
                        #these two words are exceptions, the 'ije' is not of the same type
                        if orth not in ['kasnije', 'najprije']:
                            tr = re.sub('ie', 'jeː', tr)
                        else:
                            tr = re.sub('ie', 'ije', tr)
                    
                    #Step 4: Remove any accidental resulting double length markings
                    tr = re.sub('ːː', 'ː', tr)
                
                    #Simply replace some translations with better ones, and supply their transcriptions directly
                    replace_orth = {'sisa':('grudi', 'ɡrûːdi'), #grudi is the more common word, match cognate set in other languages
                                    'njedra':('prsa', 'pr̩̂sa'), #njedra is a literary word, prsa is more common, also matches cognate set in other languages
                                    'ispravan':('pravilan', 'prâʋiːlan'), #match the cognate set in other languages
                                    'tačan':('točan', 'tôʧan'), #tačan is the Serbian form, točan the Croatian form
                                    'blatan':('prljav', 'pr̩̂ʎaʋ'), #'blatan' means 'muddy', 'prljav' is proper translation for DIRTY
                                    'brdo':('planina', 'planǐna'), #'brdo' means 'hill', not 'mountain'
                                    'drum':('put', 'pûːt'), #drum is a loanword from Greek and a very uncommon word at that; replace with "put", which is more common and matches other cognate sets
                                    'ondje':('tamo', 'tâmo'), #ondje is correct, but tamo is the more general word and matches existing cognate set in data
                                    'osjećati miris':('njušiti', 'ɲûʃiti'), #use the simpler verb
                                    'sjemenje':('sjeme', 'sjême'), #sjemenje is pluralia tantum, use singular
                                    #'papak':('kandža', 'kâːnʤa') #correct translation for CLAW is kandža; papak means hoof
                                    'dalek':('daleko', 'dalěko'), #FAR as adverb, source: IE-CoR
                                    'boj':('boriti se', 'bǒriti se') #FIGHT as verb; source: IE-CoR
                                    }
                    if orth in replace_orth:
                        orth, tr = replace_orth[orth]
                
                elif lang == 'Slovene':
                    if orth == 'dúhati': #correct this one word and supply transcription directly; cognate to Polish word
                        orth = 'vọ̑hati'
                        tr = 'ʋóːxati'
                    elif orth == 'nédrja':
                        orth = 'pŕsi'
                        tr = 'pə́rsi' #reference: IE-CoR
                    elif orth == 'lúčati':  #reference: IE-CoR
                        orth = 'vréči'
                        tr = 'u̯rèːʧi'
                    elif orth == 'dejáti': #reference: IE-CoR
                        orth = 'réči'
                        tr = 'rɛ̀ːʧi'
                    elif orth == 'máma': #reference: IE-CoR
                        orth = 'máti'
                        tr = 'màːti'
                    elif orth == 'cvetlíca': #reference: IE-CoR
                        orth = 'cvȇt'
                        tr = 'ʦʋéːt'
                    elif orth == 'bòj': #FIGHT as verb, source: IE-CoR
                        orth = 'borīti se'
                        tr = 'bɔrˈiːti sɛ'
                    elif orth in ['pŕst', 'párkelj', 'nóht na rôki', 'drôben', 
                                  'zatílnik', 'maščôba', 'grêbsti', 'plákati']:
                        #skip this pŕst, because "zêmlja" is already included
                        #skip 'párkelj', wrong translation and better translation "nóht" is already included
                        #skip 'nóht na rôki', 'nóht' is already included
                        #skip 'drôben', better translation 'tánek' is already included
                        #skip "zatílnik", because "vrát" is already included
                        #skip "maščôba", because "mást" is already included
                        #skip "grêbsti", means SCRATCH rather than DIG, and 'kopáti' is already included
                        #skip "plákati", more common "jókati" is already included (source: IE-CoR)
                        continue 
                    
                    #Switch ordering of length and tone markings in order for the length
                    #to be counted as part of the phoneme
                    #tr = re.sub('˦ː', 'ː˦', tr)
                    #tr = re.sub('˨ː', 'ː˨', tr)
                    
                    #Then change the tone markings to use same system as BCS/Lithuanian
                    tr = re.sub('˦', '́', tr) #high tone
                    tr = re.sub('˨', '̀', tr) #low tone

                    #Perform final obstruent devoicing
                    sl_devoicing = {'b':'p', 'd':'t', 'ɡ':'k', 'z':'s', 'ʒ':'ʃ'}
                    k = -1
                    while (abs(k) < len(tr)) and (tr[k] in sl_devoicing):
                        tr = list(tr)
                        tr[k] = sl_devoicing[tr[k]]
                        tr = ''.join(tr)
                        k -= 1
                    
                    #Only one instance of voicing assimilation needing to be fixed
                    #<grêbsti> /ɡréːbsti/ --> /ɡréːpsti/
                    tr = re.sub('bst', 'pst', tr)

                    #Allophony of <v> and <l>
                    #<v, l> word-finally and preceding consonants are [u]~[u̯]~[w]
                    tr = list(tr)
                    v_indices = [i for i in range(len(tr)) if tr[i] in ['ʋ', 'l']]
                    for v_index in v_indices:
                        if v_index == len(tr)-1: #if word-final
                            tr[v_index] = 'u̯'
                        else:
                            nxt = tr[v_index+1]
                            if nxt in consonants:
                                tr[v_index] = 'u̯'
                    tr = ''.join(tr)
                    
                
                elif lang == 'Czech':
                    if orth in ['šatstvo', 'běžet', 'jemný', 'rudý', 'týl', 
                                'vlas', 'dráp', 'pazneht', 'omastek',
                                'střihat', 'rýt']:
                        #skip 'šatstvo', more appropriate translation for CLOTHES 'šaty' is already in wordlist
                        #skip 'běžet', means RUN rather than WALK
                        #skip 'jemný', not quite the right translation and tenký is already included
                        #skip 'rudý', not used in the color sense and 'červený' is already included
                        #skip "týl", because "krk" is already included
                        #skip "vlas", because more usual plural form "vlasy" is already included
                        #skip 'pazneht' and 'dráp', because 'nehet' is already included
                        #skip 'omastek', because 'tuk' is already included
                        #skip 'střihat', because 'řezat' is already included
                        #skip 'rýt', because 'kopat' is already included
                        continue
                    
                    replace_orth = {'pěšina':'stezka', #pěšina is not wrong, but stezka matches a cognate set used in other languages
                                    'silnice':'cesta', #cesta is a better/more general word for ROAD, matches cognate set in other languages
                                    'osivo':'semeno', #semeno is better translation for SEED, matches other cognate sets
                                    'ňadra':'hruď', #match cognate set in other languages (reference: IE-CoR)
                                    'spálit':'pálit', #use imperfective to match other languages
                                    'přivázat':'vázat', #reference: IE-CoR
                                    'házet':'hodit', #hodit is perfective of házet; form used in IE-CoR and matches Slovak /hodiť/
                                    'hůlka':'hůl', #reference: IE-CoR
                                    'pusa':'ústa', #reference: IE-CoR
                                    'lupen':'list', #reference: IE-CoR
                                    'uhonit':'lovit', #reference: IE-CoR
                                    'květina':'květ', #reference: IE-CoR
                                    'daleký':'daleko', #FAR as adverb, source IE-CoR
                                    'spočítat':'počítat', #reference: IE-CoR
                                    'boj':'bít se' #FIGHT as verb, reference: IE-CoR
                                    }
                    if orth in replace_orth:
                        orth = replace_orth[orth]
                    
                    #NEL Czech transcriptions had many errors, use my Czech G2P tool 
                    #instead on orthographic form
                    tr = transcribe_cz(orth)
                    
                    #Czech has no geminated/long consonants, only preserved in orthography for etymological reasons
                    tr = re.sub('kk', 'k', tr)
                    tr = re.sub('nn', 'n', tr)
                    
                    #Exception is in prefixes, e.g. <od-> followed by <t>,
                    #then pronounced as two distinct consonants rather than geminate
                    #All instances of /tt/ in Czech NEL words are of this type,
                    #so no need to simplify /tt/ to /t/
                
                elif lang == 'Slovak':
                    
                    #skip mistaken translations which aren't to be replaced
                    if orth in ['vajíčko', 'šatstvo', 'spáliť', 'bežať', 
                                'priviazať', 'jemný', 'väzy', 'usmrtiť',
                                'hora', 'kvetina', 'paznecht', 'masť',
                                'strihať', 'ryť']:
                        #skip 'vajíčko', it is simply the diminutive of 'vajce', which is already in wordlist
                        #skip 'šatstvo', more appropriate translation for CLOTHES 'šaty' is already in wordlist
                        #skip 'spáliť', because 'páliť' already included
                        #skip 'bežať', means RUN rather than WALK
                        #skip 'priviazať', use 'viazať' instead (see below)
                        #skip 'jemný', not quite the right translation and tenký is already included
                        #skip "väzy", because "krk" is already included
                        #skip "usmrtiť", because "zabiť" is already included
                        #skip 'hora', it means MOUNTAIN, not FOREST
                        #skip 'kvetina' because 'kvet' is already included
                        #skip 'paznecht' because 'necht' is already included
                        #skip 'masť', means OINTMENT and not FAT, and 'tuk' is already included
                        #skip 'strihať', because 'rezať' is already included
                        #skip 'ryť', because 'kopať' is already included
                        continue
                    
                    #Correct some translations
                    replace_orth = {'mračno':'mrak', #'mračno' is not a correct translation for CLOUD, rather 'mrak'
                                    'osivo':'semeno', #'osivo' is not corrected translation for SEED, rather 'semeno'
                                    'hradská':'cesta', #cesta is a better/more general word for ROAD, matches cognate set in other languages
                                    'zaviazať':'viazať', #more general verb, reference: IE-CoR (and remove extra listing 'priviazať')
                                    'počúvať':'počuť', #reference: IE-CoR
                                    'ďaleký':'ďaleko', #FAR as adverb, source IE-CoR
                                    'boj':'biť sa' #FIGHT as verb; source IE-CoR
                                    }
                    if orth in replace_orth:
                        orth = replace_orth[orth]
                    
                    #NEL Slovak transcriptions had many errors, use my Slovak G2P tool 
                    #instead on orthographic form
                    tr = transcribe_sk(orth)
                
                elif lang == 'Polish':
                    #NEL Polish transcriptions had many errors, use my Czech G2P tool 
                    #instead on orthographic form
                    
                    if orth in ['spalić', 'drobny', 'włos', 'płynąć',
                                'szpon', 'krajać']: #skip these words
                        #skip "spalić", "palić się" is already included (standard form according to IE-CoR)
                        #skip "drobny", better translation "cienki" is already included
                        #skip "włos", because more usual plural form "włosy" is already included
                        #skip "płynąć", because "ciec" is already included
                        #skip 'szpon', because 'paznokieć' is already included
                        #skip 'krajać', because 'ciąć' is already included
                        continue
                    
                    #Correct some translations
                    replace_orth = {'łabędż':'łabędź', #misspelling
                                    'niedźwiedż':'niedźwiedź', #misspelling
                                    'zimny':'chłodny', #zimny is not wrong, but chłodny is the cognate set used in other languages, so better choice
                                    'właściwy':'prawidłowy', #better translation, fits with cognate set in other languages
                                    'dłoń':'ręka', #dłoń is PALM OF THE HAND, not HAND; ręka is HAND
                                    'ulica':'droga', #ulica is STREET, droga is ROAD (and matches existing cognate sets)
                                    'siew':'nasiono', #siew meangs "SOWING"; SEED is nasiono or nasienie
                                    'biust':'pierś', #biust is a loanword, "pierś" matches cognate classes in other languages (reference IE-CoR)
                                    'daleki':'daleko', #FAR as adverb, source IE-CoR
                                    'bój':'bić się' #FIGHT as verb; souce IE-CoR
                                    }
                    if orth in replace_orth:
                        orth = replace_orth[orth]
                    
                    #Then perform the G2P conversion on the orthography
                    tr = transcribe_pl(orth, final_denasal=True)
                    
                    #Remove dental diacritic from automatic transcription, this level of detail is unnecessary
                    tr = re.sub('̪', '', tr)
                    
                    #Only one example of <kk>, in <miękki>; not released double due to preceding nasal
                    tr = re.sub('kk', 'k', tr)
                    
                    #Replace '_' with white space
                    tr = re.sub('_', ' ', tr)
                
                elif lang in ['Belarusian', 'Ukrainian']:
                    orth = re.sub("’", "'", orth)
                    
                    if orth in ['дрібний', 'рівний', 'потилиця', 'кіготь', 'бій', #UK
                                'патыліца', 'волас', 'кіпцюр']: #BE
                        #skip UK 'дрібний', better translation 'тонкий' is already included
                        #skip UK 'рівний', better translation 'гладкий' is already included
                        #skip UK 'потилиця' / BE 'патыліца', because UK 'шия' and BE 'шыя' are already included
                        #skip BE 'волас' because the more usual plural form 'валасы' is already included
                        #skip BE 'кіпцюр' and UK 'кіготь' because BE 'ногаць' and UK 'ніготь' are already included
                        #skip UK 'бій'; it is FIGHT as a noun rather than a verb; verb is already present (via correction)
                        continue
                    
                    #Fetch the stress-annotated orthography
                    stress_orth = stress_annotations[lang][orth]
                    stress_orth, note = stress_orth
                    #Check whether the orthography was modified, if so take the new orthography
                    if note != '': 
                        orth = strip_ch(stress_orth, ['́']) #remove stress mark  
                    
                    #Automatically transcribe the stress-annotated form
                    if lang == 'Belarusian':
                        tr = transcribe_be(stress_orth)
                    elif lang == 'Ukrainian':
                        tr = transcribe_uk(stress_orth)    
                    
                #Then make general, non-language specific corrections
                #Don't do this for CZ/PL/BG/UK/BE/RU, as they were already properly transcribed otherwise
                if lang not in ['Czech', 'Polish', 'Bulgarian',
                                'Ukrainian', 'Belarusian', 'Russian']:
                    tr = fix_transcription(tr)
                
                
            except IndexError:
                print(lang, entry['rawIPA'])
                problems.append((lang, entry['rawIPA']))
                
            
            new_entry = NEL_data[i]
            parameter_id = re.sub(' ', '_', gloss)
            new_entry['ID'] = '_'.join([strip_ch(new_name, [' ']), parameter_id])
            new_entry['Language_ID'] = new_name
            new_entry['Glottocode'] = glottocode
            new_entry['ISO 639-3'] = iso_code
            new_entry['Parameter_ID'] = gloss
            new_entry['Value'] = orth
            new_entry['Form'] = tr
            new_entry['Segments'] = ' '.join(segment_word(tr))
            if source_orth != orth:
                new_entry['Source_Form'] = f'{source_orth} / {original_tr}'
            else:
                new_entry['Source_Form'] = original_tr
            new_entry['Cognate_ID'] = parameter_id
            new_entry['Loan'] = ''
            new_entry['Comment'] = ''
            new_entry['Source'] = 'Dellert et al., 2019'


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
    write_data(balto_slavic_NEL_data, str(parent_dir) + '/Balto-Slavic/balto_slavic_NEL_data.csv')
    write_data(uralic_NEL_data, str(parent_dir) + '/Uralic/uralic_NEL_data.csv')
        
        
        