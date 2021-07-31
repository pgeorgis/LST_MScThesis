from collections import defaultdict
import pandas as pd
import math, unidecode, re, operator
import numpy as np
from statistics import mean, stdev
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from sklearn import manifold
import seaborn as sns
import networkx as nx

def dict_tuplelist(dic, sort=True, reverse=True):
    """Returns a list of (key, value) tuples from the dictionary
    if sort == True, sorts the list by the value, by default in decending order"""
    d = [(key, dic[key]) for key in dic]
    if sort == True:
        d.sort(key=operator.itemgetter(1), reverse=reverse)
    return d

#%%
#STRING MANIPULATION
def strip_ch(string, to_remove):
    """Removes a set of characters from strings"""
    return ''.join([ch for ch in string if ch not in to_remove])

def format_as_variable(string):
    variable = unidecode.unidecode(string)
    variable = re.sub(' ', '', variable)
    variable = re.sub("'", '', variable)
    variable = re.sub('-', '_', variable)
    variable = re.sub('\(', '', variable)
    variable = re.sub('\)', '', variable)
    return variable


#%%
#CSV/EXCEL FILE TOOLS
def csv_to_dict(csvfile, header=True, sep=',', start=0, encoding='utf_8'):
    """Reads a CSV file into a dictionary"""
    csv_dict = defaultdict(lambda:defaultdict(lambda:''))
    with open(csvfile, 'r', encoding=encoding) as csv_file:
        csv_file = csv_file.readlines()
        columns = [item.strip() for item in csv_file[start].split(sep)]
        if header == True:
            start += 1
        for i in range(start, len(csv_file)):
            line = [item.strip() for item in csv_file[i].split(sep)]
            for j in range(len(columns)):
                key = ''
                if header == True:
                    key += columns[j]
                else:
                    key += str(j)
                try:
                    csv_dict[i][key] = line[j]
                except IndexError:
                    pass
    return csv_dict

def xlsx_to_csv(excel_path, csv_path=None, sheet=None, 
                sep=',', index=None, header=True):
    """Converts an Excel file to a CSV file"""
    if sheet != None:
        excel_file = pd.read_excel(excel_path, sheet_name=sheet)
    else:
        excel_file = pd.read_excel(excel_path)
    
    #Automatically name the output .csv file the same as the Excel file if 
    #no other name is specified
    if csv_path == None:
        csv_path = excel_path.split('.')[0] + '.csv'
    
    #Write to .csv file
    excel_file.to_csv(csv_path, index=index, header=header, sep=sep)
    print(f'Wrote file to {csv_path}.')
    
#%%
#NORMALIZATION
def normalize_dict(dict_, default=False, lmbda=None, return_=True):
    """Normalizes the values of a dictionary"""
    """If default==True, returns a default dictionary with default value lmbda"""
    """If return_==False, modifies the input dictionary without returning anything"""
    if default==True:
        normalized = defaultdict(lambda:lmbda)
    else:
        normalized = {}
    total = sum(list(dict_.values()))
    for key in dict_:
        if return_ == True:
            normalized[key] = dict_[key] / total
        else:
            dict_[key] = dict_[key] / total
    if return_ == True:
        return normalized
    
#%%
#INFORMATION CONTENT
def surprisal(p):
    try:   
        return -math.log(p, 2)
    except ValueError:
        print(f'Math Domain Error: cannot take the log of {p}')
        raise ValueError

def entropy(X):
    """X should be a dictionary with absolute counts"""
    total = sum(X.values())
    E = 0
    for i in X:
        p = X[i]/total
        if p > 0:
            E += p * surprisal(p)
    return E

#%%
#PLOTTING PAIRWISE SIMILARITY / DISTANCE
def sim_dict(group, sim_func=None, sim=True, max_dist=None):
    sims = {}
    dists = {}
    for item1 in group:
        for item2 in group:
            if item1 != item2:
                if sim == True:
                    sims[(item1, item2)] = sim_func(item1, item2)
                else:
                    dists[(item1, item2)] = sim_func(item1, item2)
    if sim == False:
        if max_dist == None:
            max_dist = max(dists.values())
        dists = {pair:dists[pair]/max_dist for pair in dists}
        sims = {pair:1-dists[pair] for pair in dists}
    return sims

