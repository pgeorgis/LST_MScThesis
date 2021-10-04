#COGNATE CLUSTERING PARAMETER TUNING
import pandas as pd
from load_languages import *

def evaluate_parameters(family, parameters, dist_func, func_sim):
    #Designate the concept list as all available concepts with >1 entries
    concept_list = [concept for concept in family.concepts.keys() 
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
        lm = linkage_matrix(group=words, dist_func=dist_func, sim=func_sim)
        
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


def evaluate_family_parameters(families, parameters, dist_func, func_sim):
    #Evaluate parameters
    family_bcubed = defaultdict(lambda:{})
    for family in families:
        family_bcubed[family.name] = evaluate_parameters(family, parameters, dist_func, func_sim)
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
validation_datasets = [Hellenic, Japonic, Quechuan, UtoAztecan]

#Load phoneme PMI and surprisal for validation datasets
for vd in validation_datasets:
    print(f'Loading {vd.name} phoneme PMI...')
    vd.load_phoneme_pmi()
    print(f'Loading {vd.name} phoneme surprisal...')
    vd.load_phoneme_surprisal()

#Distance/similarity functions
functions = {'PMI':(score_pmi, False),
             'Surprisal':(surprisal_sim, True),
             'Phonetic':(word_sim, True)
             }

#%%
#Evaluate validation datasets for all functions with parameters = [0.0, ..., 1.0]
evaluation = {}
destination = '../Results/Cognate Clustering/Validation/'
for func_label in functions:
    print(f'Evaluating {func_label} parameters...')
    dist_func, func_sim = functions[func_label]
    family_bcubed =  evaluate_family_parameters(validation_datasets,
                                                parameters=[i/100 for i in range(0,101)],
                                                dist_func=dist_func, func_sim=func_sim)
    
    #Save evaluation 
    evaluation[func_label] = family_bcubed
    write_parameters(family_bcubed, outputfile=f'{destination}{func_label} Cognate Clustering Performance.csv')
    
#%% 
#Plot all performances
for func_label in evaluation: 
    plot_performance(evaluation[func_label], func_label, save_directory=destination)
