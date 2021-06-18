import pandas as pd
import os
from collections import defaultdict
os.chdir('/Users/phgeorgis/Documents/Python Projects/') #fix this eventually, but somehow data is being lost while loading the csv with pandas
from auxiliary_functions import csv_to_dict, format_as_variable, strip_ch

class Family:
    def __init__(self, filepath, name, 
                 language_name='Language_ID', 
                 word_features={'Parameter_ID':'Concept',
                                'Value':'Orthography', 
                                'Form':'IPA', 
                                'Segments':'Segments', 
                                'Source_Form':'Source_Form',
                                'Cognate_ID':'Cognate_ID',
                                'Loan':'Loan',
                                'Source':'Source'}):
        self.filepath = filepath
        self.directory = self.filepath.rsplit('/', maxsplit=1)[0] + '/'
        self.name = name
        self.word_features = word_features
        self.language_name_column = language_name
        self.languages = {}
        self.load_data()
        self.create_vocab_index()
        self.concepts = set(concept.split('_')[0] for concept in self.cognate_sets.keys())
        
    def load_data(self, sep='\t'):
        #Load data file
        #data = pd.read_csv(self.filepath, sep=sep, error_bad_lines=False)
        data = csv_to_dict(self.filepath, divider=sep)
        
        
        #Initialize languages
        language_data = defaultdict(lambda:defaultdict(lambda:{}))
        for i in data:
            lang = data[i][self.language_name_column]
            for column in self.word_features:
                feature = self.word_features[column]
                language_data[lang][i][feature] = data[i][column]
        
        for lang in language_data:
            self.languages[lang] = Language(name=lang, vocabulary=language_data[lang])
    
    def create_vocab_index(self, output_file=None,
                           sep='\t', variants_sep='~'):
        assert sep != variants_sep
        if output_file == None:
            output_file = f'{self.directory}{self.name} Vocabulary Index.csv'
        
        #Create cognate set index
        self.cognate_sets = defaultdict(lambda:defaultdict(lambda:[]))
        for lang in self.languages:
            lang = self.languages[lang]
            for i in lang.vocabulary:
                entry = lang.vocabulary[i]
                cognate_id = entry['Cognate_ID']
                transcription = entry['IPA']
                
                #Write loanwords in parentheses, e.g. (word)
                loan = entry['Loan']
                if loan == 'TRUE':
                    transcription = f'({transcription})'
                self.cognate_sets[cognate_id][lang.name].append(transcription)
                
        #Write cognate set index to .csv file
        with open(output_file, 'w') as f:
            language_names = sorted([self.languages[lang].name for lang in self.languages])
            header = '\t'.join(['Gloss'] + language_names)
            f.write(f'{header}\n')
            
            for cognate_set_id in sorted(list(self.cognate_sets.keys())):
                forms = [cognate_set_id]
                for lang in language_names:
                    lang_forms = self.cognate_sets[cognate_set_id].get(lang, [''])
                    forms.append(variants_sep.join(lang_forms))
                f.write(sep.join(forms))
                f.write('\n')
                
                    
                    
                
            
            

        

class Language:
    def __init__(self, name, vocabulary):
        self.name = name
        #self.glottocode = glottocode
        #self.iso_code = iso_code
        self.vocabulary = vocabulary
        self.phonemes = defaultdict(lambda:0)
        self.create_phoneme_inventory()
        
    def create_phoneme_inventory(self):
        for i in self.vocabulary:
            entry = self.vocabulary[i]
            segments = entry['Segments'].split()
            for segment in segments:
                self.phonemes[segment] += 1
        
        #Normalize counts
        total_tokens = sum(self.phonemes.values())
        for phoneme in self.phonemes:
            self.phonemes[phoneme] = self.phonemes[phoneme] / total_tokens
    
        
#%%
#LOAD FAMILIES
processed_data_path = '/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Resources/Data/Processed Data/'
os.chdir(processed_data_path)

families = {}
for family in ['Arabic', 'Italic', 'Polynesian', 'Sinitic', 'Turkic', 'Uralic',
               'NorthEuraLex/BaltoSlavic', 'NorthEuraLex/Uralic']:
    filepath = processed_data_path + family + '/data.csv'
    family_name = family.split('/')[-1]
    families[family_name] = Family(filepath, family_name)
globals().update(families)

#GET COMMON GLOSSES
concept_counts = defaultdict(lambda:0)
for family in families:
    family = families[family]
    for concept in family.concepts:
        concept_counts[concept] += 1
common_concepts = sorted([concept for concept in concept_counts 
                          if concept_counts[concept] == len(families)])

