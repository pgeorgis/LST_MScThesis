import os, re
import pandas as pd
from pathlib import Path
local_dir = Path(os.getcwd())
parent_dir = local_dir.parent

#Load CSV of language metadata
language_metadata = pd.read_csv(str(parent_dir) + '/Datasets/Languages.csv', sep='\t')

#Create dictionary mapping of Glottocodes to local language IDs
language_lookup = {language_metadata.Glottocode[i]:language_metadata.Name[i]
                   for i in range(len(language_metadata))}

#Print a warning about each language which doesn't have a unique Glottocode
for i in range(len(language_metadata)):
    name = language_metadata.Name[i]
    glottocode = language_metadata.Glottocode[i]
    glottocode_count = language_metadata.Glottocode.tolist().count(glottocode)
    if glottocode_count > 1:
        print(f'Warning! {name} [{glottocode}] does not have a unique Glottocode!')



#Load Glottolog data
#NOTE: a clone of the Glottolog GitHub repository must be saved in the same directory
#Link: https://github.com/glottolog/glottolog
from pyglottolog import Glottolog
glottolog = Glottolog('glottolog/.')

#Load list of families and the Glottocodes of their roots
family_roots = {}
with open('family_roots.txt') as f:
    f = f.readlines()
    for line in f:
        line = line.strip().split(":")
        family, root = line
        family_roots[family] = root
          
#%%
#Extract each family's Glottolog tree in Newick format and write to a .tre file
for family in family_roots:
    root = family_roots[family]
    print(f'Extracting {family} tree...')
    newick_tree = Glottolog.newick_tree(glottolog, start=root)
    
    #Split by the brackets containing the Glottocodes, and possible ISO codes if present
    #Also strip the "-l-" annotation which sometimes follows
    #Take only the Glottolog name which precedes all of these
    modified_newick = re.sub(' (\[\w+\])+(-l-)*', '', newick_tree)
    
    #Remove apostrophes from language names
    #Some languages' names include apostrophes, e.g. "Xi'an Mandarin"
    #In these cases, the apostrophe is written as a double apostrophe, "''"
    #To avoid removing apostophes which are part of language names, first 
    #convert double apostrophes "''" to "~~"
    #Then remove all remaining apostrophes
    #Then convert "~~" back to single apostrophes "'"
    modified_newick = re.sub("''", '~~', modified_newick)
    modified_newick = re.sub("'", "", modified_newick)
    modified_newick = re.sub("~~", "'", modified_newick)
    
    with open(f'Gold/{family}.tre', 'w') as f:
        f.write(modified_newick)