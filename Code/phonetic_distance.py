#PHONETIC SEGMENT ANALYSIS AND PHONETIC DISTANCE
#Code written by Philip Georgis (2021)


#LOAD REQUIRED PACKAGES AND FUNCTIONS
import re, math, os
import pandas as pd
from collections import defaultdict
from nltk import edit_distance
from sklearn.metrics import jaccard_score
from scipy.spatial.distance import cosine
from statistics import mean
from nwunsch_alignment import best_alignment 
from auxiliary_functions import strip_ch

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
              if phone_features[phone]['syllabic'] == 0
              if phone not in tonemes]
vowels = [phone for phone in phone_features if phone not in consonants+tonemes]

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
suprasegmental_diacritics.remove('??') #don't include length as a suprasegmental


#Diacritics by position with respect to base segments
inter_diacritics = ['??', '??']
pre_diacritics = set([diacritics_data['Diacritic'][i] 
                      for i in range(len(diacritics_data))
                      if diacritics_data['Position'][i] == 'pre'])
post_diacritics = set([diacritics_data['Diacritic'][i]
                       for i in range(len(diacritics_data))
                       if diacritics_data['Position'][i] == 'post'])
prepost_diacritics = {'??', '??', '???'} #diacritics which can appear before or after


#List of all diacritic characters
diacritics = list(pre_diacritics) + list(post_diacritics) + inter_diacritics

def strip_diacritics(string, excepted=[]):
    """Removes diacritic characters from an IPA string
    By default removes all diacritics; in order to keep certain diacritics,
    these should be passed as a list to the "excepted" parameter"""
    try:
        to_remove = [ch for ch in string if ch in diacritics if ch not in excepted]
        return ''.join([ch for ch in string if ch not in to_remove])
    except RecursionError:
        with open('error.txt', 'w') as f:
            f.write(f'Unable to parse phonetic characters in form: {string}')
        raise RecursionError


def verify_charset(text):
    """Verifies that all characters are recognized as IPA characters or diacritics"""
    chs = set(list(text))
    unk_ch = set(ch for ch in chs if ch not in set(all_sounds+diacritics+tonemes+[' ']))
    return unk_ch


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
    parts = re.split('??|??', segment)
    
    #Generate feature dictionary for each part and add to main feature dict
    for part in parts:
        if len(part.strip()) > 0:
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
    
    #Create weights: 1 for syllabic components and 0.5 for non-syllabic components
    weights = [1 if phone_id(component)['syllabic'] == 1 else 0.5 
               for component in components]
    
    #Normalize the weights
    weight_sum = sum(weights)
    weights = [i/weight_sum for i in weights]
    
    #Create combined dictionary using features of component segments
    diphth_dict = defaultdict(lambda:0)
    for segment, weight in zip(components, weights):
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
    
    #If the length of the base > 1, the segment is a diphthong or complex toneme
    #Filter out tonemes
    if ((len(base) > 1) and (base[0] not in tonemes)):
        return diphthong_dict(segment)
    
    else:
        #Retrieve basic dictionary of phone features for the base segment
        #If the segment is a toneme, use the first component as its base
        if base[0] in tonemes:
            seg_id = tonal_features(segment)
        
        else:
            #Create copy of original feature dictionary, or else it modifies the source
            seg_id = {feature:phone_features[base][feature] for feature in phone_features[base]}
            
        #Modifiers are whichever diacritics may have been in the segment string
        modifiers = [ch for ch in segment if ch not in base]
        
        #Apply diacritic effects to feature dictionary
        for modifier in modifiers:
            for effect in diacritics_effects[modifier]:
                feature, value = effect[0], effect[1] 
                seg_id[feature] = value
                
            if modifier == '??': #lowered diacritic, for turning fricatives into approximants
                if base[0] in fricative:
                    seg_id['approximant'] = 1
                    seg_id['consonantal'] = 0
                    seg_id['delayedRelease'] = 0
                    seg_id['sonorant'] = 1
            
            elif modifier == '??': #raised diacritic
                #for turning approximants/trills into fricativized approximants
                if base[0] in approximants+trills:
                    seg_id['delayedRelease'] = 1
                    
                #for turning fricatives into plosives
                elif base[0] in fricative:
                    seg_id['continuant'] = 0
                    seg_id['delayedRelease'] = 0
        
        return seg_id


