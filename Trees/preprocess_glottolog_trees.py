import os, re
import pandas as pd
from pathlib import Path
local_dir = Path(os.getcwd())
parent_dir = local_dir.parent

#Load CSV of language metadata
language_metadata = pd.read_csv(str(parent_dir) + '/Datasets/Languages.csv', sep='\t')

#Create dictionary mapping of Glottolog names to distinctive names used in present study
language_lookup = {language_metadata['Glottolog Name'][i]:language_metadata.Name[i]
                   for i in range(len(language_metadata))}

#Print a warning about each language which doesn't have a unique Glottocode
for i in range(len(language_metadata)):
    name = language_metadata.Name[i]
    glottocode = language_metadata.Glottocode[i]
    glottocode_count = language_metadata.Glottocode.tolist().count(glottocode)
    if glottocode_count > 1:
        print(f'Warning! {name} [{glottocode}] does not have a unique Glottocode!')
print('\n')


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
    
    #Write a copy of the original Glottolog tree in Newick format before making changes
    with open(f'Gold/{family}.tre', 'w') as f:
        f.write(newick_tree)
    
    #Then preprocess the Glottolog tree
    #Split by the brackets containing the Glottocodes, and possible ISO codes if present
    #Also strip the "-l-" annotation which sometimes follows
    #Take only the Glottolog name which precedes all of these
    modified_newick = re.sub(' (\[\w+\])+(-l-)*', '', newick_tree)
    
    #Remove apostrophes surrounding languoid names and rename to new names
    #Some names include apostrophes, e.g. "Xi'an Mandarin", "Langues d'Oil", etc.
    #In these cases, the apostrophe is written as a double apostrophe, "''"
    #To avoid removing apostophes which are part of language names, first 
    #convert double apostrophes "''" to "~~"
    modified_newick = re.sub("''", '~~', modified_newick)
    
    #Isolate the languoid names by splitting by the apostrophes that surround them    
    glottolog_names = modified_newick.split("'")
    
    #Convert the languoid names to the distinctive names chosen by me, when available
    new_names = []
    for name in glottolog_names:
        
        #Glottolog names include curly brackets instead of parentheses;
        #convert these to parentheses in order to have the same form as listed in the dictionary
        fix_name = re.sub('{', '(', name)
        fix_name = re.sub('}', ')', fix_name)
        
        #Do the same with the names which previously contained apostrophes: "~~" --> "'"
        fix_name = re.sub('~~', "'", fix_name)
        
        try:
            #If the Glottolog name is in the dictionary, retrieve its new name
            new_name = language_lookup[fix_name]
            
            #Because parentheses are required as part of Newick formatting, 
            #change any parentheses in new language names to curly brackets
            new_name = re.sub('\(', '{', new_name)
            new_name = re.sub('\)', '}', new_name)
            
            #Rename the languoid by adding the modified name to the new name list
            new_names.append(new_name)
        
        #Don't change the name if not in the dictionary
        #(it is either a node/group label or language not included in dataset)
        except KeyError:
            new_names.append(name)
    
    #Rejoin into Newick format
    modified_newick = ''.join(new_names)

    #Then convert "~~" back to single apostrophes "'"
    modified_newick = re.sub("~~", "'", modified_newick)
    
    with open(f'Gold/{family}_preprocessed.tre', 'w') as f:
        f.write(modified_newick)