def dist_dict(group, dist_func=None, sim=False, max_dist=None):
    dists = {}
    for item1 in group:
        for item2 in group:
            if item1 != item2:
                if sim == True:
                    dists[(item1, item2)] = 1-dist_func(item1, item2)
                else:
                    dists[(item1, item2)] = dist_func(item1, item2)
    return dists

def list_mostsimilar(item1, comp_group, dist_func, n=5, sim=True, return_=False):
    n = min(len(comp_group), n)
    sim_list = [(item2, dist_func(item1, item2)) for item2 in comp_group if item1 != item2]
    sim_list.sort(key=operator.itemgetter(1), reverse=True)
    if return_ == True:
        return sim_list[:n]
    else:
        for item in sim_list[:n]:
            print(f'{item[0].name}: {round(item[1], 2)}')

def distance_matrix(group, dist_func, sim=False, **kwargs):
    mat = []
    already_checked = []
    group_sims = {}
    for i in range(len(group)):
        item1 = group[i]
        vec = []
        for j in range(len(group)):
            if j not in already_checked:
                item2 = group[j]
                distance_score = 0
                if i != j:
                    dist = dist_func(item1, item2, **kwargs)
                    if sim == True:
                        dist = 1 - min(1, dist)
                    distance_score += dist
                vec.append(distance_score)
                group_sims[(i, j)] = distance_score
            else:
                dist = group_sims[(j, i)]
                vec.append(dist)
                group_sims[(i, j)] = dist
        already_checked.append(i)
        mat.append(vec)
    return mat

def linkage_matrix(group, dist_func, sim=False, 
                   method = 'average', metric="euclidean",
                   **kwargs):
    """Methods: average, centroid, median, single, complete, ward, weighted
        See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html"""
    mat = distance_matrix(group, dist_func, sim, **kwargs)
    mat = np.array(mat)
    dists = squareform(mat)
    linkage_matrix = linkage(dists, method, metric)
    return linkage_matrix

def draw_dendrogram(group, dist_func, title=None, sim=False, labels=None, 
                    p=30, method='average', metric='euclidean',
                    orientation='left', 
                    save_directory='',
                    **kwargs):
    sns.set(font_scale=1.0)
    if len(group) >= 100:
        plt.figure(figsize=(20,20))
    elif len(group) >= 60:
        plt.figure(figsize=(10,10))
    else:
        plt.figure(figsize=(10,8))
    lm = linkage_matrix(group, dist_func, sim, method, metric, **kwargs)
    dendrogram(lm, p=p, orientation=orientation, labels=labels)
    if title != None:
        plt.title(title, fontsize=30)
    plt.savefig(f'{save_directory}{title}.png', bbox_inches='tight', dpi=300)
    plt.show()

def plot_distances(group, dist_func=None, sim=False, dimensions=2, labels=None, 
                   title=None, plotsize=None, invert_yaxis=False, invert_xaxis=False,
                   directory='',
                   **kwargs):   
    dm = distance_matrix(group, dist_func, sim, **kwargs)
    adist = np.array(dm)
    amax = np.amax(adist)
    adist /= amax
    mds = manifold.MDS(n_components=dimensions, dissimilarity="precomputed", random_state=42) #if an integer, random state parameter controls that multiple function calls will produce consistent mappings; popular values are 0 and 42
    results = mds.fit(adist)
    coords = results.embedding_
    sns.set(font_scale=1.0)
    if plotsize == None:
        x_coords = [coords[i][0] for i in range(len(coords))]
        y_coords = [coords[i][1] for i in range(len(coords))]
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        y_ratio = y_range / x_range
        n = max(10, round((len(group)/10)*2))
        plotsize = (n, n*y_ratio)
    plt.figure(figsize=plotsize)
    plt.scatter(
        coords[:, 0], coords[:, 1], marker = 'o'
        )
    for label, x, y in zip(labels, coords[:, 0], coords[:, 1]):
        plt.annotate(
            label,
            xy = (x, y), xytext = (5, -5),
            textcoords = 'offset points', ha = 'left', va = 'bottom',
            )
    if invert_yaxis == True:    
        plt.gca().invert_yaxis()
    if invert_xaxis == True:
        plt.gca().invert_xaxis()
    plt.savefig(f'{directory}{title}.png', bbox_inches='tight', dpi=300)
    plt.show()
    
