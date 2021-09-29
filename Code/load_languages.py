import os, re, itertools, copy
from statistics import mean
from collections import defaultdict
import math, bcubed
from auxiliary_functions import *
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
from phonetic_distance import *
from word_evaluation import *
from phoneme_correspondences import PhonemeCorrDetector
from linguistic_distance import *

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
        
        #Create a folder for plots within the dataset's directory
        create_folder('Plots', self.directory)
        
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
    
        #Information about languages included
        self.name = name
        self.languages = {}
        self.lang_ids = {}
        self.glottocodes = {}
        self.iso_codes = {}
        
        #Concepts in dataset
        self.concepts = defaultdict(lambda:defaultdict(lambda:[]))
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
                                            family=self,
                                            lang_id=self.lang_ids[lang],
                                            loan_c=self.loan_c)
            for concept in self.languages[lang].vocabulary:
                self.concepts[concept][lang].extend(self.languages[lang].vocabulary[concept])
        
    
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
            self.remove_languages([smallest_lang])
        
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
        
    
    def calculate_phoneme_pmi(self, output_file=None, **kwargs):
        """Calculates phoneme PMI for all language pairs in the dataset and saves
        the results to file"""
        
        #Specify output file name if none is specified
        if output_file == None:
            output_file = f'{self.directory}{self.name} Phoneme PMI.csv'
        
        #Calculate or retrieve PMI values and save them to the specified output file
        with open(output_file, 'w') as f:
            f.write('Language1,Phone1,Language2,Phone2,PMI\n')
            for lang1 in self.languages.values():
                for lang2 in self.languages.values():
                    if lang1 != lang2:
                        
                        #Check whether phoneme PMI has been calculated already for this pair
                        #If not, calculate it now
                        if lang2 not in lang1.phoneme_pmi:
                            print(f'Calculating phoneme PMI for {lang1.name} and {lang2.name}...')
                            pmi = PhonemeCorrDetector(lang1, lang2).calc_phoneme_pmi(**kwargs)
                        
                        #Else retrieve the precalculated values
                        else:
                            pmi = lang1.phoneme_pmi[lang2]
                            
                        #Save all segment pairs with non-zero PMI values to file
                        for seg1 in pmi:
                            for seg2 in pmi[seg1]:
                                if pmi[seg1][seg2] != 0:
                                    if abs(pmi[seg1][seg2]) > lang1.phonemes[seg1] * lang2.phonemes[seg2]: #skip extremely small decimals
                                        f.write(f'{lang1.name},{seg1},{lang2.name},{seg2},{pmi[seg1][seg2]}\n')
    
    
    def load_phoneme_pmi(self, pmi_file=None, excepted=[]):
        """Loads pre-calculated phoneme PMI values from file"""
        
        #Designate the default file name to search for if no alternative is provided
        if pmi_file == None:
            pmi_file = f'{self.directory}{self.name} Phoneme PMI.csv'
        
        #Try to load the file of saved PMI values
        try:
            pmi_data = pd.read_csv(pmi_file)
            
        #If the file is not found, recalculate the PMI values and save to 
        #a file with the specified name
        except FileNotFoundError:
            self.calculate_phoneme_pmi(output_file=pmi_file)
            pmi_data = pd.read_csv(pmi_file)
        
        #Iterate through the dataframe and save the PMI values to the Language
        #class objects' phoneme_pmi attribute
        for index, row in pmi_data.iterrows():
            lang1 = self.languages[row['Language1']]
            lang2 = self.languages[row['Language2']]
            if (lang1 not in excepted) and (lang2 not in excepted):
                phone1, phone2 = row['Phone1'], row['Phone2']
                pmi_value = row['PMI']
                lang1.phoneme_pmi[lang2][phone1][phone2] = pmi_value
            
    
    def cognate_set_dendrogram(self, cognate_id, 
                               dist_func, sim=True, 
                               combine_cognate_sets=False,
                               method='average',
                               title=None, save_directory=None,
                               **kwargs):
        if combine_cognate_sets == True:
            cognate_ids = [c for c in self.cognate_sets if cognate_id in c]
        else:
            cognate_ids = [cognate_id]
            
        words = [strip_ch(item[i], ['(', ')'])
                 for cognate_id in cognate_ids
                 for item in self.cognate_sets[cognate_id].values()
                 for i in range(len(item))]
        
        lang_labels = [key for cognate_id in cognate_ids
                       for key in self.cognate_sets[cognate_id].keys()
                       for i in range(len(self.cognate_sets[cognate_id][key]))]
        labels = [f'{lang_labels[i]} /{words[i]}/' for i in range(len(words))]
        
        #if dist_func in [word_sim, word_adaptation_surprisal, score_pmi]:
        #For this function, it requires tuple input of (word, lang)
        langs = [self.languages[lang] for lang in lang_labels]
        words = list(zip(words, langs))
        
        if title == None:
            title = f'{self.name} "{cognate_id}"'
        
        if save_directory == None:
            save_directory = self.directory + '/Plots/'
        
        draw_dendrogram(group=words,
                        labels=labels,
                        dist_func=dist_func,
                        sim=sim,
                        method=method,
                        title=title,
                        save_directory=save_directory,
                        **kwargs
                        )
    
    def cluster_cognates(self, concept_list,
                         dist_func, sim,
                         cutoff,
                         method='average',
                         **kwargs):
        clustered_cognates = {}
        for concept in sorted(concept_list):
            #print(f'Clustering words for "{concept}"...')
            words = [entry[1] for lang in self.concepts[concept] 
                     for entry in self.concepts[concept][lang]]
            lang_labels = [lang for lang in self.concepts[concept] 
                           for entry in self.concepts[concept][lang]]
            labels = [f'{lang_labels[i]} /{words[i]}/' for i in range(len(words))]
            
            #if dist_func in [word_sim, word_adaptation_surprisal, score_pmi]:
            #For this function, it requires tuple input of (word, lang)
            langs = [self.languages[lang] for lang in lang_labels]
            words = list(zip(words, langs))
    
            
            clusters = cluster_items(group=words,
                                     labels=labels,
                                     dist_func=dist_func,
                                     sim=sim,
                                     cutoff=cutoff,
                                     **kwargs)
            
            clustered_cognates[concept] = clusters
        
        return clustered_cognates
    
    
    def evaluate_clusters(self, clustered_cognates):
        """Evaluates B-cubed precision, recall, and F1 of results of automatic  
        cognate clustering against dataset's gold cognate classes"""
        
        precision_scores, recall_scores, f1_scores = {}, {}, {}
        for concept in clustered_cognates:
            clusters = {item:set([i]) for i in clustered_cognates[concept] 
                        for item in clustered_cognates[concept][i]}
            gold_clusters = {f'{lang} /{strip_ch(tr, ["(", ")"])}/':set([c]) 
                             for c in self.cognate_sets 
                             if c.split('_')[0] == concept 
                             for lang in self.cognate_sets[c] 
                             for tr in self.cognate_sets[c][lang]}
            precision = bcubed.precision(clusters, gold_clusters)
            recall = bcubed.recall(clusters, gold_clusters)
            fscore = bcubed.fscore(precision, recall)
            precision_scores[concept] = precision
            recall_scores[concept] = recall
            f1_scores[concept] = fscore
        return mean(precision_scores.values()), mean(recall_scores.values()), mean(f1_scores.values())
        
