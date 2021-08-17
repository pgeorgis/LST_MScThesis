import os, itertools, random
from auxiliary_functions import normalize_dict
from phonetic_distance import *


class PhonemeCorrFinder:
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
    

    def phoneme_pmi(self, cognate_probs=None, noncognate_probs=None, seed=1):
        """cognate_probs and non_cognate probs should be dictionaries of
        conditional correspondence probabilities in potential cognates and noncognates"""
        #Reset phoneme PMI dictionary
        try:
            del self.lang1.phoneme_pmi[self.lang2]
        except KeyError:
            pass
        
        #Provide default correspondences if none are specified
        if cognate_probs == None:
            cognate_probs = self.correspondence_probs(self.align_wordlist(self.same_meaning))
        if noncognate_probs == None:
            random.seed(seed)
            sample_size = len(self.same_meaning)
            diff_sample = random.sample(self.diff_meaning, min(sample_size, len(self.diff_meaning)))
            noncognate_probs = self.correspondence_probs(self.align_wordlist(diff_sample))
        
        #Calculate joint probabilities from conditional probabilities
        l1_phonemes = list(self.lang1.phonemes.keys())
        for corr_dict in [cognate_probs, noncognate_probs]:
            for seg1 in corr_dict:
                seg1_totals = sum(corr_dict[seg1].values())
                for seg2 in corr_dict[seg1]:
                    cond_prob = corr_dict[seg1][seg2] / seg1_totals
                    joint_prob = cond_prob * self.lang1.phonemes[seg1]
                    corr_dict[seg1][seg2] = joint_prob
                    
        #Get set of all phoneme correspondences in cognates and non-cognates
        segment_pairs = set([(seg1, seg2)
                         for corr_dict in [cognate_probs, noncognate_probs]
                         for seg1 in corr_dict 
                         for seg2 in corr_dict[seg1]])
            
        #Calculate PMI for all phoneme pairs
        for segment_pair in segment_pairs:
            seg1, seg2 = segment_pair
            p_ind = self.lang1.phonemes[seg1] * self.lang2.phonemes[seg2]
            cognate_prob = cognate_probs[seg1].get(seg2, p_ind)
            noncognate_prob = noncognate_probs[seg1].get(seg2, p_ind)
            self.lang1.phoneme_pmi[self.lang2][seg1][seg2] = math.log(cognate_prob/noncognate_prob)

    
    