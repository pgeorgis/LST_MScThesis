from phonetic_distance import *
from phoneme_correspondences import PhonemeCorrDetector
from auxiliary_functions import surprisal, adaptation_surprisal
import itertools
from asjp import ipa2asjp
from nltk import edit_distance


def basic_word_sim(word1, word2=None, sim_func=phone_sim, **kwargs):
    """Calculates phonetic similarity of an alignment without weighting by 
    segment type, position, etc.
    word1 : string (first word, unaligned) or list (alignment of two words)
    word2 : string (second word, unaligned)"""
    if word2 != None:
        alignment = phone_align(word1, word2, **kwargs)
    else:
        alignment = word1
    
    phone_sims = [sim_func(pair[0], pair[1], **kwargs) 
                  if '-' not in pair else 0 
                  for pair in alignment]
    
    return mean(phone_sims)


calculated_word_sims = {}
def word_sim(word1, word2=None, 
              sim_func=phone_sim, **kwargs):
    """Calculates phonetic similarity of an alignment without weighting by 
    segment type, position, etc.
    
    word1 : string (first word), list (alignment of two words), 
            or tuple (first word, second language)
    word2 : string (second word) or tuple (second word, second language)"""
    
    if (word1, word2, sim_func) in calculated_word_sims:
        return calculated_word_sims[(word1, word2, sim_func)]
    
    else:
        #If the languages are specified, calculate the informativity of each segment
        if (type(word1) == tuple and type(word2) == tuple):
            word1, lang1 = word1
            word2, lang2 = word2
            #Remove stress and tone diacritics; syllabic diacritics (above and below); spaces
            diacritics_to_remove = list(suprasegmental_diacritics) + ['̩', '̍', ' ']
            word_info1 = lang1.calculate_infocontent(strip_ch(word1, diacritics_to_remove))
            word_info2 = lang2.calculate_infocontent(strip_ch(word2, diacritics_to_remove))
            
        else:
            lang1, lang2 = None, None
        
        #If word2 == None, we assume word1 argument is actually an aligned word pair
        #Otherwise, align the two words
        if word2 != None:
            
            #If lang1 and lang2 are provided, supply their phoneme PMI as additional penalties for alignment
            if (lang1, lang2) != (None, None):
                #Check whether phoneme PMI has been calculated for this language pair
                #If not, then calculate it; if so, then retrieve it
                if len(lang1.phoneme_pmi[lang2]) > 0:
                    pmi_dict = lang1.phoneme_pmi[lang2]
                else:
                    pmi_dict = PhonemeCorrDetector(lang1, lang2).calc_phoneme_pmi()
                
                alignment = phone_align(word1, word2, added_penalty_dict=pmi_dict, **kwargs)
                
            else:
                alignment = phone_align(word1, word2, **kwargs)
        else:
            alignment = word1
        
        #Get list of penalties
        penalties = []
        for i in range(len(alignment)):
            pair = alignment[i]
            seg1, seg2 = pair
            
            #If the pair is a gap-aligned segment, assign the penalty 
            #based on the sonority and information content (if available) of the deleted segment
            if '-' in pair:
                penalty = 1
                if seg1 == '-':
                    deleted_segment = seg2
                    
                    #Check whether information content was calculated
                    #If so, retrieve information content of deleted segment
                    if (lang1, lang2) != (None, None): 
                        index = len([alignment[j][1] for j in range(i) if alignment[j][1] != '-'])
                        seg_info = word_info2[index][1]
                        penalty *= seg_info
                    
                else:
                    deleted_segment = seg1
                    #Check whether information content was calculated
                    #If so, retrieve information content of deleted segment
                    if (lang1, lang2) != (None, None): 
                        index = len([alignment[j][0] for j in range(i) if alignment[j][0] != '-'])
                        seg_info = word_info1[index][1]
                        penalty *= seg_info
                
                sonority = get_sonority(deleted_segment)
                sonority_penalty = 1-(sonority/(max_sonority+1))
                penalty *= sonority_penalty
                
                #Lessen the penalty under certain circumstances
                deleted_index = pair.index(deleted_segment)
                gap_index = deleted_index-1
                stripped_deleted = strip_diacritics(deleted_segment)
                if i > 0:
                    previous_seg = alignment[i-1][gap_index]
                    #1) If the deleted segment is a nasal and the corresponding 
                    #precending segment was nasalized
                    if stripped_deleted in nasals:
                        if '̃' in previous_seg: #check for nasalization diacritic:
                            penalty /= 2
                    
                    #2) If the deleted segment is a palatal glide (j, ɥ, i̯, ɪ̯),  
                    #and the corresponding preceding segment was palatalized
                    #or is a palatal consonant
                    elif strip_diacritics(deleted_segment, excepted=['̯']) in {'j', 'ɥ', 
                                                                               'i̯', 'ɪ̯'}:
                        if strip_diacritics(previous_seg)[0] in palatal:
                            penalty /= 2
                        elif ('ʲ' in previous_seg) or ('ᶣ' in previous_seg):
                            penalty /= 2
                            
                    #3) If the deleted segment is a high rounded/labial glide
                    #and the corresponding preceding segment was labialized
                    elif strip_diacritics(deleted_segment, excepted=['̯']) in {'w', 'ʍ', 'ʋ', 
                                                                               'u', 'ʊ', 
                                                                               'y', 'ʏ'}:
                        if ('ʷ' in previous_seg) or ('ᶣ' in previous_seg):
                            penalty /= 2
                    
                    #4) If the deleted segment is /h, ɦ/ and the corresponding 
                    #preceding segment was aspirated or breathy
                    elif stripped_deleted in {'h', 'ɦ'}:
                        if ('ʰ' in previous_seg) or ('ʱ' in previous_seg) or ('̤' in previous_seg):
                            penalty /= 2
                    
                        #Or if the following corresponding segment is breathy or
                        #pre-aspirated
                        else:
                            try:
                                next_seg = alignment[i+1][gap_index]
                                if ('̤' in next_seg) or (next_seg[0] in {'ʰ', 'ʱ'}):
                                    penalty /= 2
                            except IndexError:
                                pass
                        
                    #5) If the deleted segment is a rhotic approximant /ɹ, ɻ/
                    #and the corresponding preceding segment was rhoticized
                    elif stripped_deleted in {'ɹ', 'ɻ'}:
                        if (strip_diacritics(previous_seg) == 'ɚ') or ('˞' in previous_seg):
                            penalty /= 2
                    
                    #6) If the deleted segment is a glottal stop and the corresponding
                    #preceding segment was glottalized (or creaky?)
                    elif stripped_deleted == 'ʔ':
                        if 'ˀ' in previous_seg:
                            penalty /= 2
                    
                    
                #6) if the deleted segment is part of a long/geminate segment represented as double (e.g. /tt/ rather than /tː/), 
                #where at least one part of the geminate has been aligned
                #Method: check if the preceding or following pair contained the deleted segment at deleted_index, aligned to something other than the gap character
                #Check following pair
                double = False
                try:
                    nxt_pair = alignment[i+1]
                    if '-' not in nxt_pair:
                        if nxt_pair[deleted_index] == deleted_segment:
                            double = True
                except IndexError:
                    pass
                
                #Check preceding pair
                if i > 0:
                    prev_pair = alignment[i-1]
                    if '-' not in prev_pair:
                        if prev_pair[deleted_index] == deleted_segment:
                            double = True
                
                
                if double == True:
                    penalty /= 1.5
                
                
                #Discount deletion penalty according to how far from the left edge 
                #of the word it is (i.e., smaller penalties for deleted segments 
                #near the end of words)
                #penalty /= math.sqrt(i+1)
                
                #Discount deletion penalty according to prosodic sonority 
                #environment (based on List, 2012)
                deleted_i = sum([1 for j in range(i+1) if alignment[j][deleted_index] != '-'])-1
                segment_list = [alignment[j][deleted_index] 
                                for j in range(len(alignment))
                                if alignment[j][deleted_index] != '-']
                prosodic_env_weight = prosodic_environment_weight(segment_list, deleted_i)
                penalty /= math.sqrt(abs(prosodic_env_weight-7)+1)
                
                
                #Add the final penalty to penalty list
                penalties.append(penalty)
            
            #Otherwise take the penalty as the phonetic distance between the aligned segments
            else:
                distance = 1 - sim_func(seg1, seg2, **kwargs)
                penalties.append(distance)
    
        word_dist = mean(penalties)
        
        #Return as similarity: math.e**-distance = 1/(math.e**distance)
        word_sim = math.e**-word_dist
        
        #Save the calculated score
        if (lang1, lang2) != (None, None):
            calculated_word_sims[((word1, lang1), (word2, lang2), sim_func)] = word_sim
        else:
            calculated_word_sims[(word1, word2, sim_func)] = word_sim
        
        return word_sim


