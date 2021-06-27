import os
from collections import defaultdict
import pandas as pd
from nltk import edit_distance
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent

#Load file with cognate coding from Indo-European Lexical Cognacy Database (IELex)
#Downloaded from: https://pappubahry.com/maps/ie_cognates/details.html
ie_cognates = pd.read_csv('Source/IE_cognates/long_list_utf8wobom.csv')

#Get the language codes from this dataset
ie_langs = pd.read_csv('Source/IE_cognates/language_codes.csv')
ie_langs = {ie_langs.lang_ielex[i]:ie_langs.lang_me[i] for i in range(len(ie_langs))}
#Manually rename some languages 'Serbo-Croatian' --> 'Croatian'
ie_langs['Serbocroatian'] = 'Croatian'

#Rename the languages in IELex cognate file to use 'lang_me' name
ie_cognates.language = ie_cognates.language.apply(lambda x: ie_langs.get(x, x))


#Load Concepticon mapping
ielex_concepticon = pd.read_csv('Source/IE_cognates/Concept_list_Dunn_2012_207.csv', sep='\t')
concepticon_mapping = {ielex_concepticon['Name'][i].split(' [')[0]:ielex_concepticon['Parameter'][i]
                       for i in range(len(ielex_concepticon))}


#Convert the concepts in the IELex file to Concepticon glosses
ie_cognates.word = ie_cognates.word.apply(lambda x: concepticon_mapping[x])


#Get a list of the languages in Balto-Slavic dataset
baltoslavic_langs = pd.read_csv('languages.csv')


#Load the Balto-Slavic data file
baltoslavic_data = pd.read_csv('balto_slavic_data.csv', sep='\t')
baltoslavic_data_concepts = set(baltoslavic_data.Parameter_ID)


#Filter the ie_cognates dataframe to only include Balto-Slavic languages
ie_cognates = ie_cognates[ie_cognates.language.isin(list(baltoslavic_langs.Name))]


#Also filter to only include concepts which are in the Balto-Slavic dataset
ie_cognates = ie_cognates[ie_cognates.word.isin(baltoslavic_data_concepts)]


#Write csv with modified cognate class data
ie_cognates.to_csv('balto_slavic_cognate_classes.csv')

#Create a dictionary with keys = (language, concept), values = [orthography]
baltoslavic_dict = defaultdict(lambda:[])
for i in range(len(baltoslavic_data)):
    concept = baltoslavic_data.Parameter_ID[i]
    if concept in set(ie_cognates.word):
        lang = baltoslavic_data.Language_ID[i]
        orth = baltoslavic_data.Value[i]
        tr = baltoslavic_data.Form[i]
        baltoslavic_dict[(lang, concept)].append([orth, tr])

#Then combine with the words and cognate codes from ie_cognates into a new dictionary
#Add them to the entry whose orth has the smallest length-normalized Levenshtein distance
def nz_lev_dist(str1, str2):
    """Calculates the length-normalized Levenshtein distance between two strings"""
    return edit_distance(str1, str2)/max(len(str1), len(str2))

def keywithminval(d):
    """Returns the dictionary key with the lowest value"""
    v = list(d.values())
    k = list(d.keys())
    return k[v.index(min(v))]

baltoslavic_codes = defaultdict(lambda:[])
for i in range(len(ie_cognates)):
    lang = list(ie_cognates.language)[i]
    concept = list(ie_cognates.word)[i]
    value = list(ie_cognates.lang_word)[i].lower()
    cognate_class = list(ie_cognates['class'])[i]
    dists = {}
    for j in range(len(baltoslavic_dict[(lang, concept)])):
        entry = baltoslavic_dict[(lang, concept)][j]
        orth, tr = entry
        dist = min(nz_lev_dist(orth, value), nz_lev_dist(tr, value))
        dists[j] = dist
    index = keywithminval(dists)
    min_dist = dists[index]
    best_match = baltoslavic_dict[(lang, concept)][index]
    baltoslavic_codes[(lang, concept)].append(best_match+[value, cognate_class, min_dist])

#Write csv with results of matching
with open('baltoslavic_matched_cognate_classes.csv', 'w') as f:
    f.write('\t'.join(['Language', 'Concept', 'Value', 'Form', 'IE_Lex', 'Cognate_Class', 'LevDist']))
    f.write('\n')
    for key in baltoslavic_codes:
        lang, concept = key
        for entry in baltoslavic_codes[key]:
            value, form, ie_lex, cognate_class, LD = entry
            f.write('\t'.join([str(i) for i in [lang, concept, value, form, ie_lex, cognate_class, LD]]))
            f.write('\n')
    



