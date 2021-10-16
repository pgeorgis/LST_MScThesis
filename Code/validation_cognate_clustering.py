#COGNATE CLUSTERING PARAMETER TUNING
import pandas as pd
from load_languages import *
import seaborn as sns
sns.set(font_scale=1.0)

#%%
def evaluate_parameters(family, parameters, 
                        dist_func, func_sim, 
                        concept_list=None, **kwargs):
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
    bcubed_values = {}
    for value in parameters:
        precision, recall, fscore = family.evaluate_clusters(parameter_clusters[value])
        bcubed_values[value] = precision, recall, fscore
        print(f'\tParameter value = {value} | B-cubed F1 = {round(fscore, 2)}')
    
    return bcubed_values


def evaluate_family_parameters(families, parameters, dist_func, func_sim, **kwargs):
    #Evaluate parameters
    family_bcubed = defaultdict(lambda:{})
    for family in families:
        family_bcubed[family.name] = evaluate_parameters(family, parameters, dist_func, func_sim, **kwargs)
        print('\n')
    return family_bcubed


def plot_performance(family_bcubed, func_label, 
                     legend_pos=(0.4,0.4), save_directory=None):
    
    #Draw plots of performance per dataset
    for family in sorted(list(family_bcubed.keys())):
        x_values = sorted(list(family_bcubed[family].keys()))
        plt.plot(x_values, [family_bcubed[family][val][2] for val in x_values], label=family)
    plt.xlabel(f'{func_label} Clustering Threshold')
    plt.ylabel('B-Cubed F1 Score')
    plt.xlim([0,1])
    plt.ylim([0,1])
    plt.title(f'{func_label} Cognate Clustering Performance')
    plt.legend(bbox_to_anchor=legend_pos, loc='upper right', prop={'size': 6})
    if save_directory != None:    
        plt.savefig(f'{save_directory}{func_label} Cognate Clustering Performance', dpi=300)
    plt.show()
    plt.close()
    
    #Draw overall average performance over all datasets according to parameters
    precision, recall, f1 = defaultdict(lambda:[]), defaultdict(lambda:[]), defaultdict(lambda:[])
    for family in family_bcubed:
        for x_value in family_bcubed[family]:
            p, r, f = family_bcubed[family][x_value]
            precision[x_value].append(p)
            recall[x_value].append(r)
            f1[x_value].append(f)
    for d, l in zip([precision, recall, f1], ['Precision', 'Recall', 'F1']):
        for val in d:
            d[val] = mean(d[val])
        x_values = sorted(list(d.keys()))
        plt.plot(x_values, [d[val] for val in x_values], label=l)
    plt.legend(loc='best')
    plt.xlabel(f'{func_label} Clustering Threshold')
    plt.ylabel('B-Cubed Score')
    plt.title(f'Average {func_label} Cognate Clustering Performance')
    if save_directory != None:
        plt.savefig(f'{save_directory}Average {func_label}  Cognate Clustering Performance', dpi=300)
    plt.show()
    plt.close()
    
def optimal_parameter(family_bcubed):
    precision, recall, f1 = defaultdict(lambda:[]), defaultdict(lambda:[]), defaultdict(lambda:[])
    for family in family_bcubed:
        for x_value in family_bcubed[family]:
            p, r, f = family_bcubed[family][x_value]
            precision[x_value].append(p)
            recall[x_value].append(r)
            f1[x_value].append(f)
    for d, l in zip([precision, recall, f1], ['Precision', 'Recall', 'F1']):
        for val in d:
            d[val] = mean(d[val])
    return keywithmaxval(f1)
    

def write_parameters(parameter_dict, outputfile, sep=','):
    with open(outputfile, 'w') as f:
        f.write(sep.join(['Dataset', 'Parameter_Value', 'Precision', 'Recall', 'F1']))
        f.write('\n')
        for dataset in parameter_dict:
            for parameter_value in parameter_dict[dataset]:
                precision, recall, fscore = parameter_dict[dataset][parameter_value]
                f.write(sep.join([dataset, str(parameter_value), str(precision), str(recall), str(fscore)]))
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
validation_datasets = [Bantu, Hellenic, Japonic, Quechuan, Uto_Aztecan, Vietic]
test_datasets = [family for family in families.values() if family not in validation_datasets]

