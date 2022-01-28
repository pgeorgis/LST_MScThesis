import pandas as pd
from collections import defaultdict

tree_results = pd.read_csv('/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Results/Trees/tree_evaluation_results.csv')
family_trees = defaultdict(lambda:{})
mcc_trees = defaultdict(lambda:{})

cognate_method_scores = defaultdict(lambda:[])
eval_method_scores = defaultdict(lambda:[])
calibration_scores = defaultdict(lambda:[])
method_scores = defaultdict(lambda:[])
linkage_scores = defaultdict(lambda:[])
min_sim_scores = defaultdict(lambda:[])

for i, row in tree_results.iterrows():
    family = row.family
    cognate_method = row.cognate_method
    eval_method = row.eval_method
    tree_type = row.tree_type
    GQD = row.GenQuartetDist
    min_sim = row.min_similarity
    if tree_type != 'MaxCladeCredibility':
        #method_scores['/'.join([cognate_method, eval_method, tree_type])].append(GQD)
        eval_method1, calibration_method = eval_method.split('-')
        method_scores['/'.join([cognate_method, eval_method1])].append(GQD)
        linkage_scores[tree_type].append(GQD)
        cognate_method_scores[cognate_method].append(GQD)
        eval_method_scores[eval_method1].append(GQD)
        calibration_scores[calibration_method].append(GQD)
        min_sim_scores[min_sim].append(GQD)
        family_trees[family]['/'.join([family, cognate_method, eval_method, min_sim, tree_type])] = GQD
    else:
        mcc_trees[family]['/'.join([family, cognate_method, eval_method, tree_type])] = GQD
    
    
method_avg_scores = {method:mean(method_scores[method]) for method in method_scores}
auto_avg_scores = {method:mean(method_scores[method]) for method in method_scores if 'gold' not in method}

#%%
linkage_GQD = defaultdict(lambda:defaultdict(lambda:[]))
c_method_GQD = defaultdict(lambda:defaultdict(lambda:[]))
e_method_GQD = defaultdict(lambda:defaultdict(lambda:[]))
min_sim_GQD = defaultdict(lambda:defaultdict(lambda:[]))
n_trees = 0

auto_cognate_sets = defaultdict(lambda:[])

gold_evals = defaultdict(lambda:[])
auto_evals = defaultdict(lambda:[])
none_evals = defaultdict(lambda:[])

combo_methods = defaultdict(lambda:[])

best_auto_cognate_sets = defaultdict(lambda:[])
best_auto_evals = defaultdict(lambda:[])


for family in sorted(list(family_trees.keys())):
    print(f'{family.upper()} - {len(family_trees[family])} total trees')
    gold_trees = {tree:family_trees[family][tree] for tree in family_trees[family] if 'gold' in tree}
    none_trees = {tree:family_trees[family][tree] for tree in family_trees[family] if 'none' in tree}
    auto_trees = {tree:family_trees[family][tree] for tree in family_trees[family] if 'MaxCladeCredibility' not in tree if tree not in gold_trees if tree not in none_trees}
    print(f'\tBest Auto Tree: {round(min(auto_trees.values()),3)}')
    print(f'\tBest None Tree: {round(min(none_trees.values()),3)}')
    print(f'\tBest Gold Tree: {round(min(none_trees.values()),3)}')
    
    for tree_d, eval_d in zip([gold_trees, none_trees, auto_trees],
                              [gold_evals, none_evals, auto_evals]):
        for method in ['Phonetic', 'PMI', 'Surprisal', 'Hybrid']:
            combo_method = {}
            for tree in tree_d:
                if method in tree.split('/')[2]:
                    combo_method[tree] = tree_d[tree]
            eval_d[family].append(round(min(combo_method.values()),3))
    
    for method in ['Phonetic', 'PMI', 'Surprisal', 'Hybrid']:
        cog_method = {}
        for tree in auto_trees:
            if method == tree.split('/')[1]:
                cog_method[tree] = auto_trees[tree]
        auto_cognate_sets[family].append(round(min(cog_method.values()),3))
        
    for method1 in ['Phonetic', 'PMI', 'Surprisal', 'Hybrid']:
        for method2 in ['Phonetic', 'PMI', 'Surprisal', 'Hybrid']:
            combo_method = {}
            for tree in auto_trees:
                if method1 == tree.split('/')[1]:
                    if method2 == tree.split('/')[2].split('-')[0]:
                        combo_method[tree] = auto_trees[tree]
            combo_methods[family].append(round(min(combo_method.values()),3))
            
    
    for tree in family_trees[family]:
        f, cognate_method, eval_method, min_sim, linkage_method = tree.split('/')
        if linkage_method != 'MaxCladeCredibility':
            GQD = family_trees[family][tree]
            linkage_GQD[family][linkage_method].append(GQD)
            c_method_GQD[family][cognate_method].append(GQD)
            e_method_GQD[family][eval_method].append(GQD)
            min_sim_GQD[family][min_sim].append(GQD)
            
    #Get methods used for best auto trees
    best_score = min(auto_trees.values())
    best_trees = [tree for tree in auto_trees if auto_trees[tree] <= best_score]
    for tree in best_trees:
        elements = tree.split('/')
        cognate_method = elements[1]
        eval_method = elements[2].split('-')[0]
        best_auto_cognate_sets[cognate_method].append(family)
        best_auto_evals[eval_method].append(family)
    
    print('\n')


#%%
methods_GQD = defaultdict(lambda:[])
for c_method in c_method_GQD['Arabic']:
    for family in family_trees: 
        methods_GQD[c_method].extend(c_method_GQD[family][c_method])
        
#%%
mcc_analysis = defaultdict(lambda:defaultdict(lambda:[]))

for family in mcc_trees:
    for tree_id in mcc_trees[family]:
        score = mcc_trees[family][tree_id]
        tree_id = tree_id.split('/')[1:-1]
        tree_id[1] = tree_id[1].split('-')[0]
        if tree_id[0] == 'gold':
            mcc_analysis[family][tree_id[1]].append(score)
    for method in mcc_analysis[family]:
        mcc_analysis[family][method] = min(mcc_analysis[family][method])

#%%
best_trees = defaultdict(lambda:defaultdict(lambda:[]))

for family in family_trees:
    for tree_id in family_trees[family]:
        score = family_trees[family][tree_id]
        tree_id = tree_id.split('/')[1:-2]
        tree_id[1] = tree_id[1].split('-')[0]
        if tree_id[0] == 'gold':
            best_trees[family][tree_id[1]].append(score)
    for method in best_trees[family]:
        best_trees[family][method] = min(best_trees[family][method])
        
for method in ['Phonetic', 'PMI', 'Surprisal', 'Hybrid', 'Levenshtein']:
    print(method.upper())
    for family in best_trees:
        print(best_trees[family][method])
    print('\n')