tone_levels = {'??':1, '??':1, 
               '??':2, '??':2,
               '??':3, '??':3,
               '??':4, '???':4, 
               '??':5, '???':5,
               '???':0, '???':0}

def tonal_features(toneme):
    """Computes complex tonal features"""
    
    #Set the base as the first component of the toneme
    base = toneme[0]
    
    #Create copy of original feature dictionary, or else it modifies the source
    toneme_id = {feature:phone_features[base][feature] for feature in phone_features[base]}
    
    #Get the tone level of each tonal component of the toneme
    toneme_levels = [tone_levels[t] for t in toneme if t in tonemes]
    
    #Compute the complex tone features if not just a level tone
    if len(set(toneme_levels)) > 1:
        
        #Add feature tone_contour to all non-level tones
        toneme_id['tone_contour'] = 1
        
        #Ensure that contour tones do not have features tone_mid and tone_central
        #(which are unique to level tones)
        toneme_id['tone_central'] = 0
        toneme_id['tone_mid'] = 0
    
        #Get the maximum tonal level
        max_level = max(toneme_levels)
        
        #Add feature tone_high if the maximum tone level is at least 4
        if max_level >= 4:
            toneme_id['tone_high'] = 1
        
        #Check whether any subsequence of the tonal components is rising or falling
        contours = {}
        for t in range(len(toneme_levels)-1):
            t_seq = toneme_levels[t:t+2]
            
            #Check for a tonal rise
            if t_seq[0] < t_seq[1]:
                toneme_id['tone_rising'] = 1
                contours[t] = 'rise'
            
            #Check for a tonal fall
            elif t_seq[0] > t_seq[1]:
                toneme_id['tone_falling'] = 1
                contours[t] = 'fall'
                
                #If a subsequence is falling, check whether the previous subsequence was rising
                #in order to determine whether the tone is convex (rising-falling)
                if t > 0:
                    if contours[t-1] == 'rise':
                        toneme_id['tone_convex'] = 1
                                            
            #Otherwise two equal tone levels in a row, e.g. '????????'
            else:
                contours[t] = 'level'
    
    return toneme_id
    

#%%
def get_sonority(sound):
    """Returns the sonority level of a sound according to Parker's (2002) 
    universal sonority hierarchy
    
    modified:
    https://www.researchgate.net/publication/336652515/figure/fig1/AS:815405140561923@1571419143959/Adapted-version-of-Parkers-2002-sonority-hierarchy.ppm
    
    TO DO: DIPHTHONGS, Complex plosives, e.g. /k??p??/"""
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
        
        #Schwa /??/ and /??/ have special sonority
        elif strip_sound == '??':
            sonority = 13
        elif strip_sound == '??':
            sonority = 12
        
        #Open and near-open vowels
        elif ((phone['high'] == 0) and (phone['low'] == 1)): 
            sonority = 16
        
        #Open-mid, mid, close-mid vowels other than schwa /??/
        elif phone['high'] == 0:  
            sonority = 15
        
        #Near-close and close vowels other than /??/
        elif phone['high'] == 1:
            sonority = 14

    #Consonants
    elif strip_sound[0] in consonants: 
        #index 0, for affricates or complex plosives, such as /p??f/ and /k??p/, written with >1 character
        
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
        
        #Affricates, plosives, implosives, clicks
        else:
        
            #Voiced
            if phone['periodicGlottalSource'] == 1:
                sonority = 2
                
            #Voiceless 
            else:
                sonority = 1
    
    #Tonemes
    elif strip_sound[0] in tonemes:
        sonority = 0
    
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


