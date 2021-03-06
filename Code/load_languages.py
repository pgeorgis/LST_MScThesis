import os, re, itertools, copy, glob
from statistics import mean
from collections import defaultdict
import math, bcubed, random
from auxiliary_functions import *
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
from phonetic_distance import *
from word_evaluation import *
from phoneme_correspondences import PhonemeCorrDetector
from linguistic_distance import *

class LexicalDataset: 
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
        
        #Create a folder for plots and detected cognate sets within the dataset's directory
        create_folder('Plots', self.directory)
        create_folder('Cognates', self.directory)
        
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
        self.distance_matrices = {}
        
        #Concepts in dataset
        self.concepts = defaultdict(lambda:defaultdict(lambda:[]))
        self.cognate_sets = defaultdict(lambda:defaultdict(lambda:[]))
        self.clustered_cognates = defaultdict(lambda:{})
        self.load_data(self.filepath)
        self.load_cognate_sets()
        self.mutual_coverage = self.calculate_mutual_coverage()
        
        
    def load_data(self, filepath, doculects=None, sep='\t'):
        
        #Load data file
        data = csv_to_dict(filepath, sep=sep)
        self.data = data
        
        #Initialize languages
        language_vocab_data = defaultdict(lambda:defaultdict(lambda:{}))
        language_vocabulary = defaultdict(lambda:defaultdict(lambda:{}))
        for i in data:
            lang = data[i][self.language_name_c]
            if ((doculects == None) or (lang in doculects)):
                features = list(data[i].keys())
                for feature in features:
                    value = data[i][feature]
                    language_vocab_data[lang][i][feature] = value
                self.glottocodes[lang] = data[i][self.glottocode_c]
                self.iso_codes[lang] = data[i][self.iso_code_c]
                self.lang_ids[lang] = data[i][self.id_c].split('_')[0]
        
        language_list = sorted(list(language_vocab_data.keys()))
        for lang in language_list:
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
                
                #Don't add duplicate or empty entries
                if transcription.strip() != '':
                    if transcription not in self.cognate_sets[cognate_id][lang.name]:
                        self.cognate_sets[cognate_id][lang.name].append(transcription)

    
    def write_vocab_index(self, output_file=None,
                          concept_list=None,
                          sep='\t', variants_sep='~'):
        """Write cognate set index to .csv file"""
        assert sep != variants_sep
        if output_file == None:
            output_file = f'{self.directory}{self.name} Vocabulary Index.csv'
        
        if concept_list == None:
            concept_list = sorted(list(self.cognate_sets.keys()))
        else:
            concept_list = sorted([c for c in concept_list if c in self.concepts])
            concept_list = sorted([c for c in self.cognate_sets.keys() 
                                   if c.split('_')[0] in concept_list])
        
        with open(output_file, 'w') as f:
            language_names = sorted([self.languages[lang].name for lang in self.languages])
            header = '\t'.join(['Gloss'] + language_names)
            f.write(f'{header}\n')
            
            for cognate_set_id in concept_list:
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
        for lang_pair in itertools.product(self.languages.values(), self.languages.values()):
            lang1, lang2 = lang_pair
            if lang1 != lang2:
                pair_mutual_coverage = len([concept for concept in concept_list 
                                            if concept in lang1.vocabulary 
                                            if concept in lang2.vocabulary])
                mutual_coverages[lang_pair] = pair_mutual_coverage
        avg_mutual_coverage = mean(mutual_coverages.values()) / len([c for c in concept_list 
                                                                     if c in self.concepts])
        
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
            output_file = f'{self.directory}{self.name}_phoneme_PMI.csv'
        
        l = list(self.languages.values())
        
        #Check whether phoneme PMI has been calculated already for this pair
        #If not, calculate it now
        checked = []
        for pair in itertools.product(l, l):
            lang1, lang2 = pair
            if (lang2, lang1) not in checked:
                    
                if len(lang1.phoneme_pmi[lang2]) == 0:
                    print(f'Calculating phoneme PMI for {lang1.name} and {lang2.name}...')
                    pmi = PhonemeCorrDetector(lang1, lang2).calc_phoneme_pmi(**kwargs)
                
        #Save calculated PMI values to file
        with open(output_file, 'w') as f:
            f.write('Language1,Phone1,Language2,Phone2,PMI\n')
            checked = []
            for pair in itertools.product(l, l):
                lang1, lang2 = pair
                if (lang2, lang1) not in checked:
                
                    #Retrieve the precalculated values
                    pmi = lang1.phoneme_pmi[lang2]
                        
                    #Save all segment pairs with non-zero PMI values to file
                    #Also skip extremely small decimals that are close to zero
                    for seg1 in pmi:
                        for seg2 in pmi[seg1]:
                            if abs(pmi[seg1][seg2]) > lang1.phonemes[seg1] * lang2.phonemes[seg2]:
                                f.write(f'{lang1.name},{seg1},{lang2.name},{seg2},{pmi[seg1][seg2]}\n')
                    
                    checked.append((lang1, lang2))
    
    def load_phoneme_pmi(self, pmi_file=None, excepted=[]):
        """Loads pre-calculated phoneme PMI values from file"""
        
        #Designate the default file name to search for if no alternative is provided
        if pmi_file == None:
            pmi_file = f'{self.directory}{self.name}_phoneme_PMI.csv'
        
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
            try:
                lang1 = self.languages[row['Language1']]
                lang2 = self.languages[row['Language2']]
                if (lang1 not in excepted) and (lang2 not in excepted):
                    phone1, phone2 = row['Phone1'], row['Phone2']
                    pmi_value = row['PMI']
                    lang1.phoneme_pmi[lang2][phone1][phone2] = pmi_value
                    lang2.phoneme_pmi[lang1][phone2][phone1] = pmi_value
            
            #Skip loaded PMI values for languages which are not in dataset
            except KeyError:
                pass
    
    
    def calculate_phoneme_surprisal(self, ngram_size=1, output_file=None, **kwargs):
        """Calculates phoneme surprisal for all language pairs in the dataset and saves
        the results to file"""
        
        #First ensure that phoneme PMI has been calculated and loaded
        self.load_phoneme_pmi()
        
        #Specify output file name if none is specified
        if output_file == None:
            output_file = f'{self.directory}{self.name}_phoneme_surprisal_{ngram_size}gram.csv'
        
        #Check whether phoneme surprisal has been calculated already for this pair
        for lang1 in self.languages.values():
            for lang2 in self.languages.values():
                    
                #If not, calculate it now
                if len(lang1.phoneme_surprisal[(lang2, ngram_size)]) == 0:
                    print(f'Calculating phoneme surprisal for {lang1.name} and {lang2.name}...')
                    phoneme_surprisal = PhonemeCorrDetector(lang1, lang2).calc_phoneme_surprisal(ngram_size=ngram_size, **kwargs)
                
        #Save calculated surprisal values to file
        with open(output_file, 'w') as f:
            f.write('Language1,Phone1,Language2,Phone2,Surprisal,OOV_Smoothed\n')
            for lang1 in self.languages.values():
                for lang2 in self.languages.values():
                        
                    phoneme_surprisal = lang1.phoneme_surprisal[(lang2, ngram_size)]
                        
                    #Save values
                    for seg1 in phoneme_surprisal:
                        
                        #Determine the smoothed value for unseen ("out of vocabulary") correspondences
                        #Check using a non-IPA character
                        non_IPA = '?'
                        oov_smoothed = phoneme_surprisal[seg1][non_IPA]
                        
                        #Then remove this character from the surprisal dictionary
                        del phoneme_surprisal[seg1][non_IPA]
                        
                        #Save values which are not equal to the OOV smoothed value
                        for seg2 in phoneme_surprisal[seg1]:
                            if phoneme_surprisal[seg1][seg2] != oov_smoothed:
                                f.write(f'{lang1.name},{" ".join(seg1)},{lang2.name},{seg2},{phoneme_surprisal[seg1][seg2]},{oov_smoothed}\n')

    
    def load_phoneme_surprisal(self, ngram_size=1, surprisal_file=None, excepted=[]):
        """Loads pre-calculated phoneme surprisal values from file"""
        
        #Designate the default file name to search for if no alternative is provided
        if surprisal_file == None:
            surprisal_file = f'{self.directory}{self.name}_phoneme_surprisal_{ngram_size}gram.csv'
        
        #Try to load the file of saved PMI values
        try:
            surprisal_data = pd.read_csv(surprisal_file)
            
        #If the file is not found, recalculate the surprisal values and save to 
        #a file with the specified name
        except FileNotFoundError:
            self.calculate_phoneme_surprisal(output_file=surprisal_file)
            surprisal_data = pd.read_csv(surprisal_file)
        
        #Iterate through the dataframe and save the surprisal values to the Language
        #class objects' phoneme_surprisal attribute
        for index, row in surprisal_data.iterrows():
            try:
                lang1 = self.languages[row['Language1']]
                lang2 = self.languages[row['Language2']]
                if (lang1 not in excepted) and (lang2 not in excepted):
                    phone1, phone2 = row['Phone1'], row['Phone2']
                    phone1 = tuple(phone1.split())
                    surprisal_value = row['Surprisal']
                    if phone1 not in lang1.phoneme_surprisal[(lang2, ngram_size)]:
                        oov_smoothed = row['OOV_Smoothed']
                        lang1.phoneme_surprisal[(lang2, ngram_size)][phone1] = defaultdict(lambda:oov_smoothed)
                    lang1.phoneme_surprisal[(lang2, ngram_size)][phone1][phone2] = surprisal_value
            
            #Skip loaded surprisal values for languages which are not in dataset
            except KeyError:
                pass
    
    def phonetic_diversity(self, ch_to_remove=[]):
        #diversity_scores = {}
        diversity_scores = defaultdict(lambda:[])
        for cognate_set in self.cognate_sets:
            concept = cognate_set.split('_')[0]
            forms = []
            for lang1 in self.cognate_sets[cognate_set]:
                forms.extend([strip_ch(w, ['(', ')']+ch_to_remove) for w in self.cognate_sets[cognate_set][lang1]])
            lf = len(forms)
            if lf > 1:
                #diversity_scores[cognate_set] = len(set(forms)) / lf
                diversity_scores[concept].append(len(set(forms)) / lf)
        
        for concept in diversity_scores:
            diversity_scores[concept] = mean(diversity_scores[concept])
        
        return mean(diversity_scores.values())
                    
        
        
    
    def cognate_set_dendrogram(self, cognate_id, 
                               dist_func, sim=True, 
                               combine_cognate_sets=True,
                               method='average',
                               title=None, save_directory=None,
                               **kwargs):
        if combine_cognate_sets == True:
            cognate_ids = [c for c in self.cognate_sets if c.split('_')[0] == cognate_id]
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
        concept_list = [concept for concept in concept_list 
                        if len(self.concepts[concept]) > 1]
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
        
        #Create code and store the result
        code = f'{self.name}_distfunc-{dist_func.__name__}_sim-{sim}_cutoff-{cutoff}'
        for key, value in kwargs.items():
            code += f'_{key}-{value}'
        self.clustered_cognates[code] = clustered_cognates
        self.write_cognate_index(clustered_cognates, os.path.join(self.directory, 'Cognates', f'{code}.cog'))

        return clustered_cognates
    
    def write_cognate_index(self, clustered_cognates, output_file,
                        sep='\t', variants_sep='~'):
        assert sep != variants_sep
        
        cognate_index = defaultdict(lambda:defaultdict(lambda:[]))
        languages = []
        for concept in clustered_cognates:
            for i in clustered_cognates[concept]:
                cognate_id = f'{concept}_{i}'
                for entry in clustered_cognates[concept][i]:
                    lang, word = entry[:-1].split(' /')
                    cognate_index[cognate_id][lang].append(word)
                    languages.append(lang)
        languages = sorted(list(set(languages)))
        
        with open(output_file, 'w') as f:
            header = '\t'.join(['']+languages)
            f.write(header)
            f.write('\n')
            for cognate_id in cognate_index:
                line = [cognate_id]
                for lang in languages:
                    entry = '~'.join(cognate_index[cognate_id][lang])
                    line.append(entry)
                line = sep.join(line)
                f.write(f'{line}\n')
                
    def load_cognate_index(self, index_file, sep='\t', variants_sep='~'):
        assert sep != variants_sep
        index = defaultdict(lambda:defaultdict(lambda:[]))
        with open(index_file, 'r') as f:
            f = f.readlines()
            doculects = [name.strip() for name in f[0].split(sep)[1:]]
            for line in f[1:]:
                line = line.split(sep)
                cognate_id = line[0].rsplit('_', maxsplit=1)
                #print(cognate_id, line[0].rsplit('_', maxsplit=1))
                try:
                    gloss, cognate_class = cognate_id
                except ValueError:
                    gloss, cognate_class = cognate_id, '' #confirm that this is correct
                for lang, form in zip(doculects, line[1:]):
                    forms = form.split(variants_sep)
                    for form_i in forms:
                        form_i = form_i.strip()
                        
                        #Verify that all characters used in transcriptions are recognized
                        unk_ch = verify_charset(form_i)
                        if len(unk_ch) > 0:
                            unk_ch_s = '< ' + ' '.join(unk_ch) + ' >'
                            print(f'Unable to parse characters {unk_ch_s} in {lang} /{form_i}/ "{gloss}"!')
                            raise ValueError
                        if len(form_i.strip()) > 0:
                            index[gloss][cognate_class].append(f'{lang} /{form_i}/')   
        
        return index


    def load_clustered_cognates(self, **kwargs):
        cwd = os.getcwd()
        os.chdir(os.path.join(self.directory, 'Cognates'))
        cognate_files = glob.glob('*.cog')
        for cognate_file in cognate_files:
            code = cognate_file.rsplit('.', maxsplit=1)[0]
            self.clustered_cognates[code] = self.load_cognate_index(cognate_file, **kwargs)
        n = len(cognate_files)
        s = f'Loaded {n} cognate'
        if n > 1 or n < 1:
            s += ' indices.'
        else:
            s += ' index.'
        print(s)
        os.chdir(cwd)
            
        
                
    def write_BEASTling_input(self, clustered_cognates, 
                              name, directory,
                              log_params=False,
                              chainlength=2000000,
                              model='covarion',
                              rate_variation=True,
                              clock_model='relaxed',
                              calibration=None,
                              sep=','):
        """Writes a CSV file suitable as input for BEASTling from a 
        clustered cognate set using specified parameters.
        This can then be fed into BEASTling to create an .xml file to run
        in BEAST2 for Bayesian phylogenetic inference.
        
        calibration :   dictionary with comma-separated language names (strings) as keys,
                        values as range of millennia, e.g. '1.4-1.6' for 1400-1600 years
        """
        
        csv_file = directory + name + '.csv'
        config_file = directory + name + '.conf'
        
        cognate_id_count = 0
        with open(csv_file, 'w') as f:
            header = sep.join(['Language_ID', 'Feature_ID', 'IPA', 'Value'])
            f.write(f'{header}\n')
            for concept in clustered_cognates:
                cognate_ids = list(clustered_cognates[concept].keys())
                for i in range(len(cognate_ids)):
                    cognate_id = cognate_ids[i]
                    for entry in clustered_cognates[concept][cognate_id]:
                        lang, word = entry[:-1].split(' /')
                        lang = re.sub('\s', '_', lang)
                        line = sep.join([lang, concept, word, str(i+1+cognate_id_count)])
                        f.write(f'{line}\n')
                cognate_id_count += len(cognate_ids)
        
        with open(config_file, 'w') as f:
            config = '\n'.join([f'[admin]',
                                f'basename={name}',
                                f'log_params={log_params}',
                                f'[MCMC]',
                                f'chainlength={chainlength}',
                                f'[model {name}]',
                                f'model={model}',
                                f'data={name}.csv',
                                f'rate_variation={rate_variation}'])
            if clock_model != None:
                config += f'\n[clock default]\ntype={clock_model}'
            
            if calibration != None:
                config += '\n[calibration]'
                for lang_group in calibration:
                    config += f'\n{lang_group}={calibration[lang_group]}'
                
            f.write(config)
        
        print(f'Wrote BEASTling input to {directory}.')
                
    
    def evaluate_clusters(self, clustered_cognates, method='bcubed'):
        """Evaluates B-cubed precision, recall, and F1 of results of automatic  
        cognate clustering against dataset's gold cognate classes"""
        
        precision_scores, recall_scores, f1_scores, mcc_scores = {}, {}, {}, {}
        ch_to_remove = list(suprasegmental_diacritics) + ['??', '??', ' ', '(', ')']
        for concept in clustered_cognates:
            #print(concept)
            clusters = {'/'.join([strip_diacritics(unidecode.unidecode(item.split('/')[0])), 
                                  strip_ch(item.split('/')[1], ch_to_remove)])+'/':set([i]) for i in clustered_cognates[concept] 
                        for item in clustered_cognates[concept][i]}
            
            gold_clusters = {f'{strip_diacritics(unidecode.unidecode(lang))} /{strip_ch(tr, ch_to_remove)}/':set([c]) 
                             for c in self.cognate_sets 
                             if re.split('[-|_]', c)[0] == concept 
                             for lang in self.cognate_sets[c] 
                             for tr in self.cognate_sets[c][lang]}
            
            #Skip concepts without any gold cognate class information
            if len(gold_clusters) == 0:
                continue
            
            if method == 'bcubed':
            
                precision = bcubed.precision(clusters, gold_clusters)
                recall = bcubed.recall(clusters, gold_clusters)
                fscore = bcubed.fscore(precision, recall)
                precision_scores[concept] = precision
                recall_scores[concept] = recall
                f1_scores[concept] = fscore
                
            elif method == 'mcc':                
                pairs = [(item1, item2) for item1 in gold_clusters for item2 in gold_clusters if item1 != item2]
                results = []
                for pair in pairs:
                    w1, w2 = pair
                    gold_value = gold_clusters[w1] == gold_clusters[w2]
                    test_value = clusters[w1] == clusters[w2]
                    results.append((gold_value, test_value))
                    
                TP = results.count((True, True))
                FP = results.count((False, True))
                TN = results.count((False, False))
                FN = results.count((True, False))
                num = (TP * TN) - (FP * FN)
                dem = math.sqrt((TP+FP)*(TP+FN)*(TN+FP)*(TN+FN))
                try:
                    mcc = num/dem
                except ZeroDivisionError:
                    mcc = 0
                mcc_scores[concept] = mcc
                
            else:
                print(f'Error: Method "{method}" not recognized for cluster evaluation!')
                raise ValueError
        if method == 'bcubed':
            return mean(precision_scores.values()), mean(recall_scores.values()), mean(f1_scores.values())
        elif method == 'mcc':
            return mean(mcc_scores.values())
    
    def distance_matrix(self, dist_func, sim, 
                        concept_list=None,
                        cluster_func=None, cluster_sim=None, cutoff=None, 
                        cognates='auto',
                        **kwargs):
        
        #Try to skip re-calculation of distance matrix by retrieving
        #a previously computed distance matrix by its code
        code = f'cognates-{cognates}_distfunc-{dist_func.__name__}_sim-{sim}_cutoff-{cutoff}'
        for key, value in kwargs.items():
            #if type(value) == function:
            #    value = value.__name__
            code += f'_{key}-{value}'
        #doesn't yet account for concept_list ID
        
        if code in self.distance_matrices:
            return self.distance_matrices[code]
        
        #Use all available concepts by default
        if concept_list == None:
            concept_list = sorted([concept for concept in self.concepts.keys() 
                                   if len(self.concepts[concept]) > 1])
        else:
            concept_list = sorted([concept for concept in concept_list 
                                   if len(self.concepts[concept]) > 1])
        
        if dist_func == Z_score_dist:
            cognates = 'none'
        #Automatic cognate clustering        
        if cognates == 'auto':
            assert cluster_func != None
            assert cluster_sim != None
            assert cutoff != None
            
            cognate_code = f'{self.name}_distfunc-{cluster_func.__name__}_sim-{sim}_cutoff-{cutoff}'
            #for key, value in kwargs.items():
            #    code += f'_{key}-{value}'
            if cognate_code in self.clustered_cognates:
                clustered_concepts = self.clustered_cognates[cognate_code]
            else:
                print('Clustering cognates...')
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
        
        languages = [self.languages[lang] for lang in self.languages]
        names = [lang.name for lang in languages]
        
        #Compute distance matrix
        dm = distance_matrix(group=languages, labels=names, 
                             dist_func=dist_func, sim=sim,
                             clustered_cognates=clustered_concepts,
                             **kwargs)
        
        #Store computed distance matrix
        self.distance_matrices[code] = dm
        
        return dm
    
    
    def linkage_matrix(self, dist_func, sim, 
                       concept_list=None, 
                       cluster_func=None, cluster_sim=None, cutoff=None, 
                       cognates='auto',
                       method='average', metric='euclidean',
                       **kwargs):
        dm = self.distance_matrix(dist_func, sim, 
                                  concept_list, 
                                  cluster_func, cluster_sim, cutoff, 
                                  cognates, 
                                  **kwargs)
        dists = squareform(dm)
        lm = linkage(dists, method, metric)
        return lm    
    
    
    def draw_tree(self, 
                  dist_func, sim, concept_list=None,                  
                  cluster_func=None, cluster_sim=None, cutoff=None,
                  cognates='auto', 
                  method='average', metric='euclidean',
                  title=None, save_directory=None,
                  return_newick=False,
                  orientation='left', p=30,
                  **kwargs):
        
        group = [self.languages[lang] for lang in self.languages]
        labels = [lang.name for lang in group]
        if title == None:
            title = f'{self.name}'
        if save_directory == None:
            save_directory = self.directory + 'Plots/'
            
        lm = self.linkage_matrix(dist_func, sim, 
                                 concept_list, 
                                 cluster_func, cluster_sim, cutoff, 
                                 cognates, method, metric, 
                                 **kwargs)
        
        sns.set(font_scale=1.0)
        if len(group) >= 100:
            plt.figure(figsize=(20,20))
        elif len(group) >= 60:
            plt.figure(figsize=(10,10))
        else:
            plt.figure(figsize=(10,8))
        
        dendrogram(lm, p=p, orientation=orientation, labels=labels)
        if title != None:
            plt.title(title, fontsize=30)
        plt.savefig(f'{save_directory}{title}.png', bbox_inches='tight', dpi=300)
        plt.show()
        if return_newick == True:
            return linkage2newick(lm, labels)


    def plot_languages(self, 
                       dist_func, sim, concept_list=None, 
                       cluster_func=None, cluster_sim=None, cutoff=None, 
                       cognates='auto', 
                       dimensions=2, top_connections=0.3, max_dist=1, alpha_func=None,
                       plotsize=None, invert_xaxis=False, invert_yaxis=False,
                       title=None, save_directory=None, 
                       **kwargs):
        
        #Get lists of language objects and their labels
        group = [self.languages[lang] for lang in self.languages]
        labels = [lang.name for lang in group]
        
        #Compute a distance matrix
        dm = self.distance_matrix(dist_func=dist_func, sim=sim, concept_list=concept_list, 
                                  cluster_func=cluster_func, cluster_sim=cluster_sim, 
                                  cutoff=cutoff, cognates=cognates,
                                  **kwargs)
        
        #Use MDS to compute coordinate embeddings from distance matrix
        coords = dm2coords(dm, dimensions)
        
        #Set the plot dimensions
        sns.set(font_scale=1.0)
        if plotsize == None:
            x_coords = [coords[i][0] for i in range(len(coords))]
            y_coords = [coords[i][1] for i in range(len(coords))]
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            y_ratio = y_range / x_range
            n = max(10, round((len(group)/10)*2))
            plotsize = (n, n*y_ratio)
        plt.figure(figsize=plotsize)
        
        #Draw scatterplot points
        plt.scatter(
            coords[:, 0], coords[:, 1], marker = 'o'
            )
        
        #Add labels to points
        for label, x, y in zip(labels, coords[:, 0], coords[:, 1]):
            plt.annotate(
                label,
                xy = (x, y), xytext = (5, -5),
                textcoords = 'offset points', ha = 'left', va = 'bottom',
                )
        
        #Add lines connecting points with a distance under a certain threshold
        connected = []
        for i in range(len(coords)):
            for j in range(len(coords)):
                if (j, i) not in connected:
                    dist = dm[i][j]
                    if dist <= max_dist:
                        #if dist <= np.mean(dm[i]): #if the distance is lower than average
                        if dist in np.sort(dm[i])[1:round(top_connections*(len(dm)-1))]:
                            coords1, coords2 = coords[i], coords[j]
                            x1, y1 = coords1
                            x2, y2 = coords2
                            if alpha_func == None:
                                plt.plot([x1, x2],[y1, y2], alpha=1-dist)
                            else:
                                plt.plot([x1, x2],[y1, y2], alpha=alpha_func(dist))
                            connected.append((i,j))
        
        #Optionally invert axes
        if invert_yaxis == True:    
            plt.gca().invert_yaxis()
        if invert_xaxis == True:
            plt.gca().invert_xaxis()
            
        #Save the plot
        if title == None:
            title = f'{self.name} plot'
            if save_directory == None:
                save_directory = os.path.join(self.directory, 'Plots/')
            plt.savefig(f'{os.path.join(save_directory, title)}.png', bbox_inches='tight', dpi=300)
        
        #Show the figure
        plt.show()
        plt.close()
    
    def draw_network(self, 
                  dist_func, sim, concept_list=None,                  
                  cluster_func=None, cluster_sim=None, cutoff=None,
                  cognates='auto', method='spring',
                  title=None, save_directory=None,
                  network_function=newer_network_plot,
                  **kwargs):
        
        #Use all available concepts by default
        if concept_list == None:
            concept_list = sorted([concept for concept in self.concepts.keys() 
                                   if len(self.concepts[concept]) > 1])
        else:
            concept_list = sorted([concept for concept in concept_list 
                                   if len(self.concepts[concept]) > 1])
        
        if dist_func == Z_score_dist:
            cognates = 'none'
        #Automatic cognate clustering        
        if cognates == 'auto':
            assert cluster_func != None
            assert cluster_sim != None
            assert cutoff != None
            
            code = f'{self.name}_distfunc-{cluster_func.__name__}_sim-{sim}_cutoff-{cutoff}'
            #for key, value in kwargs.items():
            #    code += f'_{key}-{value}'
            if code in self.clustered_cognates:
                clustered_concepts = self.clustered_cognates[code]
            else:
                print('Clustering cognates...')
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
            title = f'{self.name} network'
        if save_directory == None:
            save_directory = self.directory + 'Plots/'
        
        return network_function(group=languages, 
                            labels=names, 
                            dist_func=dist_func,
                            sim=sim,
                            method=method,
                            title=title,
                            save_directory=save_directory,
                            clustered_cognates=clustered_concepts,
                            **kwargs)
    
    
    def examine_cognates(self, language_list=None, concepts=None, cognate_sets=None,
                         min_langs=2):
        if language_list == None:
            language_list = list(self.languages.values())
        
        if (concepts == None) and (cognate_sets == None):
            cognate_sets = sorted(list(self.cognate_sets.keys()))
        
        elif concepts != None:
            cognate_sets = []
            for concept in concepts:
                cognate_sets.extend([c for c in self.cognate_sets if '_'.join(c.split('_')[:-1]) == concept])
        
        for cognate_set in cognate_sets:
            lang_count = [lang for lang in language_list if lang.name in self.cognate_sets[cognate_set]]
            if len(lang_count) >= min_langs:
                print(cognate_set)
                for lang in lang_count:
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
    
    def add_language(self, name, data_path, **kwargs):
        self.load_data(data_path, doculects=[name], **kwargs)

    def __str__(self):
        """Print a summary of the Family object"""
        s = f'{self.name.upper()}'
        s += f'\nLanguages: {len(self.languages)}'
        s += f'\nConcepts: {len(self.concepts)}\nCognate Classes: {len(self.cognate_sets)}'
        
        return s