def network_plot(group, labels, dist_func=None, sim=True,
                 method='spring', coordpos=True, dimensions=2, seed=1,
                 edgelabels=False, edge_label_dist=True, 
                 scale_dist=100, edge_decimals=1,
                 min_edges=None, max_edges=None, threshold=None,
                 scale_nodes=True, node_sizes=None, node_colors=None,
                 title=None, directory='',
                 invert_yaxis=False, invert_xaxis=False):
    if min_edges == None:
        if method == 'coords':
            min_edges = len(group)
        else:
            min_edges = round(math.sqrt(len(group)))
    if max_edges == None:
        max_edges = len(group)
    sims_dict = sim_dict(group, sim_func=dist_func, sim=sim)
    #median_sim = statistics.median(sims_dict.values())
    if threshold == None:
        threshold = mean(sims_dict.values())
    #warnings.filterwarnings("ignore", category=UserWarning)
    item_labels = {n:labels[n] for n in range(len(labels))}
    if len(group) >= 30:
        plt.figure(figsize=(15,12))
    else:
        plt.figure(figsize=(10, 8))
    gr = nx.Graph()
    coordinates = {}
    dm = distance_matrix(group, dist_func, sim)
    adist = np.array(dm)
    amax = np.amax(adist)
    adist /= amax
    mds = manifold.MDS(n_components=dimensions, dissimilarity="precomputed", random_state=42) #if an integer, random state parameter controls that multiple function calls will produce consistent mappings; popular values are 0 and 42
    results = mds.fit(adist)
    coords = results.embedding_
    for n, x, y in zip(item_labels, coords[:, 0], coords[:, 1]):
        coordinates[n] = (x, y)
    edge_labels = {}
    item_edges = defaultdict(lambda:0)
    edges = {}
    
    for pair in sims_dict:
        if (sims_dict[pair] >= threshold) or (method == 'coords'):
            item1 = group.index(pair[0])
            item2 = group.index(pair[1])
            gr.add_edge(item1, item2, distance=(1-sims_dict[pair]))
            if edge_label_dist == True: #label edges as distances
                edge_labels[(item1, item2)] = str(round((1-sims_dict[pair])*scale_dist, edge_decimals))
            else: #label edges as similarities
                edge_labels[(item1, item2)] = str(round((sims_dict[pair])*scale_dist, edge_decimals))
    for i in range(len(group)):
        if i not in gr.nodes():
            gr.add_node(i)
    
    if method == 'coords':
        pos = coordinates
    elif method == 'spring':
        if coordpos==True:
            pos = nx.spring_layout(gr, seed=seed, pos=coordinates)
        else:
            pos = nx.spring_layout(gr, seed=seed)
    else:
        print(f'Method {method} is not recognized!')
        raise ValueError
    edgeList, colorsList = zip(*nx.get_edge_attributes(gr,'distance').items())
    if scale_nodes == True:
        if node_sizes == None:
            print('Provide a list of node sizes in order to scale nodes!')
            raise ValueError
        node_sizes = [node_sizes[node] for node in gr.nodes()]
        nz_node_sizes = [rescale(i, node_sizes, 200, 2000) for i in node_sizes]
    else:
        if node_sizes == None:
            nz_node_sizes = [300 for i in range(len(group))]
        else:
            nz_node_sizes = [node_sizes for i in range(len(group))]
    if node_colors == None:
        node_colors = ['#70B0F0' for i in range(len(group))] #default light blue
    nx.draw(gr, pos=pos, edgelist = edgeList, edge_color=colorsList, font_size=8, 
            edge_cmap = plt.cm.hot, vmin = 0, vmax = 1, labels=item_labels,
            node_color=node_colors, font_weight='bold', node_size=nz_node_sizes)
    if invert_yaxis == True:    
        plt.gca().invert_yaxis()
    if invert_xaxis == True:
        plt.gca().invert_xaxis()
    if edgelabels == True:
        nx.draw_networkx_edge_labels(gr, pos=pos, edge_labels=edge_labels, font_size=8)
    if title != None:
        plt.title(f'{title}: (method = {method}, {dimensions}-D, {min_edges} min edges, {max_edges} max edges, threshold = {round(threshold, 3)})', fontsize=20)
        plt.savefig(f'{directory}{title}.png', bbox_inches='tight', dpi=600)
    plt.show()