def prosodic_environment_weight(segments, i):
    """Returns the relative prosodic environment weight of a segment within
    a word, based on List (2012)"""
    
    #Word-initial segments
    if i == 0:
        #Word-initial consonants: weight 7
        if strip_diacritics(segments[i])[0] in consonants:
            return 7
        
        #Word-initial vowels: weight 6
        else:
            return 6
    
    #Word-final segments
    elif i == len(segments)-1:
        stripped_segment = strip_diacritics(segments[i])[0]
        
        #Word-final consonants: weight 2
        if stripped_segment in consonants:
            return 2
        
        #Word-final vowels: weight 1
        elif stripped_segment in vowels:
            return 1
        
        #Word-final tonemes: weight 0
        else:
            return 0
    
    #Word-medial segments
    else:
        prev_segment, segment_i, next_segment = segments[i-1], segments[i], segments[i+1]
        prev_sonority, sonority_i, next_sonority = map(get_sonority, [prev_segment, 
                                                                      segment_i, 
                                                                      next_segment])
        
        #Sonority peak: weight 3
        if prev_sonority <= sonority_i >= next_sonority:
            return 3
        
        #Descending sonority: weight 4
        elif prev_sonority >= sonority_i >= next_sonority:
            return 4
        
        #Ascending sonority: weight 5
        else:
            return 5


#WORD SEGMENTATION
def segment_word(word, remove_ch=[]):
    """Returns a list of segmented phones from the word"""
    
    #Remove spaces and other specified characters/diacritics (e.g. stress)
    word = ''.join([ch for ch in word if ch not in remove_ch+[' ']])
    
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
            
            #Previous segment
            prev = phone_list[i]
            
            #Last character of this previous segment
            last = prev[-1]
            
            #Base of this previous segment
            prev_base = strip_diacritics(prev)
            
            #Increment index by 1 if the current character is a consonant or vowel
            #AND if the last character of the previous sound was either
            #a post-diacritic or not a diacritic at all:
            if ch in consonants+vowels:
                if last in post_diacritics:
                    
                    #Don't increment the index unless the previous segment
                    #consists of more than just a diacritic,
                    #which would be the case for pre-aspiration/pre-nasalization
                    if len(prev_base) > 0:
                        i += 1
                    
                elif last not in diacritics:
                    i += 1
            
            #If the current character is a toneme, increment the index only
            #if the base of the previous sound was not a toneme
            #(in order to group sequences of tonemes and associated diacritics as a single segment)
            elif ch in tonemes:
                if prev_base[0] not in tonemes:
                    i += 1
            
            #If the character is a diacritic which could be either a pre- or post-diacritic
            #Increment the index by 1 if the base of the previous sound is a vowel
            #In order to prevent pre-aspiration/nasalization to be added to a previous vowel
            elif ch in prepost_diacritics:
                if prev_base in vowels:
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
    return ''.join([ch for ch in word if ch not in ['??', '??']])

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

def different_features(seg1, seg2, return_list=False):
    diffs = []
    seg1_id = phone_id(seg1)
    seg2_id = phone_id(seg2)
    for feature in seg1_id:
        if seg2_id[feature] != seg1_id[feature]:
            diffs.append(feature)
    if return_list == True:
        return diffs
    else:
        if len(diffs) > 0:
            print(f'\t\t\t{seg1}\t\t{seg2}')
            for feature in diffs:
                print(f'{feature}\t\t{seg1_id[feature]}\t\t{seg2_id[feature]}')

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

#Cosine similarity: cosine() imported from scipy.spatial.distance

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
    
    #Jaccard index does not allow continuous features
    #Ensure that they are all binarily encoded (any continuous value >0 --> 1)
    for vec in [vec1_values, vec2_values]:
        for i in range(len(vec)):
            if vec[i] > 0:
                vec[i] = 1
                
    return jaccard_score(vec1_values, vec2_values)

def dice_sim(vec1, vec2):
    jaccard = jaccard_sim(vec1, vec2)
    return (2*jaccard) / (1+jaccard)


#Feature Geometry Weights
#Feature weight calculated as ln(n_distinctions) / (tier**2)
#where n_distinctions = (n_sisters+1) + (n_descendants)
feature_geometry = pd.read_csv('Phones/feature_geometry.csv', sep='\t')
feature_geometry['Tier'] = feature_geometry['Path'].apply(lambda x: len(x.split(' | ')))
feature_geometry['Parent'] = feature_geometry['Path'].apply(lambda x: x.split(' | ')[-1])
feature_geometry['N_Sisters'] = feature_geometry['Parent'].apply(lambda x: feature_geometry['Parent'].to_list().count(x))
feature_geometry['N_Descendants'] = feature_geometry['Feature'].apply(lambda x: len([i for i in range(len(feature_geometry)) 
                                                                                     if x in feature_geometry['Path'].to_list()[i].split(' | ')]))
