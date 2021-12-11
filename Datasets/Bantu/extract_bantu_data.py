import os, re
from collections import defaultdict
from pathlib import Path
import pandas as pd
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent
source_data_dir = 'Source/grollemundbantu/'

#Load phonetic distance data and auxiliary functions
os.chdir(str(grandparent_dir) + '/Code')
from auxiliary_functions import csv_to_dict
from phonetic_distance import *
os.chdir(local_dir)

#%%
#LOAD LANGUAGE DATA CSV
lang_data = pd.read_csv(str(parent_dir) + '/Languages.csv', sep='\t')
lang_data = {lang_data['Source Name'][i]:(lang_data['Name'][i], 
                                          lang_data['Glottocode'][i], 
                                          lang_data['ISO 639-3'][i])
             for i in range(len(lang_data['Source Name'])) 
             if lang_data['Dataset'][i] == 'Bantu'}


#%%
#LOAD BANTU DATASET
forms_data = pd.read_csv(source_data_dir + 'cldf/forms.csv')
bantu_langs_data = csv_to_dict(source_data_dir + 'cldf/languages.csv')
bantu_langs_data = {bantu_langs_data[i]['ID']:(bantu_langs_data[i]['Name'], 
                                          bantu_langs_data[i]['Glottocode'], 
                                          bantu_langs_data[i]['ISO639P3code'])
                   for i in bantu_langs_data}
  
#%%
#LOAD CONCEPTICON MAPPING
concept_data = pd.read_csv(source_data_dir + 'cldf/parameters.csv')
concepticon_dict = {concept_data['ID'][i]:concept_data['Concepticon_Gloss'][i] 
                    for i in range(len(concept_data))}

#%%
conversion_dict = {#CONSONANTS
                   'dl':'ɮ', #North Ndebele, Tsonga, Tswana, Xhosa, Zulu (language-specific fixes in function)
                   'fh':'ɸ', #Venda <fh>
                   'g':'ɡ', #replace with proper IPA character
                   'hl':'ɬ', #North Ndebele, Tsonga, Tswa, Xhosa, Zulu
                   'tsh':'ʦʰ', #Kalanga, must precede <sh>
                   'dzh':'ʣʱ', #must precede  <zh>
                   'sh':'ʃ', #Bemba, Kalanga, Lozi, Meru, Ndonga, Songe
                   'vh':'β', #Venda, Shona [fixed in function]
                   'zh':'ʒ', #Kalanga, Shona, Venda
                   
                   #Implosives: transcribed inconsistently, so turn all implosives into egressive stops
                   'ɓ':'b',
                   'ɗ':'d',
                   
                   #Aspirated/breathy consonants:
                   'bh':'bʱ', #Kalanga, Shona, Xhosa, Zulu; but not North Ndebele (just /b/, fixed in function)
                   'kh':'kʰ', #Kalanga, Makhuwa, North Ndebele, Nyanja, Tsonga, Tswa, Venda, Xhosa, Zulu
                   'ph':'pʰ', #Kalanga, Makhuwa, North Ndebele, Nyanja, Venda, Xhosa, Zulu
                   'th':'tʰ', #Kalanga, Makhuwa, North Ndebele, Nyanja, Venda, Xhosa, Zulu
                   
                   #Clicks:
                   'q':'ǃ', #palatal/post-alveolar click (Xhosa, Zulu, North Ndebele, Tswana) 
                   'ɡǃ':'ǃ̬ʱ', #voiced aspirated post-alveolar click (Xhosa, North Ndebele)
                   
                   #VOWELS: tones and nasalized vowels
                   # 'à':'a˨', 
                   # 'á':'a˦',
                   #  'â':'a˥˩',
                   #  'ã':'ã',
                   #  'è':'e˨',
                   #  'é':'e˦',
                   #  'ê':'e˥˩',
                   #  'ɛ́':'ɛ˦',
                   #  'ì':'i˨',
                   #  'í':'i˦',
                   #  'î':'i˥˩',
                   #  'ò':'o˨',
                   #  'ó':'o˦',
                   #  'ô':'o˥˩',
                   #  'õ':'õ',
                   #  'ù':'u˨',
                   #  'ú':'u˦',
                   #  'û':'u˥˩',
                   #  'ě':'e˩˥',
                   #  'ń':'n˦',
                   #  'ō':'o˧',
                   #  'ǎ':'a˩˥',
                   #  'ǒ':'o˩˥',
                   #  'ǔ':'u˩˥',
                   #  'ǹ':'n˨',
                   #  'ȁ':'a˩',
                   #  'ȉ':'i˩',
                   #  'ȍ':'o˩',
                   #  'ȕ':'u˩',
                   #  'ḿ':'m˦',
                   
                    'à':'à', 
                    'á':'á',
                     'â':'â',
                     'ã':'ã',
                     'è':'è',
                     'é':'é',
                     'ê':'ê',
                     'ì':'ì',
                     'í':'í',
                     'î':'î',
                     'ò':'ò',
                     'ó':'ó',
                     'ô':'ô',
                     'õ':'õ',
                     'ù':'ù',
                     'ú':'ú',
                     'û':'û',
                     'ě':'ě',
                     'ń':'ń',
                     'ō':'ō',
                     'ǎ':'ǎ',
                     'ǒ':'ǒ',
                     'ǔ':'ǔ',
                     'ǹ':'ǹ',
                     'ȁ':'ȁ',
                     'ȉ':'ȉ',
                     'ȍ':'ȍ',
                     'ȕ':'ȕ',
                     'ḿ':'ḿ',
                    'ẅ':'ẅ',
                    'ɩ':'ɪ', #uncertain
                   
                   #Affricates
                   'pf':'p͡f', #Nyanja, Rundi, Shona, Tsonga, Venda
                   'ts':'ʦ',
                   'dz':'ʣ',
                   'tʃ':'ʧ',
                   'dʒ':'ʤ',
                   'tɬ':'t͡ɬ',     
                   
                   #Tones
                   # '̏':'˩',
                   # '̀':'˨',
                   # '̄':'˧',
                   # '́':'˦',
                   # '̋':'˥',
                   # '̂':'˥˩',
                   # '̌':'˩˥',
                   
                   #Other
                   '\+':'', 
                   ':':'ː',
                   '´':'́' #high tone
                   
                   }