def segmental_word_sim(alignment, c_weight=0.5, v_weight=0.3, syl_weight=0.2):
    """Calculates the phonetic similarity of an aligned word pair according to
    weighted sum of similarity of consonantal segments, vocalic segments, and 
    syllable structure"""
    
    #Iterate through pairs of alignment:
    #Add fully consonant pairs to c_list, fully vowel/glide pairs to v_list
    #(ignore pairs of matched non-glide consonants with vowels)
    #and create syllable structure string for each word
    c_pairs, v_pairs = [], []
    syl_structure1, syl_structure2 = [], []
    for pair in alignment:
        strip_pair = (strip_diacritics(pair[0])[-1], strip_diacritics(pair[1])[-1])
        if (strip_pair[0] in consonants) and (strip_pair[1] in consonants):
            c_pairs.append(pair)
            syl_structure1.append('C')
            syl_structure2.append('C')
        elif (strip_pair[0] in vowels+glides) and (strip_pair[1] in vowels+glides):
            v_pairs.append(pair)
            syl_structure1.append('V')
            syl_structure2.append('V')
        else:
            if strip_pair[0] in consonants:
                syl_structure1.append('C')
            elif strip_pair[0] in vowels:
                syl_structure1.append('V')
            if strip_pair[1] in consonants:
                syl_structure2.append('C')
            elif strip_pair[1] in vowels:
                syl_structure2.append('V')
    
    #Count numbers of consonants and vowels
    N_c = max(syl_structure1.count('C'), syl_structure2.count('C'))
    N_v = max(syl_structure1.count('V'), syl_structure2.count('V'))
    
    #Consonant score: mean phonetic similarity of all matched consonantal pairs, divided by number of consonant segments
    try:
        c_score = sum([phone_sim(pair[0], pair[1]) for pair in c_pairs]) / N_c
    except ZeroDivisionError:
        c_score = 1
    
    #Vowel score: sum of phonetic similarity of all matched vowel pairs, divided by number of vowel segments
    try:
        v_score = sum([phone_sim(pair[0], pair[1]) for pair in v_pairs]) / N_v
    except ZeroDivisionError:
        v_score = 1
    
    #Syllable score: length-normalized Levenshtein distance of syllable structure strings
    syl_structure1, syl_structure2 = ''.join(syl_structure1), ''.join(syl_structure2)
    syl_score = 1 - (edit_distance(syl_structure1, syl_structure2) / len(alignment))
    
    #Final score: weighted sum of each component score
    return (c_weight * c_score) + (v_weight * v_score) + (syl_weight * syl_score)