feature_geometry['N_Distinctions'] = (feature_geometry['N_Sisters'] + 1) + (feature_geometry['N_Descendants'])
weights = [math.log(row['N_Distinctions']) / (row['Tier']**2) for index, row in feature_geometry.iterrows()]
total_weights = sum(weights)
normalized_weights = [w/total_weights for w in weights]
feature_geometry['Weight'] = normalized_weights
feature_weights = {feature_geometry.Feature.to_list()[i]:feature_geometry.Weight.to_list()[i]
                   for i in range(len(feature_geometry))}


def weighted_hamming(vec1, vec2, weights=feature_weights):
    diffs = 0
    for feature in vec1:
        if vec1[feature] != vec2[feature]:
            diffs += weights[feature]
    return diffs/len(vec1)


def weighted_jaccard(vec1, vec2, weights=feature_weights):
    union, intersection = 0, 0
    for feature in vec1:
        if ((vec1[feature] == 1) and (vec2[feature] == 1)):
            intersection += weights[feature]
        if ((vec1[feature] == 1) or (vec2[feature] == 1)):
            union += weights[feature]
    return intersection/union
            

def weighted_dice(vec1, vec2, weights=feature_weights):
    w_jaccard = weighted_jaccard(vec1, vec2, weights)
    return (2*w_jaccard) / (1+w_jaccard)





#PHONE COMPARISON
checked_phone_sims = {}
def phone_sim(phone1, phone2, similarity='weighted_dice', exclude_features=[]):
    """Returns the similarity of the features of the two phones according to
    the specified distance/similarity function;
    Features not to be included in the comparison should be passed as a list to
    the exclude_features parameter (by default no features excluded)"""
    
    #If the phone similarity has already been calculated for this pair, retrieve it
    reference = (phone1, phone2, similarity, tuple(exclude_features))
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
    measures = {'cosine':cosine,
                'dice':dice_sim,
                'hamming':hamming_distance,
                'jaccard':jaccard_sim,
                'weighted_cosine':cosine,
                'weighted_dice':weighted_dice,
                'weighted_hamming':weighted_hamming,
                'weighted_jaccard':weighted_jaccard}
    try:
        measure = measures[similarity]
    except KeyError:
        print(f'Error: similarity measure "{similarity}" not recognized!')
        raise KeyError
    
    if similarity not in ['cosine', 'weighted_cosine']:
        score = measure(phone_id1, phone_id2)
    else:
        compare_features = list(phone_id1.keys())
        phone1_values = [phone_id1[feature] for feature in compare_features]
        phone2_values = [phone_id2[feature] for feature in compare_features]
        if similarity == 'weighted_cosine':
            weights = [feature_weights[feature] for feature in compare_features]
            #Subtract from 1: cosine() returns a distance
            score = 1 - measure(phone1_values, phone2_values, w=weights)
        else:
            score = 1 - measure(phone1_values, phone2_values)
    
    #If method is Hamming, convert distance to similarity
    if similarity in ['hamming', 'weighted_hamming']:
        score = 1 - score
        
    #Save the phonetic similarity score to dictionary, return score
    checked_phone_sims[reference] = score
    checked_phone_sims[reference] = score
    return score

def compare_measures(seg1, seg2):
    measures = {}
    for dist_func in ['cosine', 'hamming', 'jaccard', 'dice', 
                   'weighted_cosine', 'weighted_hamming', 'weighted_dice', 'weighted_jaccard']:
        measures[dist_func] = phone_sim(seg1, seg2, dist_func)
    return measures


