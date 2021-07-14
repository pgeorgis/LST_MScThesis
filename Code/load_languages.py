import os, re, itertools
from statistics import mean
from collections import defaultdict
from auxiliary_functions import csv_to_dict, strip_ch
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent

class Dataset: 
    def __init__(self, filepath, name, 
                 id_c = 'ID',
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
        self.id_c = id_c
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
        self.lang_ids = {}
        self.glottocodes = {}
        self.iso_codes = {}
        self.concepts = []
        self.cognate_sets = defaultdict(lambda:defaultdict(lambda:[]))
        self.load_data()
        self.load_cognate_sets()
        self.mutual_coverage = self.calculate_mutual_coverage()
        
    def load_data(self, sep='\t'):
        #Load data file
        #data = pd.read_csv(self.filepath, sep=sep, error_bad_lines=False)
        data = csv_to_dict(self.filepath, sep=sep)
        self.data = data
        
        #Initialize languages
        language_vocab_data = defaultdict(lambda:defaultdict(lambda:{}))
        language_vocabulary = defaultdict(lambda:defaultdict(lambda:{}))
        for i in data:
            lang = data[i][self.language_name_c]
            features = list(data[i].keys())
            for feature in features:
                value = data[i][feature]
                language_vocab_data[lang][i][feature] = value
            self.glottocodes[lang] = data[i][self.glottocode_c]
            self.iso_codes[lang] = data[i][self.iso_code_c]
            self.lang_ids[lang] = data[i][self.id_c].split('_')[0]
        
        for lang in language_vocab_data:
            self.languages[lang] = Language(name=lang, data=language_vocab_data[lang],
                                            id_c = self.id_c,
                                            segments_c = self.segments_c,
                                            ipa_c = self.ipa_c,
                                            orthography_c = self.orthography_c,
                                            concept_c = self.concept_c,
                                            glottocode=self.glottocodes[lang],
                                            iso_code=self.iso_codes[lang],
                                            lang_id=self.lang_ids[lang],
                                            loan_c=self.loan_c)
            self.concepts.extend(self.languages[lang].vocabulary.keys())
            self.concepts = list(set(self.concepts))
    
    def load_cognate_sets(self):
        """Creates vocabulary index sorted by cognate sets"""
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
                
                #Don't add duplicate entries
                if transcription not in self.cognate_sets[cognate_id][lang.name]:
                    self.cognate_sets[cognate_id][lang.name].append(transcription)

    
    def write_vocab_index(self, output_file=None, 
                          sep='\t', variants_sep='~'):
        """Write cognate set index to .csv file"""
        assert sep != variants_sep
        if output_file == None:
            output_file = f'{self.directory}{self.name} Vocabulary Index.csv'
        
        
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
    
    def calculate_mutual_coverage(self, concept_list=None):
        """Calculate the mutual coverage and average mutual coverage (AMC)
        of the dataset on a particular wordlist"""
        
        #By default use the entire vocabulary if no specific concept list is given
        if concept_list == None:
            concept_list = self.concepts
        
        #Calculate mutual coverage
        concept_counts = {concept:len([lang for lang in self.languages 
                                       if concept in self.languages[lang].vocabulary]) 
                          for concept in concept_list}
        shared_concepts = [concept for concept in concept_counts
                           if concept_counts[concept] == len(self.languages)]
        mutual_coverage = len(shared_concepts)
        
        #Calculate average mutual coverage
        mutual_coverages = {}
        for lang_pair in itertools.product(self.languages.keys(), self.languages.keys()):
            lang1, lang2 = lang_pair
            if lang1 != lang2:
                lang1, lang2 = self.languages[lang1], self.languages[lang2]
                pair_mutual_coverage = len([concept for concept in lang1.vocabulary 
                                            if concept in lang2.vocabulary])
                mutual_coverages[lang_pair] = pair_mutual_coverage
        avg_mutual_coverage = mean(mutual_coverages.values()) / len(self.concepts)
        
        return mutual_coverage, avg_mutual_coverage
                    
    def prune_languages(self, min_amc=0.8, concept_list=None):
        """Prunes the language with the smallest number of transcribed words
        until the dataset's AMC score reaches the minimum value"""
        
        #By default use the entire vocabulary if no specific concept list is given
        if concept_list == None:
            concept_list = self.concepts
        
        pruned = []
        start_n_langs = len(self.languages)
        original_amc = self.calculate_mutual_coverage(concept_list)[1]
        while self.calculate_mutual_coverage(concept_list)[1] < min_amc:
            smallest_lang = min(self.languages.keys(), 
                                key=lambda x: len(self.languages[x].vocabulary))
            pruned.append((smallest_lang, len(self.languages[smallest_lang].vocabulary)))
            del self.languages[smallest_lang]
        
        self.mutual_coverage = self.calculate_mutual_coverage(concept_list)
        
        if len(pruned) > 0:
            print(f'\tPruned {len(pruned)} of {start_n_langs} {self.name} languages:')
            for item in pruned:
                lang, vocab_size = item
                if vocab_size == 1:
                    print(f'\t\t{lang} ({vocab_size} concept)')
                else:
                    print(f'\t\t{lang} ({vocab_size} concepts)')
            print(f'\tAMC increased from {round(original_amc, 2)} to {round(self.mutual_coverage[1], 2)}.')
        
            
            

        

class Language(Dataset):
    def __init__(self, name, lang_id, data, glottocode, iso_code,
                 segments_c='Segments', ipa_c='Form', 
                 orthography_c='Value', concept_c='Parameter_ID',
                 loan_c='Loan', id_c='ID'):
        
        #Attributes for parsing data dictionary (could this be inherited via a subclass?)
        self.id_c = id_c
        self.segments_c = segments_c
        self.ipa_c = ipa_c
        self.orthography_c = orthography_c
        self.concept_c = concept_c
        self.loan_c = loan_c
        
        #Language data
        self.name = name
        self.lang_id = lang_id
        self.glottocode = glottocode
        self.iso_code = iso_code
        self.data = data
        
        
        self.phonemes = defaultdict(lambda:0)
        self.vocabulary = defaultdict(lambda:[])
        self.loanwords = defaultdict(lambda:[])
        
        
        self.create_phoneme_inventory()
        self.create_vocabulary()
        self.check_affricates()
        
    def create_phoneme_inventory(self):
        for i in self.data:
            entry = self.data[i]
            segments = entry[self.segments_c].split()
            
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
        for i in self.data:
            entry = self.data[i]
            concept = entry[self.concept_c]
            orthography = entry[self.orthography_c]
            ipa = entry[self.ipa_c]
            self.vocabulary[concept].append([orthography, ipa])
            loan = entry[self.loan_c]
            
            #Mark known loanwords
            if loan == 'TRUE':
                self.loanwords[concept].append([orthography, ipa])
    
    def lookup(self, segment, 
               field='transcription',
               return_list=False):
        """Prints or returns a list of all word entries containing a given 
        segment/character or sequence or segments/characters"""
        if field == 'transcription':
            field_index = 1
        elif field == 'orthography':
            field_index = 0
        else:
            print(f'Error: search field should be either "transcription" or "orthography"!')
            raise ValueError
        
        matches = []
        for concept in self.vocabulary:
            for entry in self.vocabulary[concept]:
                orthography, transcription = entry
                if segment in entry[field_index]:
                    matches.append((concept, orthography, transcription))
        
        if return_list == True:
            return matches
        
        else:
            for match in matches:
                concept, orthography, transcription = match
                print(f"<{orthography}> /{transcription}/ '{concept}'")
            
                
    def check_affricates(self):
        """Ensure that affricates have consistent representation"""
        ligatures = ['ʦ', 'ʣ', 'ʧ', 'ʤ', 'ʨ', 'ʥ']
        double_ch = ['t͡s', 'd͡z', 't͡ʃ', 'd͡ʒ', 't͡ɕ', 'd͡ʑ']
        for aff_pair in zip(ligatures, double_ch):
            lig, double = aff_pair
            if lig in self.phonemes:
                if double in self.phonemes:
                    print(f'Warning! Both /{lig}/ and /{double}/ are in {self.name} transcriptions!')
    

#%%
#LOAD FAMILIES AND WRITE VOCABULARY INDEX FILES
datasets_path = str(parent_dir) + '/Datasets/'
os.chdir(datasets_path)
families = {}
for family in ['Arabic', 'Balto-Slavic', 'Dravidian',
               'Hokan','Italic', 
               'Polynesian', 'Sinitic', 
               'Turkic', 'Uralic']:
    family_path = re.sub('-', '_', family).lower()
    filepath = datasets_path + family + f'/{family_path}_data.csv'
    print(f'Loading {family}...')
    families[family] = Dataset(filepath, family)
    #families[family].prune_languages(min_amc=0.75)
    families[family].write_vocab_index()
    globals().update(families[family].languages)
globals().update(families)
os.chdir(local_dir)

#Get lists and counts of languages/families
all_languages = [families[family].languages[lang] for family in families 
                 for lang in families[family].languages]
all_families = [families[family] for family in families]
total_languages = len(all_languages)
total_families = len(all_families)
