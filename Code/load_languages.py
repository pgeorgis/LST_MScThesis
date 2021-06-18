#import pandas as pd
import os
from collections import defaultdict
os.chdir('/Users/phgeorgis/Documents/Python Projects/') #fix this eventually, but somehow data is being lost while loading the csv with pandas
from auxiliary_functions import csv_to_dict, strip_ch

class Family: #could also be renamed to Dataset
    def __init__(self, filepath, name, 
                 language_name_c='Language_ID',
                 concept_c = 'Parameter_ID',
                 orthography_c = 'Value',
                 ipa_c = 'Form',
                 segments_c = 'Segments',
                 cognate_c = 'Cognate_ID',
                 loan_c = 'Loan',
                 glottocode_c='Glottocode',
                 iso_code_c='ISO 639-3'):

        #Directory to dataset 
        self.filepath = filepath
        self.directory = self.filepath.rsplit('/', maxsplit=1)[0] + '/'
        
        #Columns of dataset
        self.language_name_c = language_name_c
        self.concept_c = concept_c
        self.orthography_c = orthography_c
        self.ipa_c = ipa_c
        self.segments_c = segments_c
        self.cognate_c = cognate_c
        self.loan_c = loan_c
        self.glottocode_c = glottocode_c
        self.iso_code_c = iso_code_c
    
        #About the family
        self.name = name
        self.languages = {}
        self.glottocodes = {}
        self.iso_codes = {}
        self.load_data()
        self.create_vocab_index()
        self.concepts = set(concept.split('_')[0] for concept in self.cognate_sets.keys())
        
    def load_data(self, sep='\t'):
        #Load data file
        #data = pd.read_csv(self.filepath, sep=sep, error_bad_lines=False)
        data = csv_to_dict(self.filepath, divider=sep)
        self.data = data
        
        #Initialize languages
        language_vocab_data = defaultdict(lambda:defaultdict(lambda:{}))
        for i in data:
            lang = data[i][self.language_name_c]
            features = list(data[i].keys())
            for feature in features:
                value = data[i][feature]
                language_vocab_data[lang][i][feature] = value
            self.glottocodes[lang] = data[i][self.glottocode_c]
            self.iso_codes[lang] = data[i][self.iso_code_c]
        
        for lang in language_vocab_data:
            self.languages[lang] = Language(name=lang, data=language_vocab_data[lang],
                                            segments_c = self.segments_c,
                                            ipa_c = self.ipa_c,
                                            
                                            glottocode=self.glottocodes[lang],
                                            iso_code=self.iso_codes[lang])
    
    def create_vocab_index(self, output_file=None,
                           sep='\t', variants_sep='~'):
        assert sep != variants_sep
        if output_file == None:
            output_file = f'{self.directory}{self.name} Vocabulary Index.csv'
        
        #Create cognate set index
        self.cognate_sets = defaultdict(lambda:defaultdict(lambda:[]))
        for lang in self.languages:
            lang = self.languages[lang]
            for i in lang.data:
                entry = lang.data[i]
                cognate_id = entry[self.cognate_c]
                transcription = entry[self.ipa_c]
                
                #Write loanwords in parentheses, e.g. (word)
                loan = entry[self.loan_c]
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
                
                    
                    
                
            
            

        

class Language():
    def __init__(self, name, data, glottocode, iso_code, 
                 segments_c='Segments', ipa_c=''):
        
        self.name = name
        self.glottocode = glottocode
        self.iso_code = iso_code
        self.data = data
        self.phonemes = defaultdict(lambda:0)
        self.create_phoneme_inventory(segments_c)
        
    def create_phoneme_inventory(self, segments_c): #diacritics to remove as non-phonemic
        for i in self.data:
            entry = self.data[i]
            segments = entry[segments_c].split()
            
            #Remove stress and syllabic diacritics
            diacritics_to_remove = ['ˈ', 'ˌ', '̩'] #there should be another syllabic diacritic, for above
            segments = [strip_ch(seg, diacritics_to_remove) for seg in segments]
            for segment in segments:
                self.phonemes[segment] += 1
        
        #Normalize counts
        total_tokens = sum(self.phonemes.values())
        for phoneme in self.phonemes:
            self.phonemes[phoneme] = self.phonemes[phoneme] / total_tokens
            
    def create_vocabulary(self):
        pass
    
        

#LOAD FAMILIES
processed_data_path = '/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Resources/Data/Processed Data/'
os.chdir(processed_data_path)


families = {}
for family in ['Arabic', 'Italic', 'Polynesian', 'Sinitic', 'Turkic', 'Uralic',
               'NorthEuraLex/BaltoSlavic', 'NorthEuraLex/Uralic']:
    filepath = processed_data_path + family + '/data.csv'
    family_name = family.split('/')[-1]
    families[family_name] = Family(filepath, family_name)
    globals().update(families[family_name].languages)
globals().update(families)

#%%
#GET COMMON GLOSSES
concept_counts = defaultdict(lambda:0)
for family in families:
    family = families[family]
    for concept in family.concepts:
        concept_counts[concept] += 1
common_concepts = sorted([concept for concept in concept_counts 
                          if concept_counts[concept] == len(families)])

