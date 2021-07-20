#PHONETIC SEGMENT ANALYSIS AND PHONETIC DISTANCE
#Code written by Philip Georgis (2021)


#LOAD REQUIRED PACKAGES AND FUNCTIONS
import re, math
import pandas as pd
from collections import defaultdict
from nwunsch_alignment import best_alignment 
from nltk import edit_distance
from sklearn.metrics import jaccard_score
from statistics import mean

#IMPORT SOUND DATA
phone_data = pd.read_csv('Phones/segments.csv', sep=',')

def binary_feature(feature):
    """Converts features of type ['0', '-', '+'] to binary [0, 1]"""
    if str(feature) == '+':
        return 1
    else:
        return 0

#Dictionary of basic phones with their phonetic features
phone_features = {phone_data['segment'][i]:{feature:binary_feature(phone_data[feature][i])
                                          for feature in phone_data.columns
                                          if feature not in ['segment',
                                                             #'stress',
                                                             #'tone',
                                                             'sonority']
                                          if pd.isnull(phone_data[feature][i]) == False}
                  for i in range(len(phone_data))}

features = set(feature for sound in phone_features for feature in phone_features[sound])

#%%
#Dictionary of basic phone with their sonority levels
phone_sonority = {phone_data['segment'][i]:int(phone_data['sonority'][i])
                  for i in range(len(phone_data))}

max_sonority = max(phone_sonority.values())

#%%
#Load basic groupings of phones; e.g. plosive, fricative, velar, palatal
phone_groups = pd.read_csv('Phones/phone_classes.csv')
phone_groups = {phone_groups['Group'][i]:phone_groups['Phones'][i].split()
                for i in range(len(phone_groups))}

#Set these phone groups as global variables so that they are callable by name
globals().update(phone_groups)

#Set basic consonants and vowels using syllabic feature
consonants = [phone for phone in phone_features
              if phone_features[phone]['syllabic'] == 0]
vowels = [phone for phone in phone_features if phone not in consonants]

#List of all basic sounds
all_sounds = list(set(vowels + consonants))

#%%
#IMPORT DIACRITICS DATA
diacritics_data = pd.read_csv('Phones/diacritics.csv', sep='\t')

#Create dictionary of diacritic characters with affected features and values
diacritics_effects = defaultdict(lambda:[])
for i in range(len(diacritics_data)):
    effect = (diacritics_data['Feature'][i], binary_feature(diacritics_data['Value'][i]))
    
    #Skip diacritics which have no effect on features
    if type(effect[0]) != float:
        
        #Add to dictionary, with diacritic as key
        diacritics_effects[diacritics_data['Diacritic'][i]].append(effect)

#Isolate suprasegmental diacritics
suprasegmental_diacritics = set(diacritics_data.Diacritic[i] 
                                for i in range(len(diacritics_data)) 
                                if diacritics_data.Type[i] == 'suprasegmental')
suprasegmental_diacritics.remove('ː') #don't include length as a suprasegmental


#Diacritics by position with respect to base segments
pre_diacritics = set([diacritics_data['Diacritic'][i] 
                      for i in range(len(diacritics_data))
                      if diacritics_data['Position'][i] == 'pre'])
post_diacritics = set([diacritics_data['Diacritic'][i]
                       for i in range(len(diacritics_data))
                       if diacritics_data['Position'][i] == 'post'])
inter_diacritics = ['͡', '͜']

#List of all diacritic characters
diacritics = list(pre_diacritics) + list(post_diacritics) + inter_diacritics

def strip_diacritics(string, excepted=[]):
    """Removes diacritic characters from an IPA string
    By default removes all diacritics; in order to keep certain diacritics,
    these should be passed as a list to the "excepted" parameter"""
    to_remove = [ch for ch in string if ch in diacritics if ch not in excepted]
    return ''.join([ch for ch in string if ch not in to_remove])


