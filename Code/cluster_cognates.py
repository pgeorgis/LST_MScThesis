from load_languages import *
import networkx as nx
from networkx.algorithms.clique import find_cliques

def keywithmaxval(d):
    """Returns the dictionary key with the highest value"""
    v = list(d.values())
    k = list(d.keys())
    return k[v.index(max(v))]

def keywithminval(d):
    """Returns the dictionary key with the smallest value"""
    v = list(d.values())
    k = list(d.keys())
    return k[v.index(min(v))]

#%%
BaltoSlavic = families['Balto-Slavic']
#wordlist = [f'{lang} /{form}/' for lang in Arabic.cognate_sets['BIRD'] 
#                for form in Arabic.cognate_sets['BIRD'][lang]]
family = Arabic
concept = 'SUN'

wordlist = [(f'{lang} /{entry[1]}/', family.languages[lang]) for lang in family.concepts[concept]
            for entry in family.concepts[concept][lang]]
#%%
#Initialize alpha as 0.1
alpha = 0.1
update_rate = 1.5
max_iterations = 5

#Initialize all words in their own clusters
clusters = defaultdict(lambda:nx.Graph())
iteration = 0
G = nx.Graph()
G.add_nodes_from(wordlist)
clusters[iteration] = G


#Iterate until convergence
converged = False
while ((converged == False) and (iteration < max_iterations)):
    print('\talpha:', alpha)
    print('\tn_clusters:', len(list(nx.connected_components(clusters[iteration]))))
        
    
    iteration += 1
    clusters[iteration] = clusters[iteration-1].copy()
    print(f'Starting iteration {iteration}...')
    current_clusters = sorted(list(nx.connected_components(clusters[iteration-1])))
    
    for cluster_i in range(len(current_clusters)):
        
        #Get a list of the other clusters
        other_clusters = [cluster_j for cluster_j in range(len(current_clusters)) 
                          if cluster_j != cluster_i]
        
        #Assign current cluster as the list of its members
        current_cluster = list(current_clusters[cluster_i])
        
        #Iterate through words of cluster_i
        for i in range(len(current_cluster)):
            word_i, lang_i = current_cluster[i]
            ipa_i = word_i.split('/')[1]
            
            #Get list of other words in cluster
            cluster_i_others = [current_cluster[j] for j in range(len(current_cluster)) if j != i]
            
            #Remove word_i from its cluster
            #Remove all edges between word_i and other nodes in cluster
            edges_to_remove = [(word_i, current_cluster[j]) for j in range(len(current_cluster)) 
                               if j != i]
            clusters[iteration].remove_edges_from(edges_to_remove)
            
            #Get the distance of word_i to every other cluster
            #NOT IN ORIGINAL VERSION: normalize by number of words in each cluster
            cluster_dists = defaultdict(lambda:[])
            for cluster_j in other_clusters:
                other_cluster = current_clusters[cluster_j]
                for item in other_cluster:
                    word_j, lang_j = item
                    ipa_j = word_j.split('/')[1]
                    cluster_dists[cluster_j].append(word_dist(ipa_i, ipa_j, 
                                                              lang1=lang_i, lang2=lang_j))
                cluster_dists[cluster_j] = mean(cluster_dists[cluster_j])
                
            #Do the same for the current cluster, if it contained more than word_i
            #NOT IN ORIGINAL VERSION: normalize by number of words in cluster
            if len(cluster_i_others) > 0:
                for item in cluster_i_others:
                    word_j, lang_j = item
                    ipa_j = word_j.split('/')[1]
                    cluster_dists[cluster_i].append(word_dist(ipa_i, ipa_j, 
                                                              lang1=lang_i, lang2=lang_j))
                cluster_dists[cluster_i] = mean(cluster_dists[cluster_i])
                
            
            #Get the score of the minimally distant cluster
            min_cluster_dist = min(cluster_dists.values())
            
            #If this score is less than alpha*Sim(word_i, word_i), 
            #assign word_i to a new cluster
            #Practically, Sim(word_i, word_i) will always equal 1, 
            #so just check whether it's less than alpha
            #if max_cluster_sim < alpha:
            if min_cluster_dist > alpha:
                pass
                #it already has all edges removed, so doing nothing keeps it as a singleton
            
            #Otherwise, assign word_i to the cluster with the maximum net similarity
            else:
                min_dist_cluster = current_clusters[keywithminval(cluster_dists)]                
                
                edges_to_add = [((word_i, lang_i), pair_j) for pair_j in min_dist_cluster]
                clusters[iteration].add_edges_from(edges_to_add)
                
    if sorted(list(nx.connected_components(clusters[iteration]))) == current_clusters:
        converged = True
    
    else:
        #Update the alpha value
        alpha *= update_rate
        
                
#%%
def sample_alpha(alpha, scaler_alpha = 1.0, exp_lambda = 10.0): #n_clusts, n_clusters, 
    """This is the published version of alpha sampling
    """
    alpha_new = random.expovariate(exp_lambda)
    mh_ratio = 0.0
    ll_ratio, pr_ratio, hastings_ratio = 0.0, 0.0, 0.0
    ll_ratio = alpha_new/alpha
    pr_ratio = np.exp(-exp_lambda*(alpha_new-alpha))
    hastings_ratio = np.exp(scaler_alpha*(random.uniform(0,1)-0.5))
    mh_ratio = ll_ratio * pr_ratio * hastings_ratio
    if mh_ratio >= random.random():
        return alpha_new
    else:
        return alpha