# baltoslavic_lexstat = {concept:{cognate_set:{f'{item[0]} /{item[1]}/' 
#                                               for item in baltoslavic_lexstat[concept][cognate_set]} 
#                                 for cognate_set in baltoslavic_lexstat[concept]} 
#                         for concept in baltoslavic_lexstat}
                      
            
    
    
    def draw_tree(self, 
                  dist_func, sim, concept_list=None,                  
                  cluster_func=None, cluster_sim=None, cutoff=None,
                  cognates='auto', 
                  method='average', title=None, save_directory=None,
                  return_newick=False,
                  **kwargs):
        
        #Use all available concepts by default
        if concept_list == None:
            concept_list = sorted([c for c in self.concepts.keys() 
                                   if len(self.concepts[c]) > 1])
        else:
            concept_list = sorted([concept for concept in concept_list 
                                   if concept in self.concepts])
        
        if dist_func == Z_score_dist:
            cognates = 'none'
        #Automatic cognate clustering        
        if cognates == 'auto':
            assert cluster_func != None
            assert cluster_sim != None
            assert cutoff != None
            clustered_concepts = self.cluster_cognates(concept_list,
                                                       dist_func=cluster_func, 
                                                       sim=cluster_sim, 
                                                       cutoff=cutoff)

        #Use gold cognate classes
        elif cognates == 'gold':
            clustered_concepts = defaultdict(lambda:defaultdict(lambda:[]))
            for concept in concept_list:
                cognate_ids = [cognate_id for cognate_id in self.cognate_sets 
                               if cognate_id.split('_')[0] == concept]
                for cognate_id in cognate_ids:
                    for lang in self.cognate_sets[cognate_id]:
                        for form in self.cognate_sets[cognate_id][lang]:
                            form = strip_ch(form, ['(', ')'])
                            clustered_concepts[concept][cognate_id].append(f'{lang} /{form}/')
        
        #No separation of cognates/non-cognates: 
        #all synonymous words are evaluated irrespective of cognacy
        elif cognates == 'none':
            clustered_concepts = {concept:{concept:[f'{lang} /{self.concepts[concept][lang][i][1]}/'
                                  for lang in self.concepts[concept] 
                                  for i in range(len(self.concepts[concept][lang]))]}
                                  for concept in concept_list}            
        
        #Raise error for unrecognized cognate clustering methods
        else:
            print(f'Error: cognate clustering method "{cognates}" not recognized!')
            raise ValueError
        
        #Dendrogram characteristics
        languages = [self.languages[lang] for lang in self.languages]
        names = [lang.name for lang in languages]
        if title == None:
            title = f'{self.name}'
        if save_directory == None:
            save_directory = self.directory + 'Plots/'
        
        return draw_dendrogram(group=languages, 
                               labels=names, 
                               dist_func=dist_func, 
                               sim=sim, 
                               method=method, 
                               title=title, 
                               save_directory=save_directory, 
                               return_newick=return_newick,
                               clustered_cognates=clustered_concepts, #better way?
                               **kwargs
                               )
    
    
    def examine_cognates(self, language_list, concepts=None):
        if concepts == None:
            concepts = sorted(list(self.cognate_sets.keys()))
        
        for cognate_set in concepts:
            lang_count = len([lang for lang in language_list if lang.name in self.cognate_sets[cognate_set]])
            if lang_count > 1:
                print(cognate_set)
                for lang in language_list:
                    print(f'{lang.name}: {" ~ ".join(self.cognate_sets[cognate_set][lang.name])}')
                print('\n')
                
                
    def remove_languages(self, langs_to_delete):
        """Removes a list of languages from a dataset"""
        
        for lang in langs_to_delete:
            del self.languages[lang]
            del self.lang_ids[lang]
            del self.glottocodes[lang]
            del self.iso_codes[lang]
        
            for concept in self.concepts:
                try:
                    del self.concepts[concept][lang]
                except KeyError:
                    pass
            
            for cognate_set in self.cognate_sets:
                try:
                    del self.cognate_sets[cognate_set][lang]
                except KeyError:
                    pass
        
        #Remove empty concepts and cognate sets
        self.concepts = default_dict({concept:self.concepts[concept] 
                         for concept in self.concepts 
                         if len(self.concepts[concept]) > 0}, 
                                     l=defaultdict(lambda:[]))
        
        self.cognate_sets = default_dict({cognate_set:self.cognate_sets[cognate_set] 
                                          for cognate_set in self.cognate_sets 
                                          if len(self.cognate_sets[cognate_set]) > 0}, 
                                         l=defaultdict(lambda:[]))

    
    def subset(self, new_name, include=None, exclude=None, **kwargs):
        """Creates a subset of the existing dataset, including only select languages"""
        
        new_dataset = copy.deepcopy(self)
        
        #Remove languages not part of new subset
        if include != None:
            to_delete = [lang for lang in self.languages if lang not in include]
        else:
            assert exclude != None
            to_delete = exclude
        new_dataset.remove_languages(to_delete)
        
        #Assign the new name and any other specified attributes
        new_dataset.name = new_name
        for key, value in kwargs.items():
            setattr(new_dataset,key,value)
        
        #Recalculate mutual coverage among remaining langauges
        new_dataset.mutual_coverage = new_dataset.calculate_mutual_coverage()
        
        return new_dataset
        
                