#WORD-LEVEL PHONETIC COMPARISON AND ALIGNMENT'
def compatible_segments(seg1, seg2):
    """Returns True if the two segments are either:
        two consonants
        two vowels
        a vowel and a sonorant consonant (nasals, liquids, glides)
        two tonemes
    Else returns False"""
    strip_seg1, strip_seg2 = map(strip_diacritics, [seg1, seg2])
    if strip_seg1[0] in consonants:
        if strip_seg2[0] in consonants:
            return True
        elif strip_seg2[0] in vowels:
            if phone_id(seg1)['sonorant'] == 1:
                return True
            else:
                return False
        else:
            return False
    elif strip_seg1[0] in vowels:
        if strip_seg2[0] in vowels:
            return True
        elif strip_seg2[0] in consonants:
            if phone_id(seg2)['sonorant'] == 1:
                return True
            else:
                return False
        else:
            return False
    #Tonemes
    else: 
        if strip_seg2[0] in tonemes:
            return True
        else:
            return False

def align_costs(seq1, seq2, 
                dist_func, sim=False, 
                **kwargs):
    alignment_costs = {}
    for i in range(len(seq1)):
        for j in range(len(seq2)):
            seq1_i, seq2_j = seq1[i], seq2[j]
            cost = dist_func(seq1_i, seq2_j, **kwargs)
            
            #If similarity function, turn into distance and ensure it is negative
            if sim == True:
                if cost > 0:
                    cost = math.log(cost)
                else:
                    cost = -math.inf
            
            alignment_costs[(i, j)] = cost
    return alignment_costs


def phone_align(word1, word2, 
                dist_func=phone_sim, sim=True,
                gop=-0.7,
                added_penalty_dict=None,
                segmented=False,
                **kwargs):
    """Align segments of word1 with segments of word2 according to Needleman-
    Wunsch algorithm, with costs determined by phonetic and sonority similarity;
    If segmented == False, the words are first segmented before being aligned.
    GOP = -1.22 by default, determined by cross-validation on gold alignments."""
    if segmented == False:        
        segments1, segments2 = segment_word(word1), segment_word(word2)
    else:
        segments1, segments2 = word1, word2  
    
    #Combine base distances from distance function with additional penalties, if specified
    if added_penalty_dict != None:
        def added_penalty_dist(seq1, seq2, **kwargs):
            added_penalty = added_penalty_dict[seq1][seq2]
            base_dist = dist_func(seq1, seq2, **kwargs)
            #If similarity function, turn into distance and ensure it is negative
            if sim == True:
                base_dist = -(1 - base_dist)
            return base_dist + added_penalty
        
        alignment_costs = align_costs(segments1, segments2, 
                                      dist_func=added_penalty_dist, sim=False, 
                                      **kwargs)
    
    #Otherwise calculate alignment costs for each segment pair using only the base distance function
    else:
        alignment_costs = align_costs(segments1, segments2, 
                                      dist_func=phone_sim, sim=sim, 
                                      **kwargs)
    
    #Calculate best alignment using Needleman-Wunsch algorithm
    best = best_alignment(SEQUENCE_1=segments1, SEQUENCE_2=segments2,
                          SCORES_DICT=alignment_costs, GAP_SCORE=gop)
    return best


def visual_align(alignment):
    """Renders list of aligned segment pairs as an easily interpretable
    alignment string, with <???> representing null segments,
    e.g.:
    visual_align([('z??', '??'),('v??', 'v'),('??', 'j'),('-', '??a'),('z??', 'z??'),('d??', 'd'),('??a', 'a')])
    = 'z??-?? / v??-v / ??-j / ???-??a / z??-z?? / d??-d / ??a-a' """
    a = []
    for item in alignment:
        if '-' not in item:
            a.append(f'{item[0]}-{item[1]}')
        else:
            if item[0] == '-':
                a.append(f'???-{item[1]}')
            else:
                a.append(f'{item[0]}-???')
    return ' / '.join(a)


def undo_visual_align(visual_alignment):
    """Reverts a visual alignment to a list of tuple segment pairs"""
    seg_pairs = visual_alignment.split(' / ')
    seg_pairs = [tuple(pair.split('-')) for pair in seg_pairs]
    return seg_pairs
    

def reverse_alignment(alignment):
    """Flips the alignment, e.g.:
        reverse_alignment([('s', 's??'), ('o', '??'), ('l', 'l'), ('-', '??'), ('-', 'j')])
        = [('s??', 's'), ('??', 'o'), ('l', 'l'), ('??', '-'), ('j', '-')]"""
    reverse = []
    for pair in alignment:
        reverse.append((pair[1], pair[0]))
    return reverse


