#COGNATE CLUSTERING PARAMETER TUNING
import pandas as pd
from load_languages import *
from auxiliary_functions import chunk_list, rescale
import seaborn as sns
sns.set(font_scale=1.0)

#%%
def evaluate_parameters(family, parameters, 
                        dist_func, func_sim, 
                        concept_list=None, 
                        method='bcubed',
                        **kwargs):
    #Designate the concept list as all available concepts with >1 entries
    if concept_list == None:
        concept_list = [concept for concept in family.concepts.keys() 
                        if len(family.concepts[concept]) > 1]
    else:
        concept_list = [concept for concept in concept_list 
                        if len(family.concepts[concept]) > 1]
    
    #Following section accomplishes same as family.cluster_cognates function,
    #but in a more efficient way that doesn't require the linkage matrix to be
    #recalculated each time:
    #Cluster each concept according to each parameter value
    parameter_clusters = defaultdict(lambda:{})
    for concept in sorted(concept_list):
        print(f'\tClustering {family.name} concept "{concept}"...')
        words = [entry[1] for lang in family.concepts[concept] 
                 for entry in family.concepts[concept][lang]]
        lang_labels = [lang for lang in family.concepts[concept] 
                       for entry in family.concepts[concept][lang]]
        labels = [f'{lang_labels[i]} /{words[i]}/' for i in range(len(words))]
        
        #For this function, it requires tuple input of (word, lang)
        langs = [family.languages[lang] for lang in lang_labels]
        words = list(zip(words, langs))
        
        #Calculate distance matrix only once
        lm = linkage_matrix(group=words, dist_func=dist_func, sim=func_sim, **kwargs)
        
        #Iterate through clustering thresholds and generate clusters        
        for value in parameters:
            cluster_labels = fcluster(lm, value, 'distance')
            clusters = defaultdict(lambda:[])
            for item, cluster in sorted(zip(labels, cluster_labels), key=lambda x: x[1]):
                clusters[cluster].append(item)
            parameter_clusters[value][concept] = clusters
     
    #Evaluate clustering results for each parameter value
    print('Evaluating clusters...')
    if method == 'bcubed':
        bcubed_values = {}
        for value in parameters:
            precision, recall, fscore = family.evaluate_clusters(parameter_clusters[value], method='bcubed')
            bcubed_values[value] = precision, recall, fscore
            print(f'\tParameter value = {value} | B-cubed F1 = {round(fscore, 2)}')
        
        return bcubed_values
    
    elif method == 'mcc':
        mcc_values = {}
        for value in parameters:
            mcc = family.evaluate_clusters(parameter_clusters[value], method='mcc')
            mcc_values[value] = mcc
            print(f'\tParameter value = {value} | MCC = {round(mcc, 2)}')
        
        return mcc_values
    
    else:
        print(f'Error: Method "{method}" not recognized for cluster evaluation!')
        raise ValueError


def evaluate_family_parameters(families, parameters, dist_func, func_sim, **kwargs):
    #Evaluate parameters
    family_bcubed = defaultdict(lambda:{})
    for family in families:
        family_bcubed[family.name] = evaluate_parameters(family, parameters, dist_func, func_sim, **kwargs)
        print('\n')
    return family_bcubed