#%%
class Language(Dataset):
    def __init__(self, name, lang_id, data, glottocode, iso_code, family,
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
        self.family = family
        self.data = data
        
        #Phonemic inventory
        self.phonemes = defaultdict(lambda:0)
        self.vowels = defaultdict(lambda:0)
        self.consonants = defaultdict(lambda:0)
        self.tonemes = defaultdict(lambda:0)
        self.tonal = False
        
        #Phonological contexts
        self.unigrams = defaultdict(lambda:0)
        self.bigrams = defaultdict(lambda:0)
        self.trigrams = defaultdict(lambda:0)
        self.gappy_trigrams = defaultdict(lambda:0)
        self.info_contents = {}
        
        #Lexical inventory
        self.vocabulary = defaultdict(lambda:[])
        self.loanwords = defaultdict(lambda:[])
        
        
        self.create_vocabulary()
        self.create_phoneme_inventory()
        self.check_affricates()
        
        self.phoneme_entropy = entropy(self.phonemes)
        
        #Comparison with other languages
        self.phoneme_correspondences = defaultdict(lambda:defaultdict(lambda:0))
        self.phoneme_pmi = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:0)))
        self.phoneme_surprisal = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:-self.phoneme_entropy)))
        self.detected_cognates = defaultdict(lambda:[])
        self.detected_noncognates = defaultdict(lambda:[])
        
    def create_vocabulary(self):
        #Remove stress and tone diacritics from segmented words; syllabic diacritics (above and below); spaces
        diacritics_to_remove = list(suprasegmental_diacritics) + ['̩', '̍', ' ']
        
        for i in self.data:
            entry = self.data[i]
            concept = entry[self.concept_c]
            orthography = entry[self.orthography_c]
            ipa = entry[self.ipa_c]
            segments = segment_word(ipa, remove_ch=diacritics_to_remove)
            if len(segments) > 0:
                if [orthography, ipa, segments] not in self.vocabulary[concept]:
                    self.vocabulary[concept].append([orthography, ipa, segments])
                loan = entry[self.loan_c]
            
                #Mark known loanwords
                if loan == 'TRUE':
                    self.loanwords[concept].append([orthography, ipa, segments])
                    
                    
    def create_phoneme_inventory(self):
        for concept in self.vocabulary:
            for entry in self.vocabulary[concept]:
                orthography, ipa, segments = entry
                
                #Count phones
                for segment in segments:
                    self.phonemes[segment] += 1
                    self.unigrams[segment] += 1
            
                #Count trigrams and gappy trigrams
                padded_segments = ['#', '#'] + segments + ['#', '#']
                for j in range(1, len(padded_segments)-1):
                    trigram = (padded_segments[j-1], padded_segments[j], padded_segments[j+1])
                    self.trigrams[trigram] += 1
                    self.gappy_trigrams[('X', padded_segments[j], padded_segments[j+1])] += 1
                    self.gappy_trigrams[(padded_segments[j-1], 'X', padded_segments[j+1])] += 1
                    self.gappy_trigrams[(padded_segments[j-1], padded_segments[j], 'X')] += 1
                
                #Count bigrams
                padded_segments = padded_segments[1:-1]
                for j in range(1, len(padded_segments)):
                    bigram = (padded_segments[j-1], padded_segments[j])
                    self.bigrams[bigram] += 1
                    
        
        
        #Normalize counts
        total_tokens = sum(self.phonemes.values())
        for phoneme in self.phonemes:
            self.phonemes[phoneme] = self.phonemes[phoneme] / total_tokens
        
        #Get dictionaries of vowels and consonants
        self.vowels = normalize_dict({v:self.phonemes[v] 
                                      for v in self.phonemes 
                                      if strip_diacritics(v)[0] in vowels}, 
                                     default=True, lmbda=0)
        
        self.consonants = normalize_dict({c:self.phonemes[c] 
                                         for c in self.phonemes 
                                         if strip_diacritics(c)[0] in consonants}, 
                                         default=True, lmbda=0)
        
        self.tonemes = normalize_dict({t:self.phonemes[t] 
                                       for t in self.phonemes 
                                       if strip_diacritics(t)[0] in tonemes}, 
                                      default=True, lmbda=0)
        
        #Designate language as tonal if it has tonemes
        if len(self.tonemes) > 0:
            self.tonal = True
            
    
    def lookup(self, segment, 
               field='transcription',
               return_list=False):
        """Prints or returns a list of all word entries containing a given 
        segment/character or regular expression"""
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
                orthography, transcription, segments = entry
                if re.search(segment, entry[field_index]) != None:
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
    
    
    def calculate_infocontent(self, word, segmented=False):
        #Return the pre-calculated information content of the word, if possible
        if segmented == True:
            joined = ''.join([ch for ch in word])
            if joined in self.info_contents:
                return self.info_contents[joined]
        else:
            if word in self.info_contents:
                return self.info_contents[word]
        
        #Otherwise calculate it from scratch
        #First segment the word if necessary
        #Then pad the segmented word
        if segmented == False:
            segments = segment_word(word)
            padded = ['#', '#'] + segments + ['#', '#']
        else:
            padded = ['#', '#'] + word + ['#', '#']
        info_content = {}
        for i in range(2, len(padded)-2):
            trigram_counts = 0
            trigram_counts += self.trigrams[(padded[i-2], padded[i-1], padded[i])]
            trigram_counts += self.trigrams[(padded[i-1], padded[i], padded[i+1])]
            trigram_counts += self.trigrams[(padded[i], padded[i+1], padded[i+2])]
            gappy_counts = 0
            gappy_counts += self.gappy_trigrams[(padded[i-2], padded[i-1], 'X')]
            gappy_counts += self.gappy_trigrams[(padded[i-1], 'X', padded[i+1])]
            gappy_counts += self.gappy_trigrams[('X', padded[i+1], padded[i+2])]
            info_content[i-2] = (padded[i], -math.log(trigram_counts/gappy_counts, 2))
        self.info_contents[''.join(padded[2:-2])] = info_content
        return info_content
    
    
    def bigram_probability(self, bigram, delta=0.7):
        """Returns Kneser-Ney smoothed conditional probability P(p2|p1)"""
        
        p1, p2 = bigram
        
        #Total number of distinct bigrams
        n_bigrams = len(self.bigrams)
        
        #List of bigrams starting with p1
        start_p1 = [b for b in self.bigrams if b[0] == p1]
        
        #Number of bigrams starting with p1
        n_start_p1 = len(start_p1)
        
        #Number of bigrams ending in p2
        n_end_p2 = len([b for b in self.bigrams if b[1] == p2])
        
        #Unigram probability estimation
        pKN_p1 = n_end_p2 / n_bigrams
        
        #Normalizing constant lambda
        total_start_p1_counts = sum([self.bigrams[b] for b in start_p1])
        l_KN = (delta / total_start_p1_counts) * n_start_p1
        
        #Bigram probability estimation
        numerator = max((self.bigrams.get(bigram, 0)-delta), 0)
        
        return (numerator/total_start_p1_counts) + (l_KN*pKN_p1)
        
        
    
    def phone_dendrogram(self, 
                         distance='weighted_dice', 
                         method='complete', 
                         exclude_length=True, exclude_tones=True,
                         title=None, save_directory=None):
        if title == None:
            title = f'{self.name} Phonemes'
        
        if save_directory == None:
            save_directory = self.family.directory + '/Plots/'
            
        phonemes = list(self.phonemes.keys())
        
        if exclude_length == True:
            phonemes = list(set(strip_ch(p, ['ː']) for p in phonemes))
        
        if exclude_tones == True:
            phonemes = [p for p in phonemes if p not in self.tonemes]
        
        draw_dendrogram(group=phonemes, 
                        labels=phonemes,
                        dist_func=phone_sim,
                        sim=True,
                        distance=distance,
                        method=method,
                        title=title,
                        save_directory=save_directory)
    
