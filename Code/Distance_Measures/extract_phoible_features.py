import os
import pandas as pd
from collections import defaultdict
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
os.chdir(parent_dir)
from phonetic_distance import *
os.chdir(local_dir)

#%%
#LOAD PHOIBLE FEATURE SET
phoible_data = pd.read_csv('Phones/phoible-segments-features.tsv', sep='\t')

phoible_features = set(feature for feature in list(phoible_data.columns) 
                    if feature not in ['segment', 'tone', 'stress'])
#segment column denotes the segment in IPA
#tone column marks whether the character is/is not a tone, rather than a tonal value
#stress: include again later under certain circumstances

#Convert to dictionary of segments with embedded dictionary of features and values
phoible_segments = {list(phoible_data.segment)[i]:{feature:list(phoible_data[feature])[i]
                                                   for feature in phoible_features}
                    for i in range(len(phoible_data))}

tonemes = ['˥','˦','˧','˨','˩','↓']
segment_equivalents = {#Affricates
                       'ʦ':'ts', 
                       'ʣ':'dz',
                       'ʧ':'tʃ',
                       'ʤ':'dʒ',
                       'ʨ':'tɕ',
                       'ʥ':'dʑ',
                       
                       #Clicks
                       'ǀ':'kǀ',
                       'ǁ':'kǁ',
                       'ǂ':'kǂ',
                       'ǃ':'kǃ',
                       'ʘ':'kʘ',
                       
                       #Other
                       'ç':'ç', #apparently not the same character
                       'ɚ':'ə˞' #schwa with rhotacized diacritic
                       #'ɝ':'ɜ˞' #not in phoible segments
                       
                       }

base_segments = list(set(segment for segment in phoible_segments 
                    if len(segment) == 1
                    if segment not in tonemes+['ç']))
other_ch = set(ch for segment in phoible_segments.keys() for ch in segment 
               if ch not in base_segments)


with open('Phones/segments.csv', 'w') as f:
    f.write(','.join(['segment']+list(phoible_features)))
    f.write('\n')
    for segment in base_segments:
        f.write(','.join([segment]+[phoible_segments[segment][feature] for feature in phoible_features]))
        f.write('\n')
    for segment in segment_equivalents:
        base_segments.append(segment)
        equivalent = segment_equivalents[segment]
        phoible_segments[segment] = phoible_segments[equivalent]
        f.write(','.join([segment]+[phoible_segments[equivalent][feature] for feature in phoible_features]))
        f.write('\n')

#%%
#COMPARE WITH MY FEATURES
my_features = set(list(phone_id('t').keys()) + list(phone_id('a').keys()))
common_features = [feature for feature in phoible_features if feature in list(phone_id('t').keys())]
other_phoible_features = [feature for feature in phoible_features if feature not in common_features]
my_other_features = [feature for feature in my_features if feature not in common_features]

#Establish equivalent features between PHOIBLE and my original encoding
feature_equivalents = {feature:feature for feature in common_features}
feature_equivalents['long'] = 'length'
feature_equivalents['periodicGlottalSource'] = 'voice'
feature_equivalents['spreadGlottis'] = 'spread_glottis'
feature_equivalents['constrictedGlottis'] = 'constrict_glottis'
feature_equivalents['distributed'] = 'coronal_dist'
feature_equivalents['anterior'] = 'coronal_anterior'
feature_equivalents['round'] = 'roundedness'
feature_equivalents['delayedRelease'] = 'delayed_release'
feature_equivalents['low'] = 'dorsal_low'
feature_equivalents['back'] = 'dorsal_back'
feature_equivalents['high'] = 'dorsal_high' #height?
feature_equivalents['front'] = 'frontness'

#%%
def lookup_segments(features, values, 
                    segment_list=phoible_segments.keys(), 
                    segment_index=phoible_segments):
    """Returns a list of segments whose feature values match the search criteria"""
    matches = []
    for segment in segment_list:
        match_tallies = 0
        for feature, value in zip(features, values):
            if segment_index[segment][feature] == value:
                match_tallies += 1
        if match_tallies == len(features):
            matches.append(segment)
    return set(matches)