def plot_performance(family_bcubed, func_label, method='bcubed',
                     legend_pos=(0.4,0.4), legend_size=6, save_directory=None):
    assert method in ['bcubed', 'mcc']
    
    #Draw plots of performance per dataset
    for family in sorted(list(family_bcubed.keys())):
        x_values = sorted(list(family_bcubed[family].keys()))
        if method == 'bcubed':
            plt.plot(x_values, [family_bcubed[family][val][2] for val in x_values], label=family)
        else: #mcc
            plt.plot(x_values, [family_bcubed[family][val] for val in x_values], label=family)
    plt.xlabel(f'{func_label} Clustering Threshold')
    
    if method == 'bcubed':
        plt.ylabel('B-Cubed F1 Score')
    else: #mcc
        plt.ylabel('MCC')
        
    plt.xlim([0,1])
    plt.ylim([0,1])
    plt.title(f'{func_label} Cognate Clustering Performance')
    plt.legend(bbox_to_anchor=legend_pos, loc='upper right', prop={'size': legend_size})
    if save_directory != None:    
        plt.savefig(f'{save_directory}{func_label} Cognate Clustering Performance ({method})', dpi=300)
    plt.show()
    plt.close()
    
    #Draw overall average performance over all datasets according to parameters
    precision, recall, f1 = defaultdict(lambda:[]), defaultdict(lambda:[]), defaultdict(lambda:[])
    mcc = defaultdict(lambda:[])
    for family in family_bcubed:
        for x_value in family_bcubed[family]:
            if method == 'bcubed':
                p, r, f = family_bcubed[family][x_value]
                precision[x_value].append(p)
                recall[x_value].append(r)
                f1[x_value].append(f)
            else: #mcc
                mcc[x_value].append(family_bcubed[family][x_value])
    
    if method == 'bcubed':
        for d, l in zip([precision, recall, f1], ['Precision', 'Recall', 'F1']):
            for val in d:
                d[val] = mean(d[val])
            x_values = sorted(list(d.keys()))
            plt.plot(x_values, [d[val] for val in x_values], label=l)
    else: #mcc
        for val in mcc:
            mcc[val] = mean(mcc[val])
        x_values = sorted(list(mcc.keys()))
        plt.plot(x_values, [mcc[val] for val in x_values])
    
    plt.xlabel(f'{func_label} Clustering Threshold')
    if method == 'bcubed':
        plt.ylabel('B-Cubed F1 Score')
        plt.legend(loc='best')
    else: #mcc
        plt.ylabel('MCC')
    plt.xlim([0,1])
    plt.ylim([0,1])
    plt.title(f'Average {func_label} Cognate Clustering Performance')
    if save_directory != None:
        plt.savefig(f'{save_directory}Average {func_label} Cognate Clustering Performance ({method})', dpi=300)
    plt.show()
    plt.close()
    
def optimal_parameter(family_bcubed, method='bcubed'):
    assert method in ['bcubed', 'mcc']

    precision, recall, f1 = defaultdict(lambda:[]), defaultdict(lambda:[]), defaultdict(lambda:[])
    mcc = defaultdict(lambda:[])
    for family in family_bcubed:
        x_values = list(family_bcubed[family].keys())
        scores = [family_bcubed[family][x_value] for x_value in x_values]
        precision_scores = [i[0] for i in scores]
        recall_scores = [i[1] for i in scores]
        f1_scores = [i[2] for i in scores]
        for i in range(len(scores)):
            if method == 'bcubed':
                precision[x_values[i]].append(rescale(precision_scores[i], precision_scores))
                recall[x_values[i]].append(rescale(recall_scores[i], recall_scores))
                f1[x_values[i]].append(rescale(f1_scores[i], f1_scores))
            else: #mcc
                mcc[x_values[i]].append(family_bcubed[family][x_value])
        
        # for x_value in family_bcubed[family]:
        #     if method == 'bcubed':
        #         p, r, f = family_bcubed[family][x_value]
        #         precision[x_value].append(p)
        #         recall[x_value].append(r)
        #         f1[x_value].append(f)
        #     else: #mcc
        #         mcc[x_value].append(family_bcubed[family][x_value])
    
    if method == 'bcubed':
        for d, l in zip([precision, recall, f1], ['Precision', 'Recall', 'F1']):
            for val in d:
                d[val] = mean(d[val])
        return keywithmaxval(f1)
        
    else:
        for val in mcc:
            mcc[val] = mean(mcc[val])
        return keywithmaxval(mcc)
    
    

def write_parameters(parameter_dict, outputfile, sep=',', method='bcubed'):
    with open(outputfile, 'w') as f:
        if method == 'bcubed':
            f.write(sep.join(['Dataset', 'Parameter_Value', 'Precision', 'Recall', 'F1']))
        elif method == 'mcc':
            f.write(sep.join(['Dataset', 'Parameter_Value', 'MCC']))
        f.write('\n')
        for dataset in parameter_dict:
            for parameter_value in parameter_dict[dataset]:
                if method == 'bcubed':
                    precision, recall, fscore = parameter_dict[dataset][parameter_value]
                    f.write(sep.join([dataset, str(parameter_value), str(precision), str(recall), str(fscore)]))
                elif method == 'mcc':
                    mcc = parameter_dict[dataset][parameter_value]
                    f.write(sep.join([dataset, str(parameter_value), str(mcc)]))
                f.write('\n')
                
                