digraphs = []
slashes = []
def fix_tr(tr, lang, orth, gloss):
    segments = tr.split()
    fixed = []
    for seg in segments:
        if '/' in seg:
            slashes.append(seg)
            seg = seg.split('/')[0] #some segments transcribed as, e.g. <ú/u> to denote tone --> simply take the first part
        
        fixed.append(seg)
    
    fixed = ''.join(fixed)
    for seq in conversion_dict:
        fixed = re.sub(seq, conversion_dict[seq], fixed)
    
    if lang in ['Bemba', 'Lozi', 'Luba-Lulua', 'Makhuwa', 'Nyankole', 'Umbundu']:
        fixed = re.sub('c', 'ʧ', fixed)
        fixed = re.sub('x', 'ʃ', fixed) #primarily/only Makhuwa
        
    elif lang == 'Kikuyu':
        fixed = re.sub('c', 'ʃ', fixed)
    
    elif lang == 'Kimbundu':
        fixed = re.sub('x', 'ʃ', fixed)
        fixed = re.sub('nh', 'ɲ', fixed) #best guess given that it appears in word for 'ANIMAL' (/ɲama/ in most other languages) and Kimbundu is spoken in Angola, so may have had Portuguese influence on the orthography (hence <nh> = /ɲ/)
        
    elif lang == 'Ndonga':
        fixed = re.sub('tʰ', 'θ', fixed) #change <th> --> /tʰ/ --> /θ/
    
    elif lang == 'North Ndebele':
        fixed = re.sub('bʱ', 'b', fixed) #change <bh> --> /bʱ/ --> /b/
    
    elif lang == 'Shona':
        #<vh> = /v̤/, /v/ = /ʋ/
        fixed = re.sub('v', 'ʋ', fixed)
        fixed = re.sub('β', 'v̤', fixed)
        fixed = re.sub('ʒ', 'ʒ̤', fixed) #add breathy diacritic
        fixed = re.sub('mh', 'm̤', fixed)
        fixed = re.sub('nh', 'n̤', fixed)
    
    elif lang == 'Sukuma':
        fixed = re.sub('mh', 'm̤', fixed)
        fixed = re.sub('nh', 'n̤', fixed)
        fixed = re.sub('ŋh', 'ŋ̤', fixed) #add breathy diacritic
        
    elif lang == 'Swahili':
        #Swahili <j> mistranscribed as /j/ --> /ʄ/
        if 'j' in orth:
            fixed = re.sub('j', 'ʄ', fixed)
        
        #Certain Swahili words transcribed wrong (e.g. without prefix although it is transcribed in other Bantu languages)
        tr_fixed = {'yumba':('ɲumba', 'nyumba'),  #<nyumba> 'HOUSE' 
                    'ywele':('ɲwele', 'nywele'), #<nywele> 'HAIR' 
                    'yoka':('ɲoka', 'nyoka'), #<nyoka> 'SNAKE'
                    'kono':('mkono', 'mkono'), #<mkono> 'ARM'
                    'dege':('ndeɡe', 'ndege'), #<ndege> 'BIRD'
                    'fupa':('mfupa', 'mfupa'), #<mfupa> 'BONE'
                    'mande':('umande', 'umande'), #<umande> 'DEW'
                    'bwa':('mbwa', 'mbwa'), #<mbwa> 'DOG'
                    'dovu':('ndovu', 'ndovu'), #<ndovu> 'ELEPHANT'
                    'so':('uso', 'uso'), #<uso> 'FACE',
                    'futa':('mafuta', 'mafuta'), #<mafuta> 'ORGANIC FAT OR OIL'
                    'ɲoya':('uɲoja', 'unyoya'), #<unyoya> 'FEATHER'
                    'kucha':('ukuʧa', 'ukucha'), #<ukucha> 'FINGERNAIL'
                    'oto':('moto', 'moto'), #<moto> 'FIRE'
                    'buzi':('mbuzi', 'mbuzi'), #<mbuzi> 'GOAT'
                    'dongo':('udonɡo', 'udongo'), #<udongo> 'EARTH (SOIL)'
                    'chwa':('kiʧwa', 'kichwa'), #<kichwa> 'HEAD'
                    'oyo':('mojo', 'moyo'), #<moyo> 'HEART'
                    'su':('kisu', 'kisu'), #<kisu> 'KNIFE'
                    'guu':('mɡuu', 'mguu'), #<mguu> 'LEG'
                    'wanamume':('mwanamume', 'mwanamume'), #<mwanamume> 'MAN'
                    'wezi':('mwezi', 'mwezi'), #<mwezi> 'MOON'
                    'tovu':('kitovu', 'kitovu'), #<kitovu> 'NAVEL'
                    'siku':('usiku', 'usiku'), #<usiku> 'NIGHT'
                    'tu':('mtu', 'mtu'), #<mtu> 'PERSON'
                    'vua':('mvua', 'mvua'), #<mvua> 'RAIN (PRECIPITATION)'
                    'jia':('nʄia', 'njia'), #<njia> 'ROAD'
                    'zizi':('mzizi', 'mzizi'), #<mzizi> 'ROOT'
                    'changa':('mʧanɡa', 'mchanga'), #<mchanga> 'SAND'
                    'gozi':('nɡozi', 'ngozi'), #<ngozi> 'SKIN'
                    'bingu':('uwinɡu', 'uwingu'), #<uwingu> 'SKY' (<mbingu> is plural)
                    'oʃi':('moʃi', 'moshi'), #<moshi> 'SMOKE'
                    'kuki':('mkuki', 'mkuki'), #<mkuki> 'SPEAR'
                    'kia':('mkia', 'mkia'), #<mkia> 'TAIL'
                    'limi':('ulimi', 'ulimi'), #<ulimi> 'TONGUE'
                    'ti':('mti', 'mti'), #<mti> 'TREE'
                    'bili':('wili', '-wili'), #<-wili> 'TWO' (<mbili> is form in N-class)
                    'jiji':('kiʄiʄi', 'kijiji'), #<kijiji> 'VILLAGE'
                    'ta':('kita', 'kita'), #<kita> 'WAR'
                    'ji':('maʄi', 'maji'), #<maji> 'WATER'
                    'pepo':('upepo', 'upepo'), #<upepo> 'WIND'
                    'wanamke':('mwanamke', 'mwanamke'), #<mwanamke> 'WOMAN'
                    }
        
        fixed, orth = tr_fixed.get(orth, (fixed, orth))
        if gloss == 'MOUTH':
            fixed, orth = 'kiɲwa', 'kinywa'
    
    elif lang == 'Tonga':
        fixed = re.sub('sj', 'sʲ', fixed)
        fixed = re.sub('zj', 'zʲ', fixed)
            
    elif lang in ['Tsonga', 'Tswa']:
        fixed = re.sub('ɮ', 'd͡l', fixed) #change <dl> --> /ɮ/ --> /d͡l/
        fixed = re.sub('ndd͡l', 'nd͡l', fixed)
        fixed = re.sub('mh', 'm̤', fixed)
        fixed = re.sub('nh', 'n̤', fixed)
        fixed = re.sub('c', 'ʧ', fixed)
        fixed = re.sub('x', 'ʃ', fixed)
        fixed = re.sub('rh', 'rʱ', fixed)
    
    elif lang == 'Venda':
        fixed = re.sub('sw', 'ʂ', fixed)
        fixed = re.sub('ʣʱ', 'ʤ', fixed) #change <dzh> --> /ʣʱ/ --> /ʤ/
    
    elif lang in ['Zulu', 'Xhosa']:
        fixed = re.sub('ɮ', 'ɮʱ', fixed)
        fixed = re.sub('c', 'ǀ', fixed) #dental click
        fixed = re.sub('x', 'ǁ', fixed) #lateral click
        
        if lang == "Zulu":
            fixed = re.sub('nɮ', 'nd͡ɮ', fixed)
            
        else: #Xhosa
            fixed = re.sub('nɮʱ', 'nd͡ɮ', fixed) #no aspiration in Xhosa when prenasalized
            fixed = re.sub('ɡǀʼ', 'ǀ̬ʱ', fixed) #voiced aspirated dental click
            fixed = re.sub('rh', 'x', fixed)
            
    #Reverse order of tonemes and length markings, e.g. '˨ː' --> 'ː˨'   
    t = '|'.join(tonemes)
    r = re.search(f'[{t}]+ː', fixed)
    if r != None:
        start, end = r.span()
        fixed = list(fixed)
        fixed[start+1:end] = fixed[start:end-1]
        fixed[start] = 'ː'
        fixed = ''.join(fixed)
    
    return fixed, orth