#%%
#BASIC PHONE ANALYSIS: Methods for yielding feature dictionaries of phone segments
phone_ids = {} #Dictionary of phone feature dicts 
def phone_id(segment):
    """Returns a dictionary of phonetic feature values for the segment"""
    #If feature dictionary for segment has been created already, retrieve this
    if segment in phone_ids:
        return phone_ids[segment]
    
    #Otherwise generate a new phone feature dictionary
    seg_dict = defaultdict(lambda:0)
    
    #Split segment into component parts, if relevant
    parts = re.split('͡|͜', segment)
    
    #Generate feature dictionary for each part and add to main feature dict
    for part in parts:
        part_id = compact_diacritics(part)
        for feature in part_id:
            #Value = 1 (+) overrides value = 0 (-,0)
            seg_dict[feature] = max(seg_dict[feature], part_id[feature])
    
    #Ensure that affricates are +DELAYED RELEASE and -CONTINUANT
    if len(parts) > 1:
        if strip_diacritics(parts[0]) in plosive:
            if strip_diacritics(parts[-1]) in fricative:
                seg_dict['delayedRelease'] = 1 
                seg_dict['continuant'] = 0 
    
    #Add segment's feature dictionary to phone_ids; return the feature dictionary
    phone_ids[segment] = seg_dict
    return seg_dict 


def diphthong_dict(diphthong):
    """Returns dictionary of features for diphthongal segment"""
    components = segment_word(diphthong)
    
    #Create combined dictionary using features of component segments
    weight = 1 / len(components)
    diphth_dict = defaultdict(lambda:0)
    for segment in components:
        feature_id = phone_id(segment)
        for feature in feature_id:
            diphth_dict[feature] += (weight * feature_id[feature])
    
    #Length feature should be either 0 or 1
    if diphth_dict['long'] > 0:
        diphth_dict['long'] = 1
        
    return diphth_dict


def compact_diacritics(segment):
    """Applies diacritic effects to relevant segments"""
    #Base of the segment is the non-diacritic portion
    base = strip_diacritics(segment)
    
    #If the length of the base > 1, the segment is a diphthong
    if len(base) > 1:
        return diphthong_dict(segment)
    
    else:
        #Retrieve basic dictionary of phone features for the base segment
        seg_id = phone_features[base]
        
        #Modifiers are whichever diacritics may have been in the segment string
        modifiers = [ch for ch in segment if ch not in base]
        
        #Apply diacritic effects to feature dictionary
        for modifier in modifiers:
            for effect in diacritics_effects[modifier]:
                feature, value = effect[0], effect[1] 
                seg_id[feature] = value
        return seg_id

