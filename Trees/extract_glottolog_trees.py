#NOTE: a clone of the Glottolog GitHub repository must be saved in the same directory
#Link: https://github.com/glottolog/glottolog

#Load Glottolog data
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
          
#Extract each family's Glottolog tree in Newick format and write to a .tre file
for family in family_roots:
    root = family_roots[family]
    print(f'Extracting {family} tree...')
    newick_tree = Glottolog.newick_tree(glottolog, start=root)
    with open(f'Gold/{family}.tre', 'w') as f:
        f.write(newick_tree)