def common_features(segment_list, 
                    start_features=phoible_features,
                    segment_index=phoible_segments):
    """Returns the features/values shared by all segments in the list"""
    features = list(start_features)[:]
    feature_values = defaultdict(lambda:[])
    for seg in segment_list:
        for feature in features:
            value = segment_index[seg][feature]
            if value not in feature_values[feature]:
                feature_values[feature].append(value)
    common = [(feature, feature_values[feature][0]) for feature in feature_values if len(feature_values[feature]) == 1]
    return common

def different_features(seg1, seg2, 
                       segment_index=phoible_segments):
    diffs = []
    seg1_id = segment_index[seg1]
    seg2_id = segment_index[seg2]
    for feature in seg1_id:
        if seg2_id[feature] != seg1_id[feature]:
            diffs.append(feature)
    return diffs

def minimal_pairs(feature, 
                  segment_list=base_segments, 
                  segment_index=phoible_segments):
    """Finds minimal pairs of base segments which are distinguished by a single feature"""
    pairs = []
    checked = []
    for seg1 in segment_list:
        for seg2 in segment_list:
            if seg1 != seg2:
                if (seg2, seg1) not in checked:
                    if different_features(seg1, seg2, segment_index) == [feature]:
                        pairs.append((seg1, seg2))
                        #print(seg1, seg2)
                    checked.append((seg1, seg2))
    return pairs
    
    
    

#%%
#IDENTIFYING FEATURES ASSOCIATED WITH DIACRITICS

diacritics_toadd = ['̀', '̠', '̈', '²', '́', '⁰', '', '̌', 
                    '⁴', '⁵', 'ˌ', '³', '̆', 'ˑ', '¹', '̂']
#need to get representations of these ^^ still


segs_w_diacritics = defaultdict(lambda:[])
for seg in phoible_segments:
    if len(seg) > 1:
        seg_dia = [ch for ch in seg if ch in diacritics+diacritics_toadd]
        if len(seg_dia) == len(seg)-1:
            base_seg = [ch for ch in seg if ch not in seg_dia][0]
            if base_seg in phoible_segments: #some segments only appear with diacritics, so there is no base segment to compare with; skip those
                for dia in seg_dia:
                    segs_w_diacritics[dia].append((seg, base_seg))
            
#Check features which have changed between base segment and segment with diacritic
#for at least some threshold (e.g. 50%) of segments with that diacritic
#Then find the features that all the modified segments have in common
diacritic_features = defaultdict(lambda:defaultdict(lambda:0))
for dia in segs_w_diacritics:
    for item in segs_w_diacritics[dia]:
        dia_seg, base_seg = item
        diff_features = different_features(dia_seg, base_seg)
        for feature in diff_features:
            diacritic_features[dia][feature] += 1
    dia_diff_features = list(diacritic_features[dia].keys())
    for feature in dia_diff_features:
        diacritic_features[dia][feature] /= len(segs_w_diacritics[dia])
        threshold = 0.5
        if diacritic_features[dia][feature] < threshold:
            del diacritic_features[dia][feature]
    diacritic_features[dia] = common_features([ch[0] for ch in segs_w_diacritics[dia]], 
                                              start_features = dia_diff_features)
#some really rare sounds mess up a couple features, plus a couple mistakes
#corrected in Excel sheet

 

#%%   
def write_diacritic_features():        
    with open('Phones/diacritics.csv', 'w') as f:
        f.write(','.join(['Diacritic', 'Feature', 'Value']))
        f.write('\n')
        for diacritic in diacritic_features:
            affected_features = diacritic_features[diacritic]
            for item in affected_features:
                feature, value = item
                f.write(','.join([diacritic, feature, value]))
                f.write('\n')
 
#%%
def create_phone(features='''tone	stress	syllabic	short	long	consonantal	sonorant	continuant	delayedRelease	approximant	tap	trill	nasal	lateral	labial	round	labiodental	coronal	anterior	distributed	strident	dorsal	high	low	front	back	tense	retractedTongueRoot	advancedTongueRoot	periodicGlottalSource	epilaryngealSource	spreadGlottis	constrictedGlottis	fortis	raisedLarynxEjective	loweredLarynxImplosive	click'''.split('\t'),
                 sep='\t'):
    values = []
    for feature in features:
        v = input(f'{feature}:\t')
        values.append(v)
    return sep.join(values)
    
    