#NOTE: a clone of the Glottolog GitHub repository must be saved in the same directory
#Link: https://github.com/glottolog/glottolog

import os, re
from collections import defaultdict
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
grandparent_dir = parent_dir.parent

#%%
from pyglottolog import Glottolog
glottolog = Glottolog('glottolog/.')


#Extract Newick trees for each family
arabic = Glottolog.newick_tree(glottolog, start='arab1395')
baltoslavic = Glottolog.newick_tree(glottolog, start='balt1263')
italic = Glottolog.newick_tree(glottolog, start='lati1263')
polynesian = Glottolog.newick_tree(glottolog, start='poly1242')
sinitic = Glottolog.newick_tree(glottolog, start='sini1245')
turkic = Glottolog.newick_tree(glottolog, start='turk1311')
uralic = Glottolog.newick_tree(glottolog, start='ural1272')

#%%
#Load list of families and their roots
family_roots = {}
with open('family_roots.txt') as f:
    f = f.readlines()
    for line in f:
        line = line.strip().split(":")
        family, root = line
        family_roots[family] = root
        
#%%   
#Write each Newick tree to a .tre file
for family in family_roots:
    root = family_roots[family]
    newick_tree = Glottolog.newick_tree(glottolog, start=root)
    with open(f'Gold/{family}.tre', 'w') as f:
        f.write(newick_tree)