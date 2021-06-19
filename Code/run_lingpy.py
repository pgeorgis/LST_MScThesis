#RUN LINGPY ON ARABIC AND BALTO-SLAVIC DATA TO GET PRELIMINARY COGNATE SETS
#CAN THEN MANUALLY CORRECT THE OUTPUT IN ORDER TO GET GOLD COGNATE SET
from lingpy import *
from load_languages import *
from auxiliary_functions import csv_to_dict

def prepare_lingpy_input(lang_group, 
                       output_file=None,
                       DOCULECT='Language_ID',
                       CONCEPT='Parameter_ID',
                       TOKENS='Segments'):
    if output_file == None:
        output_file = f'{lang_group.directory}LingPy_input_{lang_group.name}.tsv'
    
    with open(output_file, 'w') as f:
        f.write('DOCULECT\tCONCEPT\tTOKENS\n')
        for i in lang_group.data:
            entry = lang_group.data[i]
            line = '\t'.join([entry[DOCULECT], entry[CONCEPT], entry[TOKENS]])
            f.write(f'{line}\n')
    print(f'Wrote data to {output_file}.')
        
    
def run_lingpy(lang_group, 
               output_file=None, 
               DOCULECT='Language_ID', 
               CONCEPT='Parameter_ID', 
               TOKENS='Segments'):
    if output_file == None:
        output_file = f'{lang_group.directory}LingPy_input_{lang_group.name}.tsv'
    prepare_lingpy_input(lang_group, output_file, DOCULECT, CONCEPT, TOKENS)
    wl = Wordlist(output_file)
    lex = LexStat(output_file, segments='tokens', check=False) #previously check=True
    lex.cluster(method="sca", threshold=0.45, ref='scaid')
    lex.get_scorer(runs=10000)
    lex.output('tsv', filename=f'LingPy_output_{lang_group.name}.bin', ignore=[])
    lex.cluster(method='lexstat', threshold=0.60, ref='lexstatid')
    lex.output('tsv', filename=f'Lingpy_{lang_group.name}-lexstat')
    lex = LexStat(f'Lingpy_output_{lang_group.name}.bin.tsv')
    
    
def process_lingpy_data(lang_group, filepath=None):
    if filepath == None:
        filepath = f'{lang_group.directory}LingPy_{lang_group.name}-lexstat.tsv'

    try:
        lexstat_data = csv_to_dict(filepath, sep='\t', start=3)
    except FileNotFoundError:
        run_lingpy(lang_group, output_file=filepath)
        lexstat_data = csv_to_dict(filepath, sep='\t', start=3)
    
    cognates = defaultdict(lambda:defaultdict(lambda:[]))
    fix_dia_dict = {'ã':'ã', 'ẽ':'ẽ', 'ĩ':'ĩ', 'õ':'õ', 'ũ':'ũ', 'ṳ':'ṳ'}
    for i in lexstat_data:
        entry = lexstat_data[i]
        if entry['LEXSTATID'] != '':
            cognates[entry['CONCEPT']][entry['LEXSTATID']].append((entry['DOCULECT'], entry['IPA']))
    return cognates

def create_LingPy_cognate_index(lang_group, output_file=None,
                                sep='\t', variants_sep='~'):
    assert sep != variants_sep
    if output_file == None:
        output_file = f'{lang_group.directory}{lang_group.name} LingPy Vocabulary Index.csv'
    
    #Create cognate set index
    cognate_sets = process_lingpy_data(lang_group)
    
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
            
    

    
    
    
    