def load_parameter_file(parameter_file):
    parameter_file = pd.read_csv(parameter_file)
    family_bcubed = family_bcubed = defaultdict(lambda:{})
    for index, row in parameter_file.iterrows():
        dataset = row['Dataset']
        value = row['Parameter_Value']
        precision = row['Precision']
        recall = row['Recall']
        f1 = row['F1']
        family_bcubed[dataset][value] = precision, recall, f1
    return family_bcubed

#%%
#Designate validation datasets
#validation_datasets = [Bantu, Hellenic, Japonic, Quechuan, Uto_Aztecan, Vietic]
#test_datasets = [family for family in families.values() if family not in validation_datasets]
all_datasets = list(families.values())
all_datasets.remove(Hokan)

#%%
ngram_size=1
#Load phoneme PMI and surprisal for validation datasets
for vd in all_datasets:
    print(f'Loading {vd.name} phoneme PMI...')
    vd.load_phoneme_pmi()
    print(f'Loading {vd.name} phoneme surprisal...')
    vd.load_phoneme_surprisal(ngram_size=ngram_size)

#%%
#Distance/similarity functions
functions = {'Surprisal':(surprisal_sim, True),
             'PMI':(score_pmi, False),
             'Phonetic':(word_sim, True),
             'Hybrid':(hybrid_similarity, True),
             'Levenshtein':(LevenshteinDist, False),
             #'SyllStrPhonetic':(segmental_word_sim, True),
             #'BasicPhonetic':(basic_word_sim, True),
             #'PhoneticSurprisal':(phonetic_surprisal, True),
             }

#%%
#Evaluate validation datasets for all functions with parameters = [0.0, ..., 1.0]
evaluation = {}
destination = '../Results/Cognate Clustering/Validation/'

#%%
function_labels = list(functions.keys())
method = 'bcubed'

for i in range(len(functions)):
    func_label = function_labels[i]
    if func_label not in evaluation:
        print(f'Evaluating {func_label} parameters...')
        dist_func, func_sim = functions[func_label]
        family_bcubed =  evaluate_family_parameters(all_datasets,
                                                    parameters=[i/100 for i in range(0,101)],
                                                    dist_func=dist_func, func_sim=func_sim,
                                                    concept_list=common_concepts,
                                                    
                                                    #Surprisal/hybrid arguments
                                                    ngram_size=ngram_size,
                                                    
                                                    #Phonetic arguments
                                                    #penalize_infocontent=True,
                                                    #penalize_sonority=False,
                                                    #context_reduction=True,
                                                    #prosodic_env_scaling=False,
                                                    #total_sim=True,
                                                    
                                                    method=method)
        
        #Save evaluation 
        evaluation[func_label] = family_bcubed
        write_parameters(family_bcubed, outputfile=f'{destination}{func_label} Cognate Clustering Performance.csv', 
                         method=method)
        optimum = optimal_parameter(evaluation[func_label], method=method)
        print(f'Best parameter value for {func_label}: {optimum}')
        for family in evaluation[func_label]:
            if method == 'bcubed':
                print(family, round(evaluation[func_label][family][optimum][2], 3))
            else: #mcc.
                print(family, round(evaluation[func_label][family][optimum], 3))
            print('\n')

#%%
#Plot all performances on validation datasets
for func_label in evaluation: 
    plot_performance(evaluation[func_label], func_label, save_directory=destination,
                     legend_pos=(0.9, 0.45), legend_size=3, method=method)
    #optimum = optimal_parameter(evaluation[func_label], method=method)
    #print(f'Best parameter value for {func_label}: {optimum}')
    # for family in evaluation[func_label]:
    #     if method == 'bcubed':
    #         print(family, round(evaluation[func_label][family][optimum][2], 3))
    #     else: #mcc
    #         print(family, round(evaluation[func_label][family][optimum], 3))

# #%%
# #Get performance on test datasets at optimum parameter values
# loaded = defaultdict(lambda:False)

