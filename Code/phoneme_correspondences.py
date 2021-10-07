import os, itertools, random
from auxiliary_functions import *
from phonetic_distance import *

class PhonemeCorrDetector:
    def __init__(self, lang1, lang2, wordlist=None):
        self.lang1 = lang1
        self.lang2 = lang2
        self.same_meaning, self.diff_meaning, self.loanwords = self.prepare_wordlists(wordlist)
        self.pmi_dict = self.lang1.phoneme_pmi[self.lang2]
        self.surprisal_dict = self.lang1.phoneme_surprisal[self.lang2]
    
    def prepare_wordlists(self, wordlist):
    
        #If no wordlist is provided, by default use all concepts shared by the two languages
        if wordlist == None:
            wordlist = [concept for concept in self.lang1.vocabulary 
                        if concept in self.lang2.vocabulary]
        
        #If a wordlist is provided, use only the concepts shared by both languages
        else:
            wordlist = [concept for concept in wordlist 
                        if concept in self.lang1.vocabulary 
                        if concept in self.lang2.vocabulary]
            
        #Get tuple (concept, orthography, IPA, segmented IPA) for each word entry
        l1_wordlist = [(concept, entry[0], entry[1], entry[2]) 
                       for concept in wordlist for entry in self.lang1.vocabulary[concept]]
        l2_wordlist = [(concept, entry[0], entry[1], entry[2]) 
                       for concept in wordlist for entry in self.lang2.vocabulary[concept]]
        
        #Get all combinations of L1 and L2 words
        all_wordpairs = itertools.product(l1_wordlist, l2_wordlist)
        
        #Sort out same-meaning from different-meaning word pairs, and loanwords
        same_meaning, diff_meaning, loanwords = [], [], []
        for pair in all_wordpairs:
            l1_entry, l2_entry = pair
            gloss1, gloss2 = l1_entry[0], l2_entry[0]
            if gloss1 == gloss2:
                if list(l1_entry[1:]) in self.lang1.loanwords[gloss1]:
                    loanwords.append(pair)
                elif list(l2_entry[1:]) in self.lang2.loanwords[gloss2]:
                    loanwords.append(pair)
                else:
                    same_meaning.append(pair)
            else:
                diff_meaning.append(pair)
        
        #Return a tuple of the three word type lists
        return same_meaning, diff_meaning, loanwords
    
    
    def align_wordlist(self, wordlist, 
                       align_function=phone_align, **kwargs):
        """Returns a list of the aligned segments from the wordlists"""
        return [align_function(pair[0][-1], pair[1][-1], **kwargs)
                for pair in wordlist]
    
    
    def correspondence_probs(self, alignment_list, ngram_size=1,
                             counts=False, exclude_null=True):
        """Returns a dictionary of conditional phone probabilities, based on a list
        of alignments.
        counts : Bool; if True, returns raw counts instead of normalized probabilities;
        exclude_null : Bool; if True, does not consider aligned pairs including a null segment"""
        corr_counts = defaultdict(lambda:defaultdict(lambda:0))
        for alignment in alignment_list:
            if exclude_null == True:
                alignment = [pair for pair in alignment if '-' not in pair]
            if ngram_size > 1:
                pad_n = ngram_size - 1
                alignment = [('#', '#')]*pad_n + alignment + [('#', '#')]*pad_n
                
            for i in range(ngram_size-1, len(alignment)):
                ngram = alignment[i-(ngram_size-1):i+1]
                segs = list(zip(*ngram))
                seg1, seg2 = segs
                corr_counts[seg1][seg2] += 1
        if counts == False:
            for seg1 in corr_counts:
                corr_counts[seg1] = normalize_dict(corr_counts[seg1])
        return corr_counts
    
    
    
    def radial_counts(self, wordlist, radius=2, normalize=True):
        """Checks the number of times that phones occur within a specified 
        radius of positions in their respective words from one another"""
        corr_dict = defaultdict(lambda:defaultdict(lambda:0))
        
        for item in wordlist:
            segs1, segs2 = item[0][3], item[1][3]
            for i in range(len(segs1)):
                seg1 = segs1[i]
                for j in range(max(0, i-radius), min(i+radius+1, len(segs2))):
                    seg2 = segs2[j]
                    
                    #Only count sounds which are compatible as corresponding
                    try:
                        if compatible_segments(seg1, seg2) == True:
                            corr_dict[seg1][seg2] += 1
                    except RecursionError:
                        print(seg1, seg2, item)
                        
        if normalize == True:
            for seg1 in corr_dict:
                corr_dict[seg1] = normalize_dict(corr_dict[seg1])
        
        return corr_dict
    

    def phoneme_pmi(self, dependent_probs, independent_probs=None):
        """
        dependent_probs : nested dictionary of conditional correspondence probabilities in potential cognates
        independent_probs : None, or nested dictionary of conditional correspondence probabilities in non-cognates
        """

        #If no independent probabilities are specified, 
        #use product of phoneme probabilities by default
        if independent_probs == None:
            independent_probs = defaultdict(lambda:defaultdict(lambda:0))
            for phoneme1 in self.lang1.phonemes:
                for phoneme2 in self.lang2.phonemes:
                    independent_probs[phoneme1][phoneme2] = self.lang1.phonemes[phoneme1] * self.lang2.phonemes[phoneme2]

        #Calculate joint probabilities from conditional probabilities
        for corr_dict in [dependent_probs, independent_probs]:
            for seg1 in corr_dict:
                seg1_totals = sum(corr_dict[seg1].values())
                if seg1_totals == 0:
                    print(seg1)
                for seg2 in corr_dict[seg1]:
                    cond_prob = corr_dict[seg1][seg2] / seg1_totals
                    joint_prob = cond_prob * self.lang1.phonemes[seg1]
                    corr_dict[seg1][seg2] = joint_prob
                    
        #Get set of all possible phoneme correspondences
        segment_pairs = set([(seg1, seg2)
                         for corr_dict in [dependent_probs, independent_probs]
                         for seg1 in corr_dict 
                         for seg2 in corr_dict[seg1]])
            
        #Calculate PMI for all phoneme pairs
        pmi_dict = defaultdict(lambda:defaultdict(lambda:0))
        for segment_pair in segment_pairs:
            seg1, seg2 = segment_pair
            p_ind = self.lang1.phonemes[seg1] * self.lang2.phonemes[seg2]
            cognate_prob = dependent_probs[seg1].get(seg2, p_ind)
            noncognate_prob = independent_probs[seg1].get(seg2, p_ind)
            pmi_dict[seg1][seg2] = math.log(cognate_prob/noncognate_prob)
        
        return pmi_dict


    def calc_phoneme_pmi(self, radius=2, max_iterations=10,
                          p_threshold=0.1,
                          seed=1, 
                          print_iterations=False, save=True):
        """
        Parameters
        ----------
        radius : int, optional
            Number of word positions forward and backward to check for initial correspondences. The default is 2.
        max_iterations : int, optional
            Maximum number of iterations. The default is 3.
        p_threshold : float, optional
            p-value threshold for words to qualify for PMI calculation in the next iteration. The default is 0.05.
        seed : int, optional
            Random seed for drawing a sample of different meaning word pairs. The default is 1.
        print_iterations : bool, optional
            Whether to print the results of each iteration. The default is False.
        save : bool, optional
            Whether to save the results to the Language class object's phoneme_pmi attribute. The default is True.

        Returns
        -------
        results : collections.defaultdict
            Nested dictionary of phoneme PMI values.

        """
        
        random.seed(seed)
        #Take a sample of different-meaning words, as large as the same-meaning set
        sample_size = len(self.same_meaning)
        diff_sample = random.sample(self.diff_meaning, min(sample_size, len(self.diff_meaning)))

        #First step: calculate probability of phones co-occuring within within 
        #a set radius of positions within their respective words
        synonyms_radius = self.radial_counts(self.same_meaning, radius)
        pmi_step1 = self.phoneme_pmi(dependent_probs=synonyms_radius)
    
        #At each following iteration N, re-align using the pmi_stepN as an 
        #additional penalty, and then recalculate PMI
        iteration = 0
        PMI_iterations = {iteration:pmi_step1}
        qualifying_words = default_dict({iteration:sorted(self.same_meaning)}, l=[])
        disqualified_words = default_dict({iteration:diff_sample}, l=[])
        while (iteration < max_iterations) and (qualifying_words[iteration] != qualifying_words[iteration-1]):
            iteration += 1
            
            #Align the qualifying and words of the previous step using previous step's PMI
            cognate_alignments = self.align_wordlist(qualifying_words[iteration-1], 
                                                     added_penalty_dict=PMI_iterations[iteration-1])
            
            #Align the sample of different meaning and non-qualifying words again using previous step's PMI
            noncognate_alignments = self.align_wordlist(disqualified_words[iteration-1],
                                                        added_penalty_dict=PMI_iterations[iteration-1])
            
            #Calculate correspondence probabilities and PMI values from these alignments
            cognate_probs = self.correspondence_probs(cognate_alignments)
            cognate_probs = default_dict({k[0]:{v[0]:cognate_probs[k][v] 
                                                for v in cognate_probs[k]} 
                                          for k in cognate_probs}, l=defaultdict(lambda:0))
            PMI_iterations[iteration] = self.phoneme_pmi(cognate_probs)#, noncognate_probs)
            
            #Align all same-meaning word pairs
            all_alignments = self.align_wordlist(self.same_meaning, 
                                                 added_penalty_dict=PMI_iterations[iteration-1])

            #Score PMI for different meaning words and words disqualified in previous iteration
            noncognate_PMI = []
            for alignment in noncognate_alignments:
                noncognate_PMI.append(mean([PMI_iterations[iteration][pair[0]][pair[1]] 
                                            for pair in alignment]))

            #Score same-meaning alignments for overall PMI and calculate p-value
            #against different-meaning alignments
            qualifying, disqualified = [], []
            for i in range(len(self.same_meaning)):
                alignment = all_alignments[i]
                item = self.same_meaning[i]
                PMI_score = mean([PMI_iterations[iteration][pair[0]][pair[1]] 
                                for pair in alignment])
                p_value = (len([score for score in noncognate_PMI if score >= PMI_score])+1) / (len(noncognate_PMI)+1)
                if p_value < p_threshold:
                    qualifying.append(item)
                else:
                    disqualified.append(item)
            qualifying_words[iteration] = sorted(qualifying)
            disqualified_words[iteration] = disqualified + diff_sample
            
            #Print results of this iteration
            if print_iterations == True:
                print(f'Iteration {iteration}')
                print(f'\tQualified: {len(qualifying)}')
                added = [item for item in qualifying_words[iteration]
                         if item not in qualifying_words[iteration-1]]
                for item in added:
                    word1, word2 = item[0][1], item[1][1]
                    ipa1, ipa2 = item[0][2], item[1][2]
                    print(f'\t\t{word1} /{ipa1}/ - {word2} /{ipa2}/')
                
                print(f'\tDisqualified: {len(disqualified)}')
                removed = [item for item in qualifying_words[iteration-1]
                         if item not in qualifying_words[iteration]]
                for item in removed:
                    word1, word2 = item[0][1], item[1][1]
                    ipa1, ipa2 = item[0][2], item[1][2]
                    print(f'\t\t{word1} /{ipa1}/ - {word2} /{ipa2}/')
                    
        #Return and save the final iteration's PMI results
        results = PMI_iterations[max(PMI_iterations.keys())]
        if save == True:
            self.lang1.phoneme_pmi[self.lang2] = results
            #self.lang1.phoneme_pmi[self.lang2]['thresholds'] = noncognate_PMI
        self.pmi_dict = results
        
        return results
    
    #REMOVE:
    def phoneme_pmi_thresholds(self, seed=1, **kwargs):
        """Returns a list of PMI scores for non-cognate words for use in 
        calculation of p-values"""
        
        #Retrieve or calculate phoneme PMI dictionary
        if self.lang2 not in self.lang1.phoneme_pmi:
            pmi_dict = self.calc_phoneme_pmi(**kwargs)
        
        else:
            pmi_dict = self.lang1.phoneme_pmi[self.lang2]
        
        random.seed(seed)
        #Take a sample of different-meaning words, as large as the same-meaning set
        sample_size = len(self.same_meaning)
        diff_sample = random.sample(self.diff_meaning, min(sample_size, len(self.diff_meaning)))
        
        #Align non-cognate (non-synonymous) words
        noncognate_alignments = self.align_wordlist(diff_sample, added_penalty_dict=pmi_dict)
        
        #Get PMI scores of alignments
        PMI_scores = [mean([pmi_dict[pair[0]][pair[1]] for pair in alignment]) 
                      for alignment in noncognate_alignments]
        
        return PMI_scores
        

    def phoneme_surprisal(self, correspondence_counts, ngram_size=1,
                              weights=None):
        #Interpolation smoothing
        if weights == None:
            weights = [1/ngram_size for i in range(ngram_size)]
        interpolation = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:0)))
        
        for i in range(ngram_size,0,-1):
            for ngram1 in correspondence_counts:
                for ngram2 in correspondence_counts[ngram1]:
                    #forward
                    #interpolation[i][ngram1[-i:]][ngram2[-1]] += correspondence_counts[ngram1][ngram2]
                    
                    #backward
                    interpolation[i][ngram1[:i]][ngram2[0]] += correspondence_counts[ngram1][ngram2]
        
        
        smoothed_surprisal = defaultdict(lambda:defaultdict(lambda:self.lang2.phoneme_entropy*ngram_size))
        for ngram1 in interpolation[ngram_size]:
            for ngram2 in self.lang2.phonemes:
                #forward
                # estimates = [interpolation[i][ngram1[-i:]][ngram2] / sum(interpolation[i][ngram1[-i:]].values())
                #              if i > 1 else lidstone_smoothing(x=interpolation[i][ngram1[-i:]][ngram2], 
                #                                               N=sum(interpolation[i][ngram1[-i:]].values()), 
                #                                               d = len(self.lang2.phonemes) + 1)  
                #              for i in range(ngram_size,0,-1)]
                
                #backward
                estimates = [interpolation[i][ngram1[:i]][ngram2] / sum(interpolation[i][ngram1[:i]].values())
                             if i > 1 else lidstone_smoothing(x=interpolation[i][ngram1[:i]][ngram2], 
                                                              N=sum(interpolation[i][ngram1[:i]].values()), 
                                                              d = len(self.lang2.phonemes) + 1)  
                             for i in range(ngram_size,0,-1)]
                

                smoothed = sum([estimate*weight for estimate, weight in zip(estimates, weights)])
                smoothed_surprisal[ngram1][ngram2] = surprisal(smoothed)
            smoothed_surprisal[ngram1] = default_dict(smoothed_surprisal[ngram1], l=max(smoothed_surprisal[ngram1].values()))
                
        return smoothed_surprisal
                
            
        #current status: I've gotten it to interpolate the seen ngram probabilities
        #now need to get it to work for OOV ngrams
        #e.g. given Spanish ('e', 'x'), x --> {'ʎ': 0.625, 'ʒ': 0.3125}
        #                   ('o', 'x'), x --> {'ʎ': 0.875} to Portuguese
        #       so, we need to calculate the probability that /x/ in ('o', 'x') bigram
        #       corresponds with something other than /ʎ/,
        #       i.e. if we want to estimate p(ʒ | ('o', 'x'))
        #       /ʒ/ has never been observed with the bigram ('o', 'x'), so back off 
        #       to lower-order ngram
        #       in this case, we observe the following counts: {'v': 1, 'ʎ': 6, 'ʒ': 1}
        #       but we also need to account for the case where /ʒ/ is not observed in the
        #       lower-order bigram either: Lidstone smoothing?
        
        
        #Also need to it work in both directions. Currently works only moving
        #forward/from left to right across the word, but I want it to work from
        #the back as well
        
        

    def old_phoneme_surprisal(self, correspondence_counts):
        """Calculates phoneme surprisal with Lidstone smoothing given a dictionary
        of raw phoneme correspondence counts"""
        
        #Dictionary of total occurrence of lang1 segments in alignments
        totals = {seg1:sum(correspondence_counts[seg1].values()) 
                  for seg1 in correspondence_counts}
        
        #Calculate d parameter for Lidstone smoothing as the number of 
        #phonemes in lang2, plus 1 for the gap character
        d = len(self.lang2.phonemes) + 1
        
        #Calculate surprisal with Lidstone smoothing
        surprisal_values = {seg1:{seg2:surprisal(lidstone_smoothing(x=correspondence_counts[seg1].get(seg2, 0), 
                                                                    N=totals[seg1], 
                                                                    d=d)) 
                                                 for seg2 in correspondence_counts[seg1]} 
                                                 for seg1 in correspondence_counts}
        
        #Set the default value of each nested dictionary as the Lidstone smoothed
        #surprisal value for 0 occurrences
        for seg1 in surprisal_values:
            surprisal_values[seg1] = default_dict(surprisal_values[seg1],
                                                  l=surprisal(lidstone_smoothing(x=0, 
                                                                                 N=totals[seg1], 
                                                                                 d=d)))
        surprisal_values = default_dict(surprisal_values, l=defaultdict(lambda:self.lang2.phoneme_entropy))
        return surprisal_values
    
    
    def calc_phoneme_surprisal(self, radius=2, 
                               max_iterations=10, 
                               p_threshold=0.1,
                               ngram_size=1,
                               print_iterations=False,
                               seed=1,
                               save=True):
        #METHOD
        #1) Calculate phoneme PMI
        #2) Use phoneme PMI to align 
        #3) Iterate
        
        random.seed(seed)
        #Take a sample of different-meaning words, as large as the same-meaning set
        sample_size = len(self.same_meaning)
        diff_sample = random.sample(self.diff_meaning, min(sample_size, len(self.diff_meaning)))
        
        #Calculate phoneme PMI if not already done, for alignment purposes
        if len(self.pmi_dict) == 0:
            self.pmi_dict = self.calc_phoneme_pmi(radius=radius, 
                                                  max_iterations=max_iterations, 
                                                  p_threshold=p_threshold, 
                                                  seed=seed)
        
        #Align same-meaning and different meaning word pairs using PMI values: 
        #the alignments will remain the same throughout iteration
        same_meaning_alignments = self.align_wordlist(self.same_meaning,
                                                      added_penalty_dict=self.pmi_dict)
        diff_meaning_alignments = self.align_wordlist(diff_sample,
                                                      added_penalty_dict=self.pmi_dict)
        
        #At each iteration, re-calculate surprisal for qualifying and disqualified pairs
        #Then test each same-meaning word pair to see if if it meets the qualifying threshold
        iteration = 0
        surprisal_iterations = {}
        qualifying_words = default_dict({iteration:list(range(len(same_meaning_alignments)))}, l=[])
        disqualified_words = defaultdict(lambda:[])
        while (iteration < max_iterations) and (qualifying_words[iteration] != qualifying_words[iteration-1]):
            iteration += 1
            
            #Calculate surprisal from the qualifying alignments of the previous iteration
            cognate_alignments = [same_meaning_alignments[i] for i in qualifying_words[iteration-1]]
            surprisal_iterations[iteration] = self.phoneme_surprisal(self.correspondence_probs(cognate_alignments,
                                                                                               counts=True,
                                                                                               exclude_null=False,
                                                                                               ngram_size=ngram_size), 
                                                                     ngram_size=ngram_size)
            #Retrieve the alignments of different-meaning and disqualified word pairs
            #and calculate adaptation surprisal for them using new surprisal values
            noncognate_alignments = diff_meaning_alignments + [same_meaning_alignments[i]
                                                               for i in disqualified_words[iteration-1]]
            noncognate_surprisal = [adaptation_surprisal(alignment, 
                                                         surprisal_dict=surprisal_iterations[iteration], 
                                                         normalize=True,
                                                         ngram_size=ngram_size) 
                                    for alignment in noncognate_alignments]

            #Score same-meaning alignments for surprisal and calculate p-value
            #against different-meaning alignments
            qualifying, disqualified = [], []
            for i in range(len(self.same_meaning)):
                alignment = same_meaning_alignments[i]
                item = self.same_meaning[i]
                surprisal_score = adaptation_surprisal(alignment, 
                                                       surprisal_dict=surprisal_iterations[iteration], 
                                                       normalize=True,
                                                       ngram_size=ngram_size)
                p_value = (len([score for score in noncognate_surprisal if score <= surprisal_score])+1) / (len(noncognate_surprisal)+1)
                if p_value < p_threshold:
                    qualifying.append(i)
                else:
                    disqualified.append(i)
            qualifying_words[iteration] = qualifying
            disqualified_words[iteration] = disqualified
            
            #Print results of this iteration
            if print_iterations == True:
                print(f'Iteration {iteration}')
                print(f'\tQualified: {len(qualifying)}')
                added = [self.same_meaning[i] for i in qualifying_words[iteration]
                         if i not in qualifying_words[iteration-1]]
                for item in added:
                    word1, word2 = item[0][1], item[1][1]
                    ipa1, ipa2 = item[0][2], item[1][2]
                    print(f'\t\t{word1} /{ipa1}/ - {word2} /{ipa2}/')
                
                print(f'\tDisqualified: {len(disqualified)}')
                removed = [self.same_meaning[i] for i in qualifying_words[iteration-1] 
                           if i not in qualifying_words[iteration]]
                for item in removed:
                    word1, word2 = item[0][1], item[1][1]
                    ipa1, ipa2 = item[0][2], item[1][2]
                    print(f'\t\t{word1} /{ipa1}/ - {word2} /{ipa2}/')
        
        #Return and save the final iteration's surprisal results
        results = surprisal_iterations[iteration]
        if save == True:
            self.lang1.phoneme_surprisal[self.lang2] = results
        self.surprisal_dict = results
        
        return results
            