#%%
#Load phoneme PMI and surprisal for validation datasets
for vd in validation_datasets:
    print(f'Loading {vd.name} phoneme PMI...')
    vd.load_phoneme_pmi()
    print(f'Loading {vd.name} phoneme surprisal...')
    vd.load_phoneme_surprisal()

#%%
#Distance/similarity functions
functions = {#'Surprisal':(surprisal_sim, True),
             #'PMI':(score_pmi, False),
             #'Phonetic':(word_sim, True),
             #'Levenshtein':(LevenshteinDist, False)
             #'Hybrid':(combo_sim, True),
             'PhoneticSurprisal':(phonetic_surprisal_sim, True),
             
             #'Combined':(nhd, False),
             #'Z-Surprisal':(z_score_surprisal, False)
             }

# #Define hybrid functions
# hybrid_functions = {}
# function_labels = list(functions.keys())
# for i in range(len(function_labels)):
#     for j in range(i+1, len(function_labels)):
#         label1, label2 = function_labels[i], function_labels[j]
#         def hybrid_distance(pair1, pair2, functions, func_sims, **kwargs):   
#         hybrid_functions[f'{label1}-{label2}']

#%%
#Evaluate validation datasets for all functions with parameters = [0.0, ..., 1.0]
evaluation = {}
destination = '../Results/Cognate Clustering/Validation/Common Concepts/'

#%%
function_labels = list(functions.keys())


for i in range(len(functions)):
    func_label1 = function_labels[i]
    if func_label1 not in evaluation:
        print(f'Evaluating {func_label1} parameters...')
        dist_func1, func_sim1 = functions[func_label1]
        family_bcubed =  evaluate_family_parameters(validation_datasets,
                                                    parameters=[i/100 for i in range(0,101)],
                                                    dist_func=dist_func1, func_sim=func_sim1,
                                                    concept_list=common_concepts)
        
        #Save evaluation 
        evaluation[func_label1] = family_bcubed
        write_parameters(family_bcubed, outputfile=f'{destination}{func_label1} Cognate Clustering Performance.csv')
        print(f'Best parameter value for {func_label1}: {optimal_parameter(family_bcubed)}')
        
        #Test hybrid distances
        # for j in range(i+1, len(functions)):
        #     func_label2 = function_labels[j]
        #     print(f'Evaluating hybrid {func_label1}-{func_label2} parameters...')
        #     dist_func2, func_sim2 = functions[func_label2]
                
        #     def hyb_dist(pair1, pair2):
        #         return hybrid_distance(pair1, pair2, funcs=[dist_func, dist_func2], 
        #                         func_sims=[func_sim, func_sim2])
            
        #     hybrid_family_bcubed =  evaluate_family_parameters(validation_datasets,
        #                                             parameters=[i/100 for i in range(0,101)],
        #                                             dist_func=hyb_dist, func_sim=False)
            
        #     #Save evaluation 
        #     evaluation[f'{func_label}-{func_label2}'] = hybrid_family_bcubed
        #     write_parameters(family_bcubed, outputfile=f'{destination}{func_label}-{func_label2} Cognate Clustering Performance.csv')
        

    

#%%
#Plot all performances
loaded = False
for func_label in evaluation: 
    plot_performance(evaluation[func_label], func_label, save_directory=destination,
                     legend_pos=(0.8, 0.4))
    optimum = optimal_parameter(evaluation[func_label])
    print(f'Best parameter value for {func_label}: {optimum}')
    for family in evaluation[func_label]:
        print(family, round(evaluation[func_label][family][optimum][2], 3))
     dist_func, func_sim = functions[func_label]
    # for family in test_datasets:
    #     if loaded == False:
    #         print(f'Loading {family.name} phoneme PMI and surprisal...')
            family.load_phoneme_pmi()
            family.load_phoneme_surprisal()
        family_clusters = family.cluster_cognates(concept_list=common_concepts,
                                                dist_func=dist_func, sim=func_sim,
                                                cutoff=optimum)
        family_bcubed = family.evaluate_clusters(family_clusters)
        print(family.name, round(family_bcubed[2], 3))
        
    # print('\n')
    # loaded = True