#%%
def get_sonority(sound):
    """Returns the sonority level of a sound according to Parker's (2002) 
    universal sonority hierarchy
    
    modified:
    https://www.researchgate.net/publication/336652515/figure/fig1/AS:815405140561923@1571419143959/Adapted-version-of-Parkers-2002-sonority-hierarchy.ppm
    
    TO DO: DIPHTHONGS, Complex plosives, e.g. /k͡p̚/"""
    #If sonority for this sound has already been calculated, retrieve this
    if sound in phone_sonority:
        return phone_sonority[sound]
    
    #Strip diacritics
    strip_sound = strip_diacritics(sound)
    
    #Feature dictionary for sound
    phone = phone_id(sound)
    
    #Determine appropriate sonority level by checking membership in sound 
    #groups (manner/place of articulation) and/or relevant features     

    #Vowels
    if strip_sound in vowels:
        #Treat as glide if non-syllabic
        if phone['syllabic'] == 0:
            sonority = 11
        
        #Schwa /ə/ and /ɨ/ have special sonority
        elif strip_sound == 'ə':
            sonority = 13
        elif strip_sound == 'ɨ':
            sonority = 12
        
        #Open and near-open vowels
        elif ((phone['high'] == 0) and (phone['low'] == 1)): 
            sonority = 16
        
        #Open-mid, mid, close-mid vowels other than schwa /ə/
        elif phone['high'] == 0:  
            sonority = 15
        
        #Near-close and close vowels other than /ɨ/
        elif phone['high'] == 1:
            sonority = 14

    #Consonants
    elif strip_sound[0] in consonants: 
        #index 0, for affricates or complex plosives, such as /p͡f/ and /k͡p/, written with >1 character
        
        #Glides
        if strip_sound in glides:
            sonority = 11
        
        #/r/
        elif strip_sound == 'r':
            sonority = 10
        
        #Laterals
        elif phone['lateral'] == 1:
            sonority = 9
        
        #Taps/flaps
        elif strip_sound in tap_flap:
            sonority = 8
           
        #Trills
        elif strip_sound in trills:
            sonority = 7
        
        #Nasals
        elif strip_sound in nasals:
            sonority = 6
        
        #/h/
        elif strip_sound == 'h':
            sonority = 5
        
        #Fricatives
        elif strip_sound in fricative:
            
            #Voiced fricatives
            if phone['periodicGlottalSource'] == 1:
                sonority = 4
            
            #Voiceless fricatives
            else:
                sonority = 3
        
        elif strip_sound in tonemes:
            sonority = 0
        
        #Affricates, plosives, implosives, clicks
        else:
        
            #Voiced
            if phone['periodicGlottalSource'] == 1:
                sonority = 2
                
            #Voiceless 
            else:
                sonority = 1
            
    #Other sounds: raise error message
    else:
        #Diphthong: calculate sonority as maximum sonority of component parts
        if strip_sound[0] in vowels:
            diphthong_components = segment_word(sound)
            sonorities = [get_sonority(v) for v in diphthong_components]
            sonority = max(sonorities)
            
        
        else:
            print(f'Error: the sonority of this phone ({sound}) cannot be determined!')
            raise ValueError
   
    #Save sonority level of this sound in sonority dictionary, return sonority level
    phone_sonority[sound] = sonority
    return sonority



#WORD SEGMENTATION
def segment_word(word):
    """Returns a list of segmented phones from the word"""
    phone_list = defaultdict(lambda:[])
    
    #Iterate through all characters of the word
    i = 0
    for ch in word:
        
        #If character is a preceding diacritic, add it to the next segment
        #by incrementing the index by 1
        if ch in pre_diacritics:
            i += 1
        
        #Or, if there was a previous sound at the current index
        elif i in phone_list:
            
            #Last character of this previous sound
            last = phone_list[i][-1]
            
            #Increment index by 1 if the current character is NOT a diacritic
            #AND if the last character of the previous sound was either
            #a post-diacritic or not a diacritic at all:
            if ch not in diacritics:
                if ((last in post_diacritics) or (last not in diacritics)):
                    i += 1
        
        #Add the character to the yielded index
        phone_list[i].append(ch)
    
    #Rejoin together all characters for each segment
    for i in phone_list:
        phone_list[i] = ''.join(phone_list[i])
    
    #Return a list of the segments
    return list(phone_list.values())

def remove_stress(word):
    """Removes stress annotation from an IPA string"""
    return ''.join([ch for ch in word if ch not in ['ˈ', 'ˌ']])

#%%
def common_features(segment_list, 
                    start_features=features):
    """Returns the features/values shared by all segments in the list"""
    features = list(start_features)[:]
    feature_values = defaultdict(lambda:[])
    for seg in segment_list:
        for feature in features:
            value = phone_id(seg)[feature]
            if value not in feature_values[feature]:
                feature_values[feature].append(value)
    common = [(feature, feature_values[feature][0]) for feature in feature_values if len(feature_values[feature]) == 1]
    return common

def different_features(seg1, seg2):
    diffs = []
    seg1_id = phone_id(seg1)
    seg2_id = phone_id(seg2)
    for feature in seg1_id:
        if seg2_id[feature] != seg1_id[feature]:
            diffs.append(feature)
    return diffs

