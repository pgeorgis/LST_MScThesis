#from load_languages import *
from word_evaluation import *
from statistics import mean
import math


def binary_cognate_sim(lang1, lang2, clustered_cognates,
                       exclude_synonyms=True):
    """Calculates the proportion of shared cognates between the two languages.
    lang1   :   Language class object
    lang2   :   Language class object
    clustered_cognates  :   nested dictionary of concepts and cognate IDs with their forms
    exclude_synonyms    :   Bool, default = True
        if True, calculation is based on concepts rather than cognate IDs 
        (i.e. maximum score = 1 for each concept, regardless of how many forms
         or cognate IDs there are for the concept)"""
        
    sims = {}
    total_cognate_ids = 0
    for concept in clustered_cognates:
        shared, not_shared = 0, 0
        l1_words, l2_words = 0, 0
        for cognate_id in clustered_cognates[concept]:
            langs_with_form = set(entry.split('/')[0].strip() 
                               for entry in clustered_cognates[concept][cognate_id])
            if lang1.name in langs_with_form:
                l1_words += 1
                if lang2.name in langs_with_form:
                    l2_words += 1
                    shared += 1
                else:
                    not_shared += 1
            elif lang2.name in langs_with_form:
                l2_words += 1
                not_shared += 1
        
        if (l1_words > 0) and (l2_words > 0):
            if exclude_synonyms == True:
                sims[concept] = min(shared, 1) if shared > 0 else 0
                total_cognate_ids += 1
            else:
                sims[concept] = max(shared, 0)
                total_cognate_ids += shared + not_shared
    
    return sum(sims.values()) / total_cognate_ids


def cognate_sim(lang1, lang2, clustered_cognates,
                eval_func, eval_sim, exclude_synonyms=True,
                **kwargs):
    sims = {}
    for concept in clustered_cognates:
        concept_sims = {}
        l1_wordcount, l2_wordcount = 0, 0
        for cognate_id in clustered_cognates[concept]:
            items = [entry.split('/') for entry in clustered_cognates[concept][cognate_id]]
            items = [(item[0].strip(), item[1]) for item in items]
            l1_words = [item[1] for item in items if item[0] == lang1.name]
            l2_words = [item[1] for item in items if item[0] == lang2.name]
            l1_wordcount += len(l1_words)
            l2_wordcount += len(l2_words)
            for l1_word in l1_words:
                for l2_word in l2_words:
                    score = eval_func((l1_word, lang1), (l2_word, lang2))#, *kwargs)
                    if eval_sim == False:
                        score = math.e**-score
                    concept_sims[(l1_word, l2_word)] = score
                    
        if len(concept_sims) > 0:
            if exclude_synonyms == True:
                sims[concept] = max(concept_sims.values())
            else:
                sims[concept] = mean(concept_sims.values())
            
        else:
            if (l1_wordcount > 0) and (l2_wordcount > 0):
                sims[concept] = 0
    
    return mean(sims.values())
    

#TO ADD:
#2) Phonetic word similarity (basic/advanced, with and without feature weighting)
#3) PMI similarity/distance
#4) Surprisal distance

#DONE:
#1) Binary cognate similarity (with/without synonyms)
    
    
    
    
    