# #%%
# for func_label in functions:
#     optimum = optimal_parameter(evaluation[func_label], method=method)
#     dist_func, func_sim = functions[func_label]
#     for family in test_datasets: 
#         if (loaded[family.name] == False):  
#             print(f'Loading {family.name} phoneme PMI...') 
#             family.load_phoneme_pmi() 
#             print(f'Loading {family.name} phoneme surprisal...') 
#             family.load_phoneme_surprisal(ngram_size=ngram_size)
#             loaded[family.name] = True
    
#     for family in families.values():
#         print(f'Clustering {family.name} words according to {func_label} measure...') 
#         family_clusters = family.cluster_cognates(concept_list=common_concepts,
#                                         dist_func=dist_func, sim=func_sim,
#                                         cutoff=optimum, 
#                                         #ngram_size=ngram_size
#                                         #total_sim=True
#                                         )
        
#         print(f'Writing cognate index file...')
#         create_folder(func_label, '../Results/Cognate Clustering/')
#         family.write_cognate_index(family_clusters,
#                                    output_file=f'../Results/Cognate Clustering/{func_label}/{family.name}_{func_label}-{optimum}_cognates.csv')
        
#         print(f'Evaluating {family.name} cognate clusters...') 
#         family_eval = family.evaluate_clusters(family_clusters, method=method)
#         if method == 'bcubed':
#             print(family.name, round(family_eval[2], 3))
#         else: #mcc
#             print(family.name, round(family_eval, 3)) 
            
#         print('\n')
        
#%%
#Randomly split datasets into k folds for CV
import random
random.seed(7)

#Perform CV for each function
for func_label in evaluation:
    dist_func, func_sim = functions[func_label]
    optima = defaultdict(lambda:[])
    
    for iteration in range(10):
        random.shuffle(all_datasets)
        k = 4
        k_folds = chunk_list(all_datasets, n=k)
        #17 datasets (with Hokan subgroups separated)
        #k = 4 --> 3 folds of 4 datasets, 1 fold of 5 datasets
        #Reassign final single dataset to the penultimate fold
        k_folds[-2].extend(k_folds[-1])
        k_folds = k_folds[:-1]
        
        #Iterate through k folds
        for k in range(len(k_folds)):
            
            #Designate train and hold-out sets
            hold_out = [dataset.name for dataset in k_folds[k]]
            train_sets = []
            for k_i in range(len(k_folds)):
                if k_i != k:
                    train_sets.extend([dataset.name for dataset in k_folds[k_i]])
                    
            #Filter train performances
            evaluation_k = {family:evaluation[func_label][family] 
                            for family in train_sets}
            
            #Get optimum
            optimum = optimal_parameter(evaluation_k, method='bcubed')
            
            #Evaluate hold-out set performance using optimum
            test_performance = [evaluation[func_label][family][optimum][2]
                                for family in hold_out]
            test_performance = mean(test_performance)
            
            #Save performance
            optima[optimum].append(test_performance)
        
    #Determine the optimum clustering value which maximizes the CV hold-out performance
    for o in optima:
        optima[o] = sum(optima[o])
    best_optimum = keywithmaxval(optima)
    
    #Print the best optimum along with the average test performance,
    #and the performance on each individual dataset
    print(f'{func_label.upper()}: {best_optimum}')
    print(f'\tAverage Test F1: {round(optima[best_optimum], 3)}')
    
    for family in sorted([d.name for d in all_datasets]):
        print(f'\t{family}: {round(evaluation[func_label][family][best_optimum][2], 3)}')
        # family = families[family]
        
        # #Re-generate the clusters of cognates at this clustering threshold
        # family_clusters = family.cluster_cognates(concept_list=common_concepts,
        #                                 dist_func=dist_func, sim=func_sim,
        #                                 cutoff=best_optimum, 
        #                                 #ngram_size=ngram_size
        #                                 #total_sim=True
        #                                 )
        # family_score = family.evaluate_clusters(family_clusters)
        # print(f'\t{family}: {round(family_score, 3)}')
        
        # #Save the cognate clusters to file
        # create_folder(func_label, '../Results/Cognate Clustering/')
        # family.write_cognate_index(family_clusters,
        #                             output_file=f'../Results/Cognate Clustering/{func_label}/{family.name}_{func_label}-{best_optimum}_cognates.csv')
    print('\n')