def lookup_segments(features, values, 
                    segment_list=all_sounds):
    """Returns a list of segments whose feature values match the search criteria"""
    matches = []
    for segment in segment_list:
        match_tallies = 0
        for feature, value in zip(features, values):
            if phone_id(segment)[feature] == value:
                match_tallies += 1
        if match_tallies == len(features):
            matches.append(segment)
    return set(matches)

#%%

#SIMILARITY / DISTANCE MEASURES
def dot_product(vec1, vec2):
    """Returns the dot product of two vectors"""
    products = []
    for term in vec1:
        try:
            product = vec1[term] * vec2[term]
            products.append(product)
        except KeyError:
            print(f'The specified key ({term}) is missing from vec2.')
    return sum(products)

def norm(vector):
    """Returns the norm of a vector"""
    sum_of_squares = 0
    for term in vector:
        sum_of_squares += (vector[term] ** 2)
    return math.sqrt(sum_of_squares)        

def vector_sim(vec1, vec2):
    """Returns the cosine similarity of two non-zero vectors"""
    numerator = dot_product(vec1, vec2)
    denominator = norm(vec1) * norm(vec2)
    if denominator == 0:
        print('Error: one or more of the vectors is a zero-vector!')
        raise ValueError
    similarity = numerator / denominator
    return similarity


def hamming_distance(vec1, vec2, normalize=True):
    differences = len([feature for feature in vec1 if vec1[feature] != vec2[feature]])
    if normalize == True:
        return differences / len(vec1)
    else: 
        return differences

def jaccard_sim(vec1, vec2):
    features = sorted(list(vec1.keys()))
    vec1_values = [vec1[feature] for feature in features]
    vec2_values = [vec2[feature] for feature in features]
    return jaccard_score(vec1_values, vec2_values)

def dice_sim(vec1, vec2):
    jaccard = jaccard_sim(vec1, vec2)
    return (2*jaccard) / (1+jaccard)

#PHONE COMPARISON
checked_phone_sims = {}
def phone_sim(phone1, phone2, method='dice', exclude_features=[]):
    """Returns the similarity of the features of the two phones according to
    the specified distance/similarity function;
    Features not to be included in the comparison should be passed as a list to
    the exclude_features parameter (by default no features excluded)"""
    
    #If the phone similarity has already been calculated for this pair, retrieve it
    reference = (phone1, phone2, method, tuple(exclude_features))
    if reference in checked_phone_sims:
        return checked_phone_sims[reference]
    
    #Get feature dictionaries for each phone
    phone_id1, phone_id2 = phone_id(phone1), phone_id(phone2)
    
    #Remove any specified features
    for feature in exclude_features:
        for phoneid in [phone_id1, phone_id2]:
            try:
                del phoneid[feature]
            except KeyError:
                pass

    #Calculate similarity of phone features according to specified measure
    measures = {'cosine':vector_sim,
                'dice':dice_sim,
                'hamming':hamming_distance,
                'jaccard':jaccard_sim}
    dist_func = measures[method]
    
    score = dist_func(phone_id1, phone_id2)
    
    #If method is Hamming, convert distance to similarity
    if method == 'hamming':
        score = 1 - score
        
    #Save the phonetic similarity score to dictionary, return score
    checked_phone_sims[reference] = score
    checked_phone_sims[reference] = score
    return score

def compare_measures(seg1, seg2):
    measures = {}
    for method in ['cosine', 'dice', 'hamming', 'jaccard']:
        measures[method] = phone_sim(seg1, seg2, method)
    return measures


#WORD-LEVEL PHONETIC COMPARISON AND ALIGNMENT
def align_costs(seq1, seq2, dist_func, sim=False): #*kwargs?
    alignment_costs = {}
    for i in range(len(seq1)):
        for j in range(len(seq2)):
            seq1_i, seq2_j = seq1[i], seq2[j]
            cost = dist_func(seq1_i, seq2_j)
            if sim == True:
                cost = 1 - cost
            alignment_costs[(i, j)] = cost
    return alignment_costs

