from auxiliary_functions import create_folder
from load_languages import *
import re
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster, to_tree

#%%
destination = '/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Trees/Results/'

functions = {'PMI':(score_pmi, False, 0.36),
             'Surprisal':(surprisal_sim, True, 0.78),
             'Phonetic':(word_sim, True, 0.23) 
             }


#OPTIMAL VALUES FROM VALIDATION DATASETS ON COMMON CONCEPT SET
#PMI: 0.36
#Surprisal: 0.78
#Phonetic: 0.23

#%%
combined_functions = {}
combined_labels = []
for i in range(101):
    for j in range(100-i):
        k = 100 - i - j
        #print(i, j, k)
        #i, j, k = round(i/100, 2), round(j/100, 2), round(k/100, 2)
        label = f'PMI-{round(i/100, 2)}_Surprisal-{round(j/100, 2)}_Phonetic-{round(k/100, 2)}'
        #print(label)
        
        def combined(lang1, lang2, clustered_cognates, **kwargs): 
            return combined_cognate_sim(lang1, lang2, clustered_cognates, 
                                        eval_funcs=[score_pmi, surprisal_sim, word_sim], 
                                        eval_sims=[False, True, True], 
                                        weights=[i/100, j/100, k/100], **kwargs)
        combined_functions[label] = combined
        combined_labels.append(label)

#%%
plot = False
for family in families:
    family = families[family]
    print(f'Loading {family.name} phoneme PMI...')
    family.load_phoneme_pmi()
    print(f'Loading {family.name} phoneme surprisal...')
    family.load_phoneme_surprisal()
    create_folder('Plots', family.directory)
    create_folder(family.name, destination)
    
    #Dendrogram characteristics
    languages = list(family.languages.values()) 
    names = [lang.name for lang in languages]
    concept_list = [c for c in common_concepts if len(family.concepts[c]) > 1]
    
    gold, none = False, False
    for cog in ['auto', 'gold', 'none']:
        print(f'Generating trees based on {cog.upper()} cognate sets... ')
        
        for cluster_label in functions:
            if cog == 'auto':
                print(f'\tAutomatic clustering: {cluster_label}')
                cluster_func, cluster_sim, cutoff = functions[cluster_label]
                clustered_concepts = family.cluster_cognates(concept_list, dist_func=cluster_func,
                                                                 sim=cluster_sim, cutoff=cutoff)
                
            elif cog == 'gold':
                if gold == False:
                    gold = True
                    clustered_concepts = defaultdict(lambda:defaultdict(lambda:[]))
                    for concept in concept_list:
                        cognate_ids = [cognate_id for cognate_id in family.cognate_sets 
                                       if cognate_id.split('_')[0] == concept]
                        for cognate_id in cognate_ids:
                            for lang in family.cognate_sets[cognate_id]:
                                for form in family.cognate_sets[cognate_id][lang]:
                                    form = strip_ch(form, ['(', ')'])
                                    clustered_concepts[concept][cognate_id].append(f'{lang} /{form}/')
                else:
                    continue
                
            else:
                if none == False:
                    none = True
                    clustered_concepts = {concept:{concept:[f'{lang} /{family.concepts[concept][lang][i][1]}/'
                                          for lang in family.concepts[concept] 
                                          for i in range(len(family.concepts[concept][lang]))]}
                                          for concept in concept_list}
                else:
                    continue
            
            for eval_label in functions:
                print(f'\t\tEvaluation method: {eval_label}')
                
                eval_func, eval_sim = functions[eval_label][:-1]
                
                dm = distance_matrix(group=languages, 
                                     dist_func=cognate_sim, 
                                     sim=True,
                                     eval_func=eval_func,
                                     eval_sim=eval_sim,
                                     clustered_cognates=clustered_concepts)
                dists = squareform(dm)
                
                for method in ['complete', 'weighted', 'ward', 'average']:                
                    linkage_matrix = linkage(dists, method, metric='euclidean')
                    newick_tree = linkage2newick(linkage_matrix, names)
                    newick_tree = re.sub('\s', '_', newick_tree)
                    
                    if cog == 'auto':
                        title = f'{family.name} (Cognates:{cluster_label}, Eval:{eval_label}, {method})'
                        newick_title = f'{family.name}_auto-{cluster_label}_{eval_label}_{method}.tre'
                    else:
                        title = f'{family.name} (Cognates:{cog}, Eval:{eval_label}, {method})'
                        newick_title = f'{family.name}_{cog}_{eval_label}_{method}.tre'
                        
                    with open(f'{destination}/{family.name}/{newick_title}', 'w') as f:
                        f.write(newick_tree)
                    
                    if plot == True:
                        plt.figure(figsize=(10,8))
                        dendrogram(linkage_matrix, p=30, orientation='left', labels=names)
                        plt.title(title, fontsize=30)
                        save_directory = family.directory + 'Plots/'
                        plt.savefig(f'{save_directory}{title}.png', bbox_inches='tight', dpi=300)
                        plt.show()
                        plt.close()
                    
    print('\n')