#%%


combined_surprisal_dicts = {}
scored_WAS = {}
def mutual_surprisal(pair1, pair2, ngram_size=1, **kwargs):
    if (pair1, pair2) in scored_WAS:
        return scored_WAS[(pair1, pair2)]
    
    else:
        word1, lang1 = pair1
        word2, lang2 = pair2
        
        #Remove suprasegmental diacritics
        diacritics_to_remove = list(suprasegmental_diacritics) + ['̩', '̍', ' ']
        word1 = strip_ch(word1, diacritics_to_remove)
        word2 = strip_ch(word2, diacritics_to_remove)
        
        #Calculate combined phoneme PMI if not already done
        pmi_dict = combine_PMI(lang1, lang2, **kwargs)
        
        #Generate alignments in each direction: alignments need to come from PMI
        alignment = phone_align(word1, word2, added_penalty_dict=pmi_dict)
        
        #Calculate phoneme surprisal if not already done
        if len(lang1.phoneme_surprisal[lang2]) == 0:
            surprisal_dict_l1l2 = PhonemeCorrDetector(lang1, lang2).calc_phoneme_surprisal(ngram_size=ngram_size, **kwargs)
        if len(lang2.phoneme_surprisal[lang1]) == 0:
            surprisal_dict_l2l1 = PhonemeCorrDetector(lang2, lang1).calc_phoneme_surprisal(ngram_size=ngram_size, **kwargs)
            
        #Calculate the word-adaptation surprisal in each direction
        #(note: alignment needs to be reversed to run in second direction)
        WAS_l1l2 = adaptation_surprisal(alignment, lang1.phoneme_surprisal[lang2], normalize=False, ngram_size=ngram_size)
        WAS_l2l1 = adaptation_surprisal(reverse_alignment(alignment), lang2.phoneme_surprisal[lang1], normalize=False, ngram_size=ngram_size)
        
        #Calculate self-surprisal values in each direction
        self_surprisal1 = lang1.calculate_infocontent(word1)
        self_surprisal1 = sum([item[1] for item in self_surprisal1.values()])
        self_surprisal2 = lang2.calculate_infocontent(word2)
        self_surprisal2 = sum([item[1] for item in self_surprisal2.values()])
        
        #Divide WAS by self-surprisal
        WAS_l1l2 /= self_surprisal2
        WAS_l2l1 /= self_surprisal1
        
        #Return the average of these two values
        return mean([WAS_l1l2, WAS_l2l1])

def surprisal_sim(pair1, pair2, ngram_size=1, **kwargs):
    #Return mutual surprisal distance as similarity: math.e**-distance = 1/(math.e**distance)
    return math.e**-(mutual_surprisal(pair1, pair2, ngram_size=ngram_size, **kwargs))
    #another possibility: mutual surprisal in relation to phoneme entropy; if it exceeds the phoneme entropy then similarity is 0

