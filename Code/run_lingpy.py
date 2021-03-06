from lingpy import *
from load_languages import *
from auxiliary_functions import csv_to_dict, create_folder
from phonetic_distance import strip_diacritics
import re


#%%
def prepare_lexstat_input(lang_group, output_file=None):
    if output_file == None:
        create_folder('LexStat', lang_group.directory)
        output_file = f'{lang_group.directory}/LexStat/LexStat_input_{lang_group.name}.tsv'
    
    with open(output_file, 'w') as f:
        f.write('DOCULECT\tCONCEPT\tTOKENS\n')
        for doculect in lang_group.languages:
            lang = lang_group.languages[doculect]
            for concept in lang.vocabulary:
                for entry in lang.vocabulary[concept]:
                    orth, ipa, segments = entry
                    line = '\t'.join([doculect, concept, " ".join(segments)])
                    f.write(f'{line}\n')
    print(f'Wrote data to {output_file}.')
        
    
def run_lexstat(lang_group, output_file=None):
    if output_file == None:
        create_folder('LexStat', lang_group.directory)
        output_file = f'{lang_group.directory}/LexStat/LexStat_input_{lang_group.name}.tsv'
    prepare_lexstat_input(lang_group, output_file)
    wl = Wordlist(output_file)
    lex = LexStat(output_file , segments='tokens', check=False) #previously False 
    lex.get_scorer()
    #lex.output('tsv', filename=f'{lang_group.directory}/LexStat/LexStat_output_{lang_group.name}.bin', ignore=[])
    lex.cluster(method='lexstat', threshold=0.60, ref='lexstatid')
    lex.output('tsv', filename=f'{lang_group.directory}/LexStat/LexStat_{lang_group.name}-lexstat')
    #lex = LexStat(f'{lang_group.directory}/LexStat/LexStat_output_{lang_group.name}.bin.tsv')
    
tr_fixes = {'à':'à',
                'ȁ':'ȁ',
                'á':'á',
                'ā':'ā',
                'â':'â',
                'ǎ':'ǎ',
                'ã':'ã',
                'ḁ':'ḁ',
                'ă':'ă',
                'ǣ':'ǣ',
                'é':'é',
                'è':'è',
                'ê':'ê',
                'ẽ':'ẽ',
                'ě':'ě',
                'ĕ':'ĕ',
                'ḛ':'ḛ',
                'ë':'ë',
                'ì':'ì',
                'ȉ':'ȉ',
                'í':'í',
                'î':'î',
                'ĩ':'ĩ',
                'ǐ':'ǐ',
                'ĭ':'ĭ',
                'ḭ':'ḭ',
                'ī':'ī',
                'ḿ':'ḿ',
                'ń':'ń',
                'ǹ':'ǹ',
                'ō':'ō',
                'ó':'ó',
                'ò':'ò',
                'ȍ':'ȍ',
                'ô':'ô',
                'ǒ':'ǒ',
                'õ':'õ',
                'ŏ':'ŏ',
                'ř':'ř',
                'ù':'ù',
                'ȕ':'ȕ',
                'ú':'ú',
                'û':'û',
                'ǔ':'ǔ',
                'ũ':'ũ',
                'ṳ':'ṳ',
                'ṵ':'ṵ',
                'ŭ':'ŭ',
                'ū':'ū',
                'ẅ':'ẅ',
                'ý':'ý',
                'ŷ':'ŷ',
                'ỹ':'ỹ',
                '̩̂':'̩̂',
                '̩̂':'̩̂',
                }    
    
def process_lexstat_data(lang_group, tr_fixes=tr_fixes, filepath=None):
    if filepath == None:
        create_folder('LexStat', lang_group.directory)
        filepath = f'{lang_group.directory}/LexStat/LexStat_{lang_group.name}-lexstat.tsv'

    try:
        lexstat_data = csv_to_dict(filepath, sep='\t', start=3)
    except FileNotFoundError:
        run_lexstat(lang_group, output_file=filepath)
        lexstat_data = csv_to_dict(filepath, sep='\t', start=3)
    
    cognates = defaultdict(lambda:defaultdict(lambda:[]))
    #Convert characters back to IPA, which were distorted when running LexStat
    
    for i in lexstat_data:
        entry = lexstat_data[i]
        if entry['LEXSTATID'] != '':
            ipa = entry['IPA']
            for ch in tr_fixes:
                ipa = re.sub(ch, tr_fixes[ch], ipa)
            cognates[entry['CONCEPT']][entry['LEXSTATID']].append((entry['DOCULECT'], ipa))
    return cognates

def create_LexStat_cognate_index(lang_group, output_file=None,
                                sep='\t', variants_sep='~', **kwargs):
    assert sep != variants_sep
    if output_file == None:
        output_file = f'{lang_group.directory}/LexStat/{lang_group.name} LexStat Vocabulary Index.csv'
    
    #Create cognate set index
    cognate_sets = process_lexstat_data(lang_group, **kwargs)
    
    #Write cognate set index to .csv file
    with open(output_file, 'w') as f:
        language_names = sorted([lang_group.languages[lang].name 
                                 for lang in lang_group.languages])
        header = '\t'.join(['Gloss'] + language_names)
        f.write(f'{header}\n')
        
        for concept in sorted(list(cognate_sets.keys())):
            cognate_ids = list(cognate_sets[concept].keys())
            for i in range(len(cognate_ids)):
                cognate_id = cognate_ids[i]
                new_cognate_id = concept + '_' + str(i+1)
                forms = cognate_sets[concept][cognate_id]
                forms_dict = defaultdict(lambda:[])
                forms_list = [new_cognate_id]
                for form in forms:
                    lang, ipa = form
                    forms_dict[lang].append(ipa)
                for lang in language_names:
                    lang_forms = forms_dict.get(lang, [''])
                    forms_list.append(variants_sep.join(lang_forms))
                f.write(sep.join(forms_list))
                f.write('\n')


def adjust_characters(lexstat_ch, skip=[]):
    # for ch in tr_fixes:
    #     if ch not in skip:
    #         lexstat_ch = re.sub(ch, tr_fixes[ch], lexstat_ch)
    # return lexstat_ch
    return strip_diacritics(unidecode.unidecode(lexstat_ch))
    

def load_lexstat_clusters(dataset, concept_set=None, **kwargs):
    lexstat_data = process_lexstat_data(dataset, **kwargs)
    
    if concept_set == None:
        concept_set = list(lexstat_data.keys())
    else:
        concept_set = [concept for concept in lexstat_data if concept in concept_set]
    
    
    lexstat_data = {concept:{cognate_set:{f'{adjust_characters(item[0])} /{item[1]}/' 
                                          for item in lexstat_data[concept][cognate_set]} 
                             for cognate_set in lexstat_data[concept]} 
                    for concept in concept_set}
    return lexstat_data 
    
    
    