#%%
#COMBINING DATASETS

def combine_datasets(dataset_list):
    pass

    

#%%
#LOAD FAMILIES AND WRITE VOCABULARY INDEX FILES
datasets_path = str(parent_dir) + '/Datasets/'
os.chdir(datasets_path)
families = {}
for family in ['Arabic', 'Balto-Slavic', 'Dravidian',
               'Hokan','Italic',
               'Polynesian',
               'Quechuan',
               'Sinitic', 
               'Turkic', 'Uralic', #'Germanic'
               ]:
    family_path = re.sub('-', '_', family).lower()
    filepath = datasets_path + family + f'/{family_path}_data.csv'
    print(f'Loading {family}...')
    families[family] = Dataset(filepath, family)
    #families[family].prune_languages(min_amc=0.75)
    families[family].write_vocab_index()
    language_variables = {format_as_variable(lang):families[family].languages[lang] 
                          for lang in families[family].languages}
    globals().update(language_variables)
globals().update(families)
BaltoSlavic = families['Balto-Slavic']
os.chdir(local_dir)

#Get lists and counts of languages/families
all_languages = [families[family].languages[lang] for family in families 
                 for lang in families[family].languages]
all_families = [families[family] for family in families]
total_languages = len(all_languages)
total_families = len(all_families)

#Load common concepts
common_concepts = pd.read_csv(str(parent_dir) + '/Datasets/Concepts/common_concepts.csv', sep='\t')
common_concepts = set(concept 
                      for i, row in common_concepts.iterrows() 
                      for concept in row['Alternate_Labels'].split('; '))