combined_PMI_dicts = {}
def combine_PMI(lang1, lang2, **kwargs):
    #Return already calculated dictionary if possible
    if (lang1, lang2) in combined_PMI_dicts:
        return combined_PMI_dicts[(lang1, lang2)]

    #Otherwise calculate from scratch
    if len(lang1.phoneme_pmi[lang2]) > 0:
        pmi_dict_l1l2 = lang1.phoneme_pmi[lang2]
    else:
        pmi_dict_l1l2 = PhonemeCorrDetector(lang1, lang2).calc_phoneme_pmi(**kwargs)
    if len(lang2.phoneme_pmi[lang1]) > 0:
        pmi_dict_l2l1 = lang2.phoneme_pmi[lang1]
    else:
        pmi_dict_l2l1 = PhonemeCorrDetector(lang2, lang1).calc_phoneme_pmi(**kwargs)
        
    #Average together the PMI values from each direction
    pmi_dict = defaultdict(lambda:defaultdict(lambda:0))
    for seg1 in pmi_dict_l1l2:
        for seg2 in pmi_dict_l1l2[seg1]:
            pmi_dict[seg1][seg2] = mean([pmi_dict_l1l2[seg1][seg2], pmi_dict_l2l1[seg2][seg1]])
    combined_PMI_dicts[(lang1, lang2)] = pmi_dict
    combined_PMI_dicts[(lang2, lang1)] = pmi_dict
    return pmi_dict



scored_word_pmi = {}
def score_pmi(pair1, pair2, sim2dist=True, **kwargs):
    if (pair1, pair2, sim2dist) in scored_word_pmi:
        return scored_word_pmi[(pair1, pair2, sim2dist)]
    
    else:
        word1, lang1 = pair1
        word2, lang2 = pair2
        
        #Remove suprasegmental diacritics
        diacritics_to_remove = list(suprasegmental_diacritics) + ['̩', '̍', ' ']
        word1 = strip_ch(word1, diacritics_to_remove)
        word2 = strip_ch(word2, diacritics_to_remove)
        
        #Calculate PMI in both directions if not already done, otherwise retrieve the dictionaries
        pmi_dict = combine_PMI(lang1, lang2, **kwargs)
            
        #Align the words with PMI
        alignment = phone_align(word1, word2, added_penalty_dict=pmi_dict)
        
        #Calculate PMI scores for each aligned pair
        PMI_values = [pmi_dict[pair[0]][pair[1]] for pair in alignment]
        PMI_score = mean(PMI_values) 
        
        if sim2dist == True:
            alpha=0.5
            PMI_dist = math.exp(-max(PMI_score, 0)**alpha)
            scored_word_pmi[(pair1, pair2, sim2dist)] = PMI_dist
            return PMI_dist
        
        else:
            scored_word_pmi[(pair1, pair2, sim2dist)] = PMI_score
            return PMI_score

#%%
def LevenshteinDist(word1, word2, normalize=True, asjp=True):
    if asjp == True:
        word1, word2 = map(ipa2asjp, [word1, word2])
    LevDist = edit_distance(word1, word2)
    if normalize == True:
        LevDist /= max(len(word1), len(word2))
    return LevDist
        
    

#%%
hybrid_scores = {}
def hybrid_distance(pair1, pair2, funcs, func_sims, weights=None, **kwargs):
    if weights == None:
        weights = [1/len(funcs) for i in range(len(funcs))]
    if (pair1, pair2, tuple(functions), tuple(weights)) in scored_word_pmi:
        return hybrid_scores[(pair1, pair2, functions, weights)]
    
    else:
        word1, lang1 = pair1
        word2, lang2 = pair2
        
        scores = {}
        for func, func_sim, weight in zip(funcs, func_sims, weights):
            if weight > 0:
                score = func(pair1, pair2, **kwargs)
                if func_sim == True:
                    score = 1 - score
                scores[func] = score * weight
            else:
                scores[func] = 0
        
        hybrid_score = sum(scores.values())
        hybrid_scores[(pair1, pair2, tuple(functions), tuple(weights))] = hybrid_score
        return hybrid_score, scores#, hybrid_score
        
    
#%%
    
def Z_score(p_values):
    neg_log_p = [-math.log(p) for p in p_values]
    return (sum(neg_log_p) - len(p_values)) / math.sqrt(len(p_values))

def Z_max(n_concepts):
    return ((n_concepts * -math.log(1/((n_concepts**2)-n_concepts+1))) - n_concepts) / math.sqrt(n_concepts)

def Z_min(n_concepts):
    return (n_concepts * -math.log(1) - n_concepts) / math.sqrt(n_concepts)

def Z_dist(p_values):
    N = len(p_values)
    Zmax = Z_max(N)
    Zmin = Z_min(N)
    Zscore = Z_score(p_values)
    return (Zmax - Zscore) / (Zmax - Zmin)
    
    