#%%
#Remove infinitive prefixes from verb transcriptions
Bantu_verbs = ['BITE', 'BURN (SOMETHING)', 'COME', 'COUNT', 'DIE', 'DRINK', 
               'EAT', 'FALL', 'FLY (MOVE THROUGH AIR)', 'GIVE', 'HEAR', 'KILL', 
               'KNOW (SOMETHING)', 'SEE', 'SEND', 'STEAL', 'VOMIT', 'WALK']
accents = '|'.join(list(suprasegmental_diacritics)+tonemes)  
uku_ = f"^u[{accents}]*ku[{accents}]*"
ukw_ = f"^u[{accents}]*kw[{accents}]*"
oku_ = f"^o[{accents}]*ku[{accents}]*"
okw_ = f"^o[{accents}]*kw[{accents}]*"
iku_ = f"^i[{accents}]*ku[{accents}]*"
ku_ = f"^ku[{accents}]*"
kw_ = f"^kw[{accents}]*"
ko_ = f"^ko[{accents}]*"
gu_ = f"^ɡ[u|ʊ][{accents}]*"
u_ = f"^u[{accents}]*"
w_ = f"^w[{accents}]*"
i_ = f"^i[{accents}]*"
a_ = f"^a[{accents}]*"

#Inifitive prefixes attested in dataset for each language
infinitive_prefixes = {'Bemba':[uku_, ukw_],
                       'Bulu':[],
                       'Fang':[a_],
                       'Ganda':[ku_],
                       'Gogo':[ku_, gu_],
                       'Haya':[ku_, kw_, oku_],
                       'Kalanga':[kw_],
                       'Kamba':[kw_, ko_],
                       'Kikuyu':[ku_],
                       'Kimbundu':[ku_],
                       'Koongo':[kw_],
                       'Lingala':[ku_, kw_],
                       'Lozi':[ku_],
                       'Luba-Katanga':[ku_, kw_],
                       'Luba-Lulua':[ku_],
                       'Makhuwa':[u_, w_],
                       'Meru':[i_],
                       'Ndonga':[oku_, okw_],
                       'Ndzwani Comorian':[],
                       'Ngazidja Comorian':[],
                       'North Ndebele':[uku_],
                       'Nyanja':[],
                       'Nyankole':[ku_, kw_],
                       'Rundi':[ku_, kw_, gu_],
                       'Shona':[],
                       'Songe':[ku_],
                       'Sukuma':[ku_, kw_, gu_],
                       'Swahili':[],
                       'Tonga':[ku_, kw_],
                       'Tsonga':[],
                       'Tswa':[],
                       'Tswana':[],
                       'Umbundu':[oku_, okw_],
                       'Venda':[],
                       'Xhosa':[uku_, ukw_],
                       'Yaka':[],
                       'Zulu':[uku_, ukw_]}

