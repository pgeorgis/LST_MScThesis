from auxiliary_functions import create_folder
from load_languages import *
import re
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster, to_tree

#%%
destination = '../Results/Trees/'

functions = {'PMI':(score_pmi, False, 0.36),
             'Surprisal':(surprisal_sim, True, 0.74),
             #'Surprisal2gram':(surprisal_sim, True, 0.69),
             'Phonetic':(word_sim, True, 0.16),
             'Hybrid':(hybrid_similarity, True, 0.57),
             'Levenshtein':(LevenshteinDist, False, 0.73)
             }


#OPTIMAL VALUES FROM VALIDATION DATASETS ON COMMON CONCEPT SET USING BCUBED F1
#PMI: 0.34
#Surprisal unigram: 0.72
#Surprisal bigram: 0.69
#Phonetic_mean_penalties (DEFAULT): 0.15 #THIS IS THE VERSION I USE FOR TREE DRAWING
#Phonetic_summed_penalties: 0.65
#Hybrid similarity: 0.58 (old) / 0.56 (unigram, mean_sim phonetic - DEFAULT) / 0.64 (unigram, total_sim phonetic)
#Levenshtein distance of ASJP: 0.66 

#OPTIMAL VALUES FROM CROSS VALIDATION
#PMI: 0.36
#Surprisal unigram: 0.74
#Surprisal bigram: ? not yet run with CV
#Phonetic_mean_penalties (DEFAULT): 0.16 #THIS IS THE VERSION I USE FOR TREE DRAWING
#Phonetic_summed_penalties: 0.65
#Hybrid similarity: 0.58 (old) / 0.57 (unigram, mean_sim phonetic - DEFAULT) / 0.64 (unigram, total_sim phonetic)
#Levenshtein distance of ASJP: 0.73


#%%
def draw_all_trees(family, newick_directory,
                   concept_list=common_concepts,
                   cognate_types=['auto', 'gold', 'none'],
                   cluster_functions=functions,
                   eval_functions=functions,
                   linkage_methods=['average', 'complete', 'single', 'ward', 'weighted'],
                   min_similarities=[i/100 for i in range(0,51,10)],
                   plot=False, plot_directory=None,
                   load_pmi=True,
                   load_surprisal=True, ngram_size=1):
    if load_pmi == True:
        print(f'Loading {family.name} phoneme PMI...')
        family.load_phoneme_pmi()
    if load_surprisal == True:
        print(f'Loading {family.name} phoneme surprisal ({ngram_size}gram)...')
        family.load_phoneme_surprisal(ngram_size)
        
    if plot == True:
        assert plot_directory != None
    
    #Dendrogram characteristics
    languages = list(family.languages.values()) 
    names = [lang.name for lang in languages]
    concept_list = [c for c in concept_list if len(family.concepts[c]) > 1]
    
    gold, none = False, False
    for cog in cognate_types:
        print(f'Generating {family.name} trees based on {cog.upper()} cognate sets... ')
        
        for cluster_label in cluster_functions:
            if cog == 'auto':
                print(f'\tAutomatic clustering: {cluster_label}')
                cluster_func, cluster_sim, cutoff = cluster_functions[cluster_label]
                clustered_concepts = family.cluster_cognates(concept_list, dist_func=cluster_func,
                                                                 sim=cluster_sim, cutoff=cutoff)
                cluster_id = f'auto-{cluster_label}'
                
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
                                    cluster_id = 'gold'
                else:
                    continue
                
            else:
                if none == False:
                    none = True
                    clustered_concepts = {concept:{concept:[f'{lang} /{family.concepts[concept][lang][i][1]}/'
                                          for lang in family.concepts[concept] 
                                          for i in range(len(family.concepts[concept][lang]))]}
                                          for concept in concept_list}
                    cluster_id = 'none'
                else:
                    continue
            
            for eval_label in eval_functions:
                eval_func, eval_sim = eval_functions[eval_label][:-1]
                
                for calibration, calibration_label in zip([True, False],
                                                          ['calibrated', 'uncalibrated']):
                    print(f'\t\tEvaluation method: {eval_label}-{calibration_label}')
                    
                    for min_sim in min_similarities:
                        dm = distance_matrix(group=languages, 
                                             dist_func=cognate_sim, 
                                             sim=True,
                                             eval_func=eval_func,
                                             eval_sim=eval_sim,
                                             clustered_cognates=clustered_concepts,
                                             calibrate=calibration,
                                             clustered_id=cluster_id,
                                             min_similarity=min_sim)
                        dists = squareform(dm)
                        
                        for method in linkage_methods:                
                            lm = linkage(dists, method, metric='euclidean')
                            newick_tree = linkage2newick(lm, names)
                            newick_tree = re.sub('\s', '_', newick_tree)
                            
                            if cog == 'auto':
                                title = f'{family.name} (Cognates:{cluster_label}, Eval:{eval_label}-{calibration_label}-min_{min_sim}, {method})'
                                newick_title = f'{family.name}_auto-{cluster_label}_{eval_label}-{calibration_label}_min-{min_sim}_{method}.tre'
                            else:
                                title = f'{family.name} (Cognates:{cog}, Eval:{eval_label}-min_{min_sim}, {method})'
                                newick_title = f'{family.name}_{cog}_{eval_label}-{calibration_label}-min_{min_sim}_{method}.tre'
                                
                            with open(f'{newick_directory}/{newick_title}', 'w') as f:
                                f.write(newick_tree)
                            
                            if plot == True:
                                plt.figure(figsize=(10,8))
                                dendrogram(lm, p=30, orientation='left', labels=names)
                                plt.title(title, fontsize=30)
                                plt.savefig(f'{plot_directory}/{title}.png', bbox_inches='tight', dpi=300)
                                plt.show()
                                plt.close()
                            
#%%
for family in families.values():
    plot_directory = family.directory + 'Plots/'
    create_folder(family.name, destination)
    newick_directory = f'{destination}/{family.name}'
    draw_all_trees(family, 
                    newick_directory=newick_directory, 
                    plot=False, plot_directory=plot_directory,
                    load_pmi=True, load_surprisal=True)
