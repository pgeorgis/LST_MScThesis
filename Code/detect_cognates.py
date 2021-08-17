import os, itertools, random
from auxiliary_functions import *
from load_languages import *


def lidstone_smoothing(x, N, d, alpha=0.3):
    """Given x (unsmoothed counts), N (total observations), 
    and d (number of possible outcomes), returns smoothed Lidstone probability"""
    return (x + alpha) / (N + (alpha*d))

def word_adaptation_surprisal(alignment, corr_counts, d,
                              alpha=0.03, normalize=True):
    """Calculates the WAS of a word pair alignment.
    corr_counts : nested dictionary of phoneme correspondence raw counts
    d : integer length of L2 alphabet (number of L2 phones)
    alpha : Lidstone smoothing parameter
    normalize : if True, normalizes the WAS by the length of the alignment"""
    surprisal_score = 0
    for pair in alignment:
        seg1, seg2 = pair[0], pair[1]
        joint_count = corr_counts[seg1].get(seg2, 0)
        lidstone_cond_p = (joint_count + alpha) / (sum(corr_counts[seg1].values()) + (alpha * d))
        surprisal_score += surprisal(lidstone_cond_p)
    if normalize == True:
        surprisal_score /= len(alignment)
    return surprisal_score
    

class CognateDetector:
    def __init__(self, lang1, lang2, wordlist=None):
        self.lang1 = lang1
        self.lang2 = lang2
        self.same_meaning, self.diff_meaning, self.loanwords = self.prepare_wordlists(wordlist)
        
    
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
    
    
    def correspondence_probs(self, alignment_list, 
                             counts=False, exclude_null=True):
        """Returns a dictionary of conditional phone probabilities, based on a list
        of alignments.
        counts : Bool; if True, returns raw counts instead of normalized probabilities;
        exclude_null : Bool; if True, does not consider aligned pairs including a null segment"""
        corr_counts = defaultdict(lambda:defaultdict(lambda:0))
        for alignment in alignment_list:
            if exclude_null == True:
                alignment = [pair for pair in alignment if '-' not in pair]
            for pair in alignment:
                seg1, seg2 = pair[0], pair[1]
                corr_counts[seg1][seg2] += 1
        if counts == False:
            for seg1 in corr_counts:
                corr_counts[seg1] = normalize_dict(corr_counts[seg1])
        return corr_counts
    
    
    def train(self, method,
              max_iterations=5,
              seed=1, sample_size=None, p_threshold=0.05):
        #the evaluation functions should all be either similarity or distances
        
        #Set random seed
        random.seed(seed)
        
        #Sample N different meaning pairs
        #If no sample size is specified, as many different meaning pairs as
        #same meaning pairs will be sampled by default
        if sample_size == None:
            sample_size = len(self.same_meaning)
        diff_sample = random.sample(self.diff_meaning, min(sample_size, len(self.diff_meaning)))
        diff_len = len(diff_sample)
        
        #Get alignments of same and different meaning word pairs
        same_alignments, diff_alignments, loan_alignments = map(self.align_wordlist, 
                                                                [self.same_meaning,
                                                                 diff_sample,
                                                                 self.loanwords])
        
        #Begin iteration: continue iterating until either the maximum number of 
        #iterations has been reached, or the set of identified cognates stops changing
        iteration = 0
        identified_cognates, identified_noncognates = defaultdict(lambda:[]), defaultdict(lambda:[])
        identified_cognates[iteration] = sorted(self.same_meaning+self.loanwords)
        while iteration < max_iterations:
            if ((iteration == 0) or (identified_cognates[iteration] != identified_cognates[iteration-1])):
                iteration += 1
                #Perform any prerequisite steps, depending on the detection method
                #e.g. (re)calculate PMI, correspondence probabilities, etc.
                #Calculate scores for different meaning alignments
                if method == 'surprisal':
                    same_corrs = self.correspondence_probs(self.align_wordlist(identified_cognates[iteration-1]), 
                                                           counts=True, exclude_null=False)
                    diff_scores = [word_adaptation_surprisal(alignment, same_corrs, 
                                                             d=len(self.lang2.phonemes))
                                   for alignment in diff_alignments]
                    
                elif method == 'PMI':
                    pass
                
                elif method == 'phonetic':
                    diff_scores = [1-word_sim(alignment) for alignment in diff_alignments]
                
                #Determine cognacy among same-meaning pairs
                for words, alignment in zip(self.same_meaning, same_alignments):
                    
                    #Calculate alignment score according to method
                    if method == 'surprisal':
                        score = word_adaptation_surprisal(alignment, same_corrs, d=len(self.lang2.phonemes))
                    
                    elif method == 'phonetic':
                        score = 1-word_sim(alignment)
                    
                    p_value = len([diff_score for diff_score in diff_scores if diff_score <= score]) / diff_len
                    if (p_value <= p_threshold):
                        identified_cognates[iteration].append(words)
                    else:
                        identified_noncognates[iteration].append(words)
                
                identified_noncognates[iteration].sort()
            
            else:
                break
            
        return identified_cognates[iteration], identified_noncognates[iteration]
        
        
        
    
    def is_cognate(self, word1, word2):
        pass
    
        