def remove_inf_prefix(tr, lang):
    inf_prefixes = infinitive_prefixes[lang]
    if len(inf_prefixes) > 0:
        for form in inf_prefixes:
            if re.match(form, tr) != None:
                root = re.split(form, tr, maxsplit=1)[-1]
                
                #Correct situation in Kamba language where prefix /ko-/ merges
                #with initial /o/ in root, yielding /koː-/
                #Simply change the initial length marker into /o/
                if lang == 'Kamba':
                    if root[0] == 'ː':
                        root = list(root)
                        root[0] = 'o'
                        root = ''.join(root)
                
                return root
            
        #If no prefix was found, simply return the original transcription
        return tr
    else:
        return tr
    


#%%
skipped = []
skipped_cognates = []
bantu_data = defaultdict(lambda:{})
index = 0
for index, entry in forms_data.iterrows():
    word_id = ''.join(entry['ID'].split('-')[:-1]) + '-1-1'
    lang_id = entry['Language_ID']

    #Filter only languages in languages.csv
    try:
        new_name, glottocode, iso_code = lang_data[lang_id]
    except KeyError:
        skipped.append(lang_id)
        continue 
    
    concept = entry['Parameter_ID']
    concepticon_gloss = concepticon_dict[concept]
    
    cognate_id = concepticon_gloss + '_' + entry['Cognacy'].split('-')[-1]
    
    tr = entry['Segments']
    
    #skip nan entries
    if type(entry['Value']) == float:
        continue
    if type(entry['Segments']) == float:
        continue
    
    index += 1
    
    new_entry = bantu_data[index]
    new_entry['ID'] = '_'.join([re.sub('-', '_', new_name), str(cognate_id)])
    new_entry['Language_ID'] = new_name
    new_entry['Glottocode'] = glottocode
    new_entry['ISO 639-3'] = iso_code if type(iso_code) != float else ''
    new_entry['Parameter_ID'] = concepticon_gloss
    tr, orth = fix_tr(tr, new_name, entry['Value'], concepticon_gloss)
    new_entry['Value'] = orth
    
    #Remove infinitive prefixes
    if concepticon_gloss in Bantu_verbs:
        prefix_tr = tr[:]
        tr = remove_inf_prefix(tr, new_name)
        if len(tr.strip()) == 0:
            del bantu_data[index]
            index -= 1
            continue
        if tr != prefix_tr:
            print(f'{new_name.upper()}: /{prefix_tr}/ --> /{tr}/')
        
    new_entry['Form'] = tr
    new_entry['Segments'] = ' '.join(segment_word(new_entry['Form']))
    new_entry['Source_Form'] = tr
    new_entry['Cognate_ID'] = cognate_id
    new_entry['Loan'] = entry['Comment'].upper() if type(entry['Comment']) != float else ''
    new_entry['Comment'] = entry['Comment'] if type(entry['Comment']) != float else ''
    new_entry['Source'] = entry['Source'] if type(entry['Source']) != float else ''

#%%
#CHECKING PHONETIC CHARACTERS
bantu_phones = set([ch for i in bantu_data
                   for ch in bantu_data[i]['Form']])

new_chs = set(phone for phone in bantu_phones 
              if phone not in all_sounds+diacritics+[' ']+tonemes)

def lookup_segment(segment, data=bantu_data, langs=None):
    if langs == None:
        langs = set(data[i]['Language_ID'] for i in data)
    
    occurrences = defaultdict(lambda:defaultdict(lambda:[]))
    for i in data:
        entry = data[i]
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
output_file = 'bantu_data.csv'
print(f'Writing preprocessed Bantu data to "{output_file}"...')

def write_data(data_dict, output_file, sep='\t'):
    features = list(data_dict[list(data_dict.keys())[0]].keys())
    with open(output_file, 'w') as f:
        header = sep.join(features)
        f.write(f'{header}\n')
        for i in data_dict:
            try:
                values = sep.join([data_dict[i][feature] for feature in features])
            except TypeError:
                print(i, data_dict[i])
            f.write(f'{values}\n')
            
write_data(bantu_data, output_file=output_file)
