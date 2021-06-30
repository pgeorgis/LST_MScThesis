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

#Load automatic G2P transcription tools for Czech and Polish
os.chdir(str(grandparent_dir) + '/Code/Automatic_Transcription/')
from transcribe_czech import *
from transcribe_polish import *
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
          
        #CORRECTIONS IN SLAVIC LANGUAGES
        elif lang == 'Russian':
            #Russian: palatalized /l/ <ль> or <л> followed by soft vowel transcribed
            #as /l/ instead of /lʲ/
            #simply changing all instances of /l/ to /lʲ/ isn't a problem because 
            #the non-palatalized version is transcribed as /ɫ/
            tr = re.sub('l', 'lʲ', tr)
            
            #Russian: <щ> transcribed as /ʃʃ/ or /ʃʲː/ instead of /ɕː/
            tr = re.sub('(?<!͡)ʃʃ', 'ɕː', tr)
            tr = re.sub('ʃʲː', 'ɕː', tr)
            
            #and <ч> as /t͡ʃʲ/ or /t͡ʃ/ instead of <ʨ>
            tr = re.sub('t͡ʃʲ', 'ʨ', tr)
            tr = re.sub('t͡ʃ', 'ʨ', tr)
            
            #/ʒʲ/ --> /ʐj/, e.g. <побережье>, <ружьё> 
            #(<ь> after hard consonants such as <ж> marks /j/ rather than palatalization, 
            #as hard consonants have no palatalized equivalent)
            tr = re.sub('ʒʲ', 'ʐj', tr)
            
            #and /ʒ/ --> /ʐ/, /ʃ/ --> /ʂ/
            tr = re.sub('ʒ', 'ʐ', tr)
            tr = re.sub('ʃ', 'ʂ', tr)
            
            #Russian: <что> transcribed with long /ɔː/ -- Russian has no long vowels
            tr = re.sub('ɔː', 'ɔ', tr)
            
            #Then, it has <ё> transcribed as /о/ instead of /ɵ/
            #and <о> transcribed as /ɔ/ instead of /o/
            tr = re.sub('o', 'ɵ', tr)
            tr = re.sub('ɔ', 'o', tr)
            #Exception: <ё> is /o/, not /ɵ/, after hard consonants <ж, ш>, it is only /ɵ/ after soft consonants
            tr = re.sub('ʐɵ', 'ʐo', tr)
            tr = re.sub('ʂɵ', 'ʂo', tr)
            
            #Correct sequence /stʲ/ to /sʲtʲ/ (palatalization assimilation)
            tr = re.sub('stʲ', 'sʲtʲ', tr)
            
            #Remove half-long marking
            tr = re.sub('ˑ', '', tr)
            
            #removed this block because of a bug and because we can't properly convert all
            #vowels to ther inter-palatal form since some are transcribed as reduced, see note below
            """
            #Russian <а, у> between soft/palatalized consonants are [æ, ʉ]
            segments = segment_word(tr)
            if len(segments) > 1: #don't bother for words consisting of only a single segment
                ru_soft_c = ['bʲ', 'dʲ', 'fʲ', 'lʲ', 'mʲ', 'nʲ', 'pʲ', 
                             'rʲ', 'sʲ', 'tʲ', 'vʲ', 'zʲ', 'ɕː', 'ʨ']
                tr = [segments[0]]
                for i in range(1, len(segments)-1):
                    seg = segments[i]
                    if seg in ['a', 'u', 'ʊ']: 
                        nxt_seg = segments[i+1]
                        prev_seg = segments[i-1]
                        if ((nxt_seg in ru_soft_c) and (prev_seg in ru_soft_c)):
                            #some /a/ are mistranscribed as /ə, ɐ/ (e.g. <часть> /ʨəstʲ/), 
                            #can't do anything about those though because we can't distinguish 
                            #them from reduced <о> unless the orthography is checked
                            if seg in ['a']:
                                tr.append('æ')
                            elif seg in ['u', 'ʊ']:
                                tr.append('ʉ')
                        else:
                            tr.append(seg)
                    else:
                        tr.append(seg)
                tr.append(segments[-1])
                tr = ''.join(tr)"""
            
            
        elif lang == 'Bulgarian':
            #Palatalized <т, д> should be transcribed as either /c, ɟ/ or /tʲ, dʲ/, not mix and match
            #The former version is the standard transcription convention, also already used in NEL for /c/
            tr = re.sub('dʲ', 'ɟ', tr)
            
        elif lang == 'Croatian':
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
        
        elif lang == 'Slovene':
            #Switch ordering of length and tone markings in order for the length
            #to be counted as part of the phoneme
            tr = re.sub('˦ː', 'ː˦', tr)
            tr = re.sub('˨ː', 'ː˨', tr)
        
        elif lang == 'Czech':
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
            #Same geminate/long consonant situation as described above in Czech
            #Exception: <ŕ, ĺ> /r̩ː, l̩ː/, which we leave unchanged
            tr = re.sub('kː', 'k', tr)
            tr = re.sub('nː', 'n', tr)
            
            #<dd> in prefix, as describe in Czech
            tr = re.sub('dː', 'dd', tr)
            
            #Diphthongs <ie>, <iu>, <ia> have /ɪ̯/, not /i̯/, according to Illustrations of IPA Slovak
            tr = re.sub('i̯', 'ɪ̯', tr)
            
            #Likewise, diphthong <ô> has /ʊ̯/ not /u̯/
            tr = re.sub('u̯', 'ʊ̯', tr)
        
        elif lang == 'Polish':
            #NEL Polish transcriptions had many errors, use my Czech G2P tool 
            #instead on orthographic form
            words = orth.split()
            tr_words = []
            for word in words:
                #This word (reflexive particle) typically is not pronounced with a nasal vowel, 
                #as would have been automatically transcribed
                if word == 'się':
                    tr_words.append('ɕɛ')
                    
                #Otherwise transcribe all other words automatically using G2P
                else:
                    tr_words.append(transcribe_pl(word))
            tr = ' '.join(tr_words)
            
            #Remove dental diacritic from automatic transcription, this level of detail is unnecessary
            tr = re.sub('̪', '', tr)
            
            #Only one example of <kk>, in <miękki>; not released double due to preceding nasal
            tr = re.sub('kk', 'k', tr)
            
            #Replace '_' with white space
            tr = re.sub('_', ' ', tr)
        
        elif lang == 'Belarusian':
            #Apostrophe <ʼ> in Belarusian orthography marks that preceding consonant is not palatalized,
            #similar to Russian <ъ> --> should not be in phonetic transcription
            tr = re.sub('ʼ', '', tr)
            
            #/dz/ --> /ʣ/
            tr = re.sub('dz', 'ʣ', tr)
            
            #Note: geminates in Belarusian are genuine geminates
        
        elif lang == 'Ukrainian':
            #All instances of /t͡sː/ should actually be /sʦ/
            tr = re.sub('t͡sː', 'sʦ', tr)
            #Other geminates are genuine geminates, as in Belarusian
            #Correct these to geminates, will be corrected to proper alveolar affricates in next line
            tr = re.sub('ʈʈ͡ʂ', 'ʈ͡ʂː', tr)
            
            #Change retroflex fricatives and affricates to alveolar, according to Illustrations of the IPA Ukrainian
            tr = re.sub('ʈ͡ʂ', 'ʧ', tr)
            tr = re.sub('ɖ͡ʐ', 'ʤ', tr)
            tr = re.sub('ʂ', 'ʃ', tr)
            tr = re.sub('ʐ', 'ʒ', tr)
            
        
            
            
        #Then make general, non-language specific corrections
        #Don't do this for Czech or Polish, as they were already properly transcribed using G2P
        if lang not in ['Czech', 'Polish']:
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
        
        
        