#%%
class Language(LexicalDataset):
    def __init__(self, name, data, 
                 lang_id=None, glottocode=None, iso_code=None, family=None,
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
        self.ngrams = defaultdict(lambda:defaultdict(lambda:0))
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
        self.noncognate_thresholds = defaultdict(lambda:[])
        
    def create_vocabulary(self):
        #Remove stress and tone diacritics from segmented words; syllabic diacritics (above and below); spaces
        diacritics_to_remove = list(suprasegmental_diacritics) + ['??', '??', ' ']
        
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
        self.ngrams[1] = self.unigrams
        self.ngrams[2] = self.bigrams
        self.ngrams[3] = self.trigrams
        
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
    
    def list_ngrams(self, ngram_size):
        """Returns a dictionary of ngrams of a particular size, with their counts"""
        if len(self.ngrams[ngram_size]) > 0:
            return self.ngrams[ngram_size]
        
        else:
            segmented_words = [entry[2] for concept in self.vocabulary for entry in self.vocabulary[concept]]
            for segs in segmented_words:
                pad_n = ngram_size - 1
                padded = ['#']*pad_n + segs + ['#']*pad_n
                for i in range(len(padded)-pad_n):
                    ngram = tuple(padded[i:i+ngram_size])
                    self.ngrams[ngram_size][ngram] += 1
            return self.ngrams[ngram_size]
        
    
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
        ligatures = ['??', '??', '??', '??', '??', '??']
        double_ch = ['t??s', 'd??z', 't????', 'd????', 't????', 'd????']
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
    
    def self_surprisal(self, word, segmented=False, normalize=False):
        info_content = self.calculate_infocontent(word, segmented=segmented)
        if normalize == True:
            return mean(info_content[j][1] for j in info_content)
        else:
            return sum(info_content[j][1] for j in info_content)
    
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
                         similarity='weighted_dice', 
                         method='ward', 
                         exclude_length=True, exclude_tones=True,
                         title=None, save_directory=None,
                         **kwargs):
        if title == None:
            title = f'Phonetic Inventory of {self.name}'
        
        if save_directory == None:
            save_directory = self.family.directory + '/Plots/'
            
        phonemes = list(self.phonemes.keys())
        
        if exclude_length == True:
            phonemes = list(set(strip_ch(p, ['??']) for p in phonemes))
        
        if exclude_tones == True:
            phonemes = [p for p in phonemes if p not in self.tonemes]
        
        return draw_dendrogram(group=phonemes,
                               labels=phonemes, 
                               dist_func=phone_sim, 
                               sim=True, 
                               similarity=similarity, 
                               method=method, 
                               title=title, 
                               save_directory=save_directory, 
                               **kwargs)
    
    def __str__(self):
        """Print a summary of the language object"""
        s = f'{self.name.upper()} [{self.glottocode}][{self.iso_code}]'
        s += f'\nFamily: {self.family.name}'
        s += f'\nRelatives: {len(self.family.languages)}'
        s += f'\nConsonants: {len(self.consonants)}, Vowels: {len(self.vowels)}'
        if self.tonal == True:
            s += f', Tones: {len(self.tonemes)}'
        percent_loanwords = len([1 for concept in self.loanwords for entry in self.loanwords[concept]]) / len([1 for concept in self.vocabulary for entry in self.vocabulary[concept]])
        percent_loanwords *= 100
        if percent_loanwords > 0:
            s += f'\nLoanwords: {round(percent_loanwords, 1)}%'
            
        s += '\nExample Words:'
        for i in range(5):
            concept = random.choice(list(self.vocabulary.keys()))
            entry = random.choice(self.vocabulary[concept])
            orth, ipa, segs = entry
            s+= f'\n\t"{concept.upper()}": /{ipa}/'
            
        
        return s
    