def detect_cognates(lang1, lang2, p_threshold=0.01, method='surprisal'):
    CD = CognateDetector(lang1, lang2)
    return CD.train(method=method, p_threshold=p_threshold)

def binary_cognate_sim(lang1, lang2, **kwargs):
    cognates, noncognates = detect_cognates(lang1, lang2, **kwargs)
    cognate_concepts = set(cognates[i][0][0] for i in range(len(cognates)))
    noncognate_concepts = set(noncognates[i][0][0] for i in range(len(noncognates)))
    noncognate_concepts = set(concept for concept in noncognate_concepts 
                              if concept not in cognate_concepts)
    
    return len(cognate_concepts) / (len(cognate_concepts) + len(noncognate_concepts))

def phonetic_cognate_sim(lang1, lang2, **kwargs):
    cognates, noncognates = detect_cognates(lang1, lang2, **kwargs)
    cognate_concepts = set(cognates[i][0][0] for i in range(len(cognates)))
    noncognate_concepts = set(noncognates[i][0][0] for i in range(len(noncognates)))
    noncognate_concepts = set(concept for concept in noncognate_concepts 
                              if concept not in cognate_concepts)
    
    concept_scores = {}
    for concept in noncognate_concepts:
        concept_scores[concept] = 0
    for concept in cognate_concepts:
        entries = [entry for entry in cognates if entry[0][0] == concept]
        entry_scores = {}
        for i in range(len(entries)):
            entry = entries[i]
            segs1, segs2 = entry[0][-1], entry[1][-1]
            alignment = phone_align(segs1, segs2, segmented=True)
            phone_score = word_sim(alignment)
            entry_scores[i] = phone_score
        concept_scores[concept] = max(entry_scores.values())
    return mean(concept_scores.values())
    
surprisal_cognate_dists = {}
def surprisal_cognate_dist(lang1, lang2, p_threshold=0.01, method='surprisal'):
    if (lang1, lang2) in surprisal_cognate_dists:
        return surprisal_cognate_dists[(lang1, lang2)]
    
    CD = CognateDetector(lang1, lang2)
    cognates, noncognates = CD.train(method=method, p_threshold=p_threshold)
    cognate_corrs = CD.correspondence_probs(CD.align_wordlist(cognates), counts=True, exclude_null=False)
    
    cognate_concepts = set(cognates[i][0][0] for i in range(len(cognates)))
    noncognate_concepts = set(noncognates[i][0][0] for i in range(len(noncognates)))
    noncognate_concepts = set(concept for concept in noncognate_concepts 
                              if concept not in cognate_concepts)
    
    concept_scores = {}
    for concept in noncognate_concepts:
        concept_scores[concept] = lang2.phoneme_entropy #correct?
    for concept in cognate_concepts:
        entries = [entry for entry in cognates if entry[0][0] == concept]
        entry_scores = {}
        for i in range(len(entries)):
            entry = entries[i]
            segs1, segs2 = entry[0][-1], entry[1][-1]
            alignment = phone_align(segs1, segs2, segmented=True)
            WAS_score = word_adaptation_surprisal(alignment, cognate_corrs, d=len(lang2.phonemes))
            entry_scores[i] = WAS_score
        concept_scores[concept] = min(entry_scores.values())
    
    
    surprisal_cognate_dist_score = mean(concept_scores.values())
    surprisal_cognate_dists[(lang1, lang2)] = surprisal_cognate_dist_score
    #surprisal_cognate_dists[(lang2, lang1)] = surprisal_cognate_dist_score
    
    return surprisal_cognate_dist_score

def surprisal_cognate_dist_mut(lang1, lang2):
    return mean([surprisal_cognate_dist(lang1, lang2), surprisal_cognate_dist(lang2, lang1)])
    


lexiphon_sims = {}
def lexiphon_sim(lang1, lang2, cutoff=0): #word_sim
    
    if (lang1, lang2) in lexiphon_sims:
        return lexiphon_sims[(lang1, lang2)]
    
    sims = {}
    for concept in lang1.vocabulary:
        if concept in lang2.vocabulary:
            scores = {}
            for entry1 in lang1.vocabulary[concept]:
                tr1 = entry1[1]
                for entry2 in lang2.vocabulary[concept]:
                    tr2 = entry2[1]
                    word_score = word_sim([tr1, tr2])
                    scores[(tr1, tr2)] = word_score
            max_score = max(scores.values())
            if max_score >= cutoff:
                sims[concept] = max_score
            else:
                sims[concept] = 0
    
    try:
        lexiphon_score = mean(sims.values())
        lexiphon_sims[(lang1, lang2)] = lexiphon_score
        lexiphon_sims[(lang2, lang1)] = lexiphon_score
        return lexiphon_score
    except StatisticsError:
        print(f'Error: {lang1.name}, {lang2.name}')    
    

def draw(group, sim_func, sim, method='average', **kwargs):
    draw_dendrogram(group=list(group.languages.values()),
                    dist_func=sim_func,
                    sim=sim,
                    labels=list(group.languages.keys()),
                    title=group.name,
                    method=method,
                    **kwargs)
        
    
