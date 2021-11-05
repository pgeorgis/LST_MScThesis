import pandas as pd
from collections import defaultdict

tree_results = pd.read_csv('/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Trees/Results/tree_evaluation_results.csv')

linkage_GQD = defaultdict(lambda:defaultdict(lambda:0))
c_method_GQD = defaultdict(lambda:defaultdict(lambda:0))
e_method_GQD = defaultdict(lambda:defaultdict(lambda:0))
calibration_GQD = defaultdict(lambda:defaultdict(lambda:0))
n_trees = 0

family_trees = defaultdict(lambda:{})

for i, row in tree_results.iterrows():
    family = row.family
    cognate_method = row.cognate_method
    eval_method = row.eval_method
    tree_type = row.tree_type
    GQD = row.GenQuartetDist
    
    family_trees[family]['/'.join([family, cognate_method, eval_method, tree_type])] = GQD
    
    
    

    
    
#%%    
    cognate_method = row.cognate_method
    if cognate_method != 'gold':
        tree_type = row.tree_type
        if tree_type != 'MaxCladeCredibility':
            n_trees += 1
            GQD = row.GenQuartetDist
            family = row.family
            linkage_GQD[family][tree_type] += GQD
            c_method_GQD[family][cognate_method] += GQD
            eval_method = row.eval_method
            e_method_GQD[family][eval_method] += GQD
            calibration = eval_method.split('-')[1]
            calibration_GQD[family][calibration] += GQD
            