#%%
plot = False
for family in families:
    family = families[family]
    print(f'Loading {family.name} phoneme PMI...')
    # family.load_phoneme_pmi()
    print(f'Loading {family.name} phoneme surprisal...')
    # family.load_phoneme_surprisal()
    # create_folder('Plots', family.directory)
    # create_folder(family.name, destination)
    
    #Dendrogram characteristics
    languages = list(family.languages.values()) 
    names = [lang.name for lang in languages]
    concept_list = [c for c in common_concepts if len(family.concepts[c]) > 1]
    
    gold, none = False, False
    for cog in ['auto', 'gold', 'none']:
        print(f'Generating trees based on {cog.upper()} cognate sets... ')
        
        for cluster_label in functions:
            if cog == 'auto':
                print(f'\tAutomatic clustering: {cluster_label}')
                cluster_func, cluster_sim, cutoff = functions[cluster_label]
                clustered_concepts = family.cluster_cognates(concept_list, dist_func=cluster_func,
                                                                 sim=cluster_sim, cutoff=cutoff)
                
            elif cog == 'gold':
                if gold == False:
                    gold = True
                    clustered_concepts = defaultdict(lambda:defaultdict(lambda:[]))
                    for concept in concept_list:
                        cognate_ids = [cognate_id for cognate_id in family.cognate_sets 
                                       if cognate_id.split('_')[0] == concept]
                        for cognate_id in cognate_ids:
                            for lang in family.cognate_sets[cognate_id]:
                                for form in family.cognate_sets[cognate_id][lang]:
                                    form = strip_ch(form, ['(', ')'])
                                    clustered_concepts[concept][cognate_id].append(f'{lang} /{form}/')
                else:
                    continue
                
            else:
                if none == False:
                    none = True
                    clustered_concepts = {concept:{concept:[f'{lang} /{family.concepts[concept][lang][i][1]}/'
                                          for lang in family.concepts[concept] 
                                          for i in range(len(family.concepts[concept][lang]))]}
                                          for concept in concept_list}
                else:
                    continue
            
            for syn, syn_label in zip([True, False], ['nosyn', 'syn']):
                dm = distance_matrix(group=languages, 
                                     dist_func=binary_cognate_sim, 
                                     sim=True,
                                     clustered_cognates=clustered_concepts,
                                     exclude_synonyms=syn)
                dists = squareform(dm)
                
                for method in ['complete', 'weighted', 'ward', 'average']:                
                    linkage_matrix = linkage(dists, method, metric='euclidean')
                    newick_tree = linkage2newick(linkage_matrix, names)
                    newick_tree = re.sub('\s', '_', newick_tree)
                    
                    if cog == 'auto':
                        title = f'{family.name} (Cognates:{cluster_label}, Eval:binary-{syn_label}, {method})'
                        newick_title = f'{family.name}_auto-{cluster_label}_binary-{syn_label}_{method}.tre'
                    else:
                        title = f'{family.name} (Cognates:{cog}, Eval:binary-{syn_label}, {method})'
                        newick_title = f'{family.name}_{cog}_binary-{syn_label}_{method}.tre'
                        
                    with open(f'{destination}/{family.name}/{newick_title}', 'w') as f:
                        f.write(newick_tree)
                    
                    if plot == True:
                        plt.figure(figsize=(10,8))
                        dendrogram(linkage_matrix, p=30, orientation='left', labels=names)
                        plt.title(title, fontsize=30)
                        save_directory = family.directory + 'Plots/'
                        plt.savefig(f'{save_directory}{title}.png', bbox_inches='tight', dpi=300)
                        plt.show()
                        plt.close()
                    
    print('\n')
    