#%%
#COMBINING DATASETS

def combine_datasets(dataset_list):
    pass

    

#%%
#LOAD COMMON CONCEPTS
common_concepts = pd.read_csv(str(parent_dir) + '/Datasets/Concepts/common_concepts.csv', sep='\t')
common_concepts = set(concept 
                      for i, row in common_concepts.iterrows() 
                      for concept in row['Alternate_Labels'].split('; '))

#LOAD FAMILIES AND WRITE VOCABULARY INDEX FILES
datasets_path = str(parent_dir) + '/Datasets/'
os.chdir(datasets_path)
families = {}

def load_family(family):
    family_path = re.sub('-', '_', family).lower()
    filepath = datasets_path + family + f'/{family_path}_data.csv'
    print(f'Loading {family}...')
    families[family] = LexicalDataset(filepath, family)
    #families[family].prune_languages(min_amc=0.75, concept_list=common_concepts)
    #families[family].write_vocab_index()
    language_variables = {format_as_variable(lang):families[family].languages[lang] 
                          for lang in families[family].languages}
    globals().update(language_variables)
    return families[family]
    

# for family in ['Arabic', 
#                'Balto-Slavic', 
#                'Bantu',
#                'Dravidian',
#                #'French',
#                'Germanic',
#                'Hellenic',
#                'Hokan',
#                'Italic',
#                'Japonic',
#                'Polynesian',
#                'Quechuan',
#                'Sinitic', 
#                'Turkic', 
#                'Uralic',
#                'Uto-Aztecan',
#                'Vietic'
#                ]:
#     family_path = re.sub('-', '_', family).lower()
#     filepath = datasets_path + family + f'/{family_path}_data.csv'
#     print(f'Loading {family}...')
#     families[family] = LexicalDataset(filepath, family)
#     #families[family].prune_languages(min_amc=0.75, concept_list=common_concepts)
#     #families[family].write_vocab_index()
#     language_variables = {format_as_variable(lang):families[family].languages[lang] 
#                           for lang in families[family].languages}
#     globals().update(language_variables)

#Add some commmonly used subsets
#families['Pomoan'] = families['Hokan'].subset('Pomoan', include=[lang for lang in families['Hokan'].languages if 'Pomo' in lang]+['Kashaya'])
#families['Yana'] = families['Hokan'].subset('Yana', include=['Northern Yana', 'Central Yana', 'Yahi'])
#families['Yuman'] = families['Hokan'].subset('Yuman', include=['Mohave', 'Yavapai', 'Tipai', 'Ipai', 'Cocopa'])

globals().update({format_as_variable(family):families[family] for family in families})
os.chdir(local_dir)

#Get lists and counts of languages/families
all_languages = [families[family].languages[lang] for family in families 
                 for lang in families[family].languages]
all_families = [families[family] for family in families]
total_languages = len(all_languages)
total_families = len(all_families)