def log_phone_sim_sonority(seg1, seg2, method='dice'):
    try:
        phon_sim = math.log(phone_sim(seg1, seg2, method))
    
    #If phone similarity = 0, we can't take the log. Instead set to negative infinity
    except ValueError:
        phon_sim = -math.inf
    
    #Sonority difference is number of levels of difference in sonority
    son_diff = abs(get_sonority(seg1) - get_sonority(seg2))
    
    #Sonority similarity is 1 - normalized sonority difference
    son_sim = math.log(1 - ((son_diff+1) / (max_sonority+1)))
    
    return phon_sim + son_sim


def phone_align(word1, word2, gop=-0.7, segmented=False):
    """Align segments of word1 with segments of word2 according to Needleman-
    Wunsch algorithm, with costs determined by phonetic and sonority similarity;
    If segmented == False, the words are first segmented before being aligned."""
    if segmented == False:
        segments1, segments2 = segment_word(word1), segment_word(word2)
    else:
        segments1, segments2 = word1, word2  
    
    #Calculate costs of aligning each pair of segments
    alignment_costs = {}
    for i in range(len(segments1)):
        for j in range(len(segments2)):
            #Cost of aligning segments1[i] with segments2[j] is log of their
            #phone similarity, plus the log of their sonority similarity
            try:
                phon_sim = math.log(phone_sim(segments1[i], segments2[j]))
            
            #If phone similarity = 0, we can't take the log. Instead set to negative infinity
            except ValueError:
                phon_sim = -math.inf
            
            #Sonority difference is number of levels of difference in sonority
            son_diff = abs(get_sonority(segments1[i]) - get_sonority(segments2[j]))
            
            #Sonority similarity is 1 - normalized sonority difference
            son_sim = math.log(1 - ((son_diff+1) / (max_sonority+1)))
            
            alignment_costs[(i, j)] = phon_sim + son_sim
    
    #Calculate best alignment using Needleman-Wunsch algorithm
    best = best_alignment(SEQUENCE_1=segments1, SEQUENCE_2=segments2,
                          SCORES_DICT=alignment_costs, GAP_SCORE=gop)
    return best


def visual_align(alignment):
    """Renders list of aligned segment pairs as an easily interpretable
    alignment string, with <∅> representing null segments,
    e.g.:
    visual_align([('z̪', 'ɡ'),('vʲ', 'v'),('ɪ', 'j'),('-', 'ˈa'),('z̪', 'z̪'),('d̪', 'd'),('ˈa', 'a')])
    = 'z̪-ɡ / vʲ-v / ɪ-j / ∅-ˈa / z̪-z̪ / d̪-d / ˈa-a' """
    a = []
    for item in alignment:
        if '-' not in item:
            a.append(f'{item[0]}-{item[1]}')
        else:
            if item[0] == '-':
                a.append(f'∅-{item[1]}')
            else:
                a.append(f'{item[0]}-∅')
    return ' / '.join(a)


def undo_visual_align(visual_alignment):
    """Reverts a visual alignment to a list of tuple segment pairs"""
    seg_pairs = visual_alignment.split(' / ')
    seg_pairs = [tuple(pair.split('-')) for pair in seg_pairs]
    return seg_pairs
    

def reverse_alignment(alignment):
    """Flips the alignment, e.g.:
        reverse_alignment([('s', 's̪'), ('o', 'ɔ'), ('l', 'l'), ('-', 'ɛ'), ('-', 'j')])
        = [('s̪', 's'), ('ɔ', 'o'), ('l', 'l'), ('ɛ', '-'), ('j', '-')]"""
    reverse = []
    for pair in alignment:
        reverse.append((pair[1], pair[0]))
    return reverse


def word_sim(alignment, c_weight=0.5, v_weight=0.3, syl_weight=0.2):
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