#%%
plot = False
for family in families:
    family = families[family]
    print(f'Loading {family.name} phoneme PMI...')
    family.load_phoneme_pmi()
    print(f'Loading {family.name} phoneme surprisal...')
    family.load_phoneme_surprisal()
    create_folder(family.name, destination)
    
    #Dendrogram characteristics
    languages = list(family.languages.values()) 
    names = [lang.name for lang in languages]
    concept_list = [c for c in common_concepts if len(family.concepts[c]) > 1]
    
    gold, none = False, False
    for cog in ['auto', 'gold', 'none']:
        print(f'Generating trees based on {cog.upper()} cognate sets... ')
        
        for cluster_label in functions:
            if cog == 'auto':
                print(f'\tAutomatic clustering: {cluster_label}')
                cluster_func, cluster_sim, cutoff = functions[cluster_label]
                clustered_concepts = family.cluster_cognates(concept_list, dist_func=cluster_func,
                                                                 sim=cluster_sim, cutoff=cutoff)
                cog += f'_{cluster_label}'
                
            elif cog == 'gold':
                if gold == False:
                    gold = True
                    clustered_concepts = defaultdict(lambda:defaultdict(lambda:[]))
                    for concept in concept_list:
                        cognate_ids = [cognate_id for cognate_id in family.cognate_sets 
                                       if cognate_id.split('_')[0] == concept]
                        for cognate_id in cognate_ids:
                            for lang in family.cognate_sets[cognate_id]:
                                for form in family.cognate_sets[cognate_id][lang]:
                                    form = strip_ch(form, ['(', ')'])
                                    clustered_concepts[concept][cognate_id].append(f'{lang} /{form}/')
                else:
                    continue
                
            else:
                if none == False:
                    none = True
                    clustered_concepts = {concept:{concept:[f'{lang} /{family.concepts[concept][lang][i][1]}/'
                                          for lang in family.concepts[concept] 
                                          for i in range(len(family.concepts[concept][lang]))]}
                                          for concept in concept_list}
                else:
                    continue
                
            for combined_function_label in combined_functions:
                print(f'\t\tEvaluation method: {combined_function_label}')
                combined_function = combined_functions[combined_function_label]
                dm = distance_matrix(group=languages, 
                                     dist_func=combined_function, 
                                     sim=True,
                                     clustered_cognates=clustered_concepts,
                                     clustered_id=cog)
                
                dists = squareform(dm)
                
                for method in ['complete', 'weighted', 'ward', 'average']:                
                    linkage_matrix = linkage(dists, method, metric='euclidean')
                    newick_tree = linkage2newick(linkage_matrix, names)
                    newick_tree = re.sub('\s', '_', newick_tree)
                    
                    if cog == 'auto':
                        title = f'{family.name} (Cognates:{cluster_label}, Eval:{combined_function_label}, {method})'
                        newick_title = f'{family.name}_auto-{cluster_label}_{combined_function_label}_{method}.tre'
                    else:
                        title = f'{family.name} (Cognates:{cog}, Eval:{combined_function_label}, {method})'
                        newick_title = f'{family.name}_{cog}_{combined_function_label}_{method}.tre'
                        
                    with open(f'{destination}/{family.name}/{newick_title}', 'w') as f:
                        f.write(newick_tree)
                    
                    if plot == True:
                        plt.figure(figsize=(10,8))
                        dendrogram(linkage_matrix, p=30, orientation='left', labels=names)
                        plt.title(title, fontsize=30)
                        save_directory = family.directory + 'Plots/'
                        plt.savefig(f'{save_directory}{title}.png', bbox_inches='tight', dpi=300)
                        plt.show()
                        plt.close()
                    
    print('\n')
