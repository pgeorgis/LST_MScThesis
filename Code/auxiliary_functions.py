from collections import defaultdict
import pandas as pd
import math, unidecode, re, operator, os
import numpy as np
from statistics import mean, median, stdev
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster, to_tree
from scipy.spatial.distance import squareform
from sklearn import manifold
import seaborn as sns
import networkx as nx

#GENERAL AUXILIARY FUNCTIONS
def dict_tuplelist(dic, sort=True, reverse=True):
    """Returns a list of (key, value) tuples from the dictionary
    if sort == True, sorts the list by the value, by default in decending order"""
    d = [(key, dic[key]) for key in dic]
    if sort == True:
        d.sort(key=operator.itemgetter(1), reverse=reverse)
    return d

def default_dict(dic, l):
    """Turns an existing dictionary into a default dictionary with default value l"""
    dd = defaultdict(lambda:l)
    for key in dic:
        dd[key] = dic[key]
    return dd

def keywithmaxval(d):
    """Returns the dictionary key with the highest value"""
    v = list(d.values())
    k = list(d.keys())
    return k[v.index(max(v))]

def keywithminval(d):
    """Returns the dictionary key with the lowest value"""
    v = list(d.values())
    k = list(d.keys())
    return k[v.index(min(v))]

def create_folder(folder_name, directory=None):
    """Creates a folder with the specified name, by default in the current
    working directory (or else in a specified directory)"""
    cwd = os.getcwd()
    if directory != None:
        os.chdir(directory)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    os.chdir(cwd)

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
        
def adaptation_surprisal(alignment, surprisal_dict, normalize=True):
    """Calculates the surprisal of an aligned sequence, given a dictionary of 
    surprisal values for the sequence corresponcences"""
    values = [surprisal_dict[pair[0]][pair[1]] for pair in alignment]
    if normalize == True:
        return mean(values)
    else:
        return sum(values)
    
    

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
#SMOOTHING
def lidstone_smoothing(x, N, d, alpha=0.3):
    """Given x (unsmoothed counts), N (total observations), 
    and d (number of possible outcomes), returns smoothed Lidstone probability"""
    return (x + alpha) / (N + (alpha*d))

#%%
#PLOTTING PAIRWISE SIMILARITY / DISTANCE
def list_mostsimilar(item1, comp_group, dist_func, n=5, sim=True, return_=False):
    n = min(len(comp_group), n)
    sim_list = [(item2, dist_func(item1, item2)) for item2 in comp_group if item1 != item2]
    sim_list.sort(key=operator.itemgetter(1), reverse=sim)
    if return_ == True:
        return sim_list[:n]
    else:
        for item in sim_list[:n]:
            print(f'{item[0].name}: {round(item[1], 2)}')

def distance_matrix(group, dist_func, sim=False, **kwargs):
    #Initialize nxn distance matrix filled with zeros
    mat = np.zeros((len(group),len(group)))
    
    #Calculate pairwise distances between items and add to matrix
    for i in range(len(group)):
        for j in range(i+1, len(group)):
            dist = dist_func(group[i], group[j], **kwargs)
            
            #Convert similarities to distances
            if sim == True:
                dist = 1 - min(1, dist)
                
            mat[i][j] = dist
            mat[j][i] = dist
            
    return mat


def linkage_matrix(group, dist_func, sim=False, 
                   method = 'average', metric="euclidean",
                   **kwargs):
    """Methods: average, centroid, median, single, complete, ward, weighted
        See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html"""
    mat = distance_matrix(group, dist_func, sim, **kwargs)
    dists = squareform(mat)
    linkage_matrix = linkage(dists, method, metric)
    return linkage_matrix


def cluster_items(group, labels,
                  dist_func, sim, cutoff,
                  method = 'average', metric='euclidean',
                  **kwargs):
    lm = linkage_matrix(group, dist_func, sim, method, metric, **kwargs)
    cluster_labels = fcluster(lm, cutoff, 'distance')
    clusters = defaultdict(lambda:[])
    for item, cluster in sorted(zip(labels, cluster_labels), key=lambda x: x[1]):
        #sorting just makes it so that the cluster dictionary will be returned
        #with the clusters in numerical order
        clusters[cluster].append(item)
    
    return clusters
        
def draw_dendrogram(group, dist_func, title=None, sim=False, labels=None, 
                    p=30, method='average', metric='euclidean',
                    orientation='left', 
                    save_directory='',
                    return_newick=False,
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
    if return_newick == True:
        return linkage2newick(lm, labels)

def getNewick(node, newick, parentdist, leaf_names):
    #source: https://stackoverflow.com/questions/28222179/save-dendrogram-to-newick-format
    if node.is_leaf():
        return "%s:%.2f%s" % (leaf_names[node.id], parentdist - node.dist, newick)
    else:
        if len(newick) > 0:
            newick = "):%.2f%s" % (parentdist - node.dist, newick)
        else:
            newick = ");"
        newick = getNewick(node.get_left(), newick, node.dist, leaf_names)
        newick = getNewick(node.get_right(), ",%s" % (newick), node.dist, leaf_names)
        newick = "(%s" % (newick)
        return newick

def linkage2newick(linkage_matrix, leaf_labels):
    #Convert parentheses in labels to brackets, as parentheses are part of Newick format
    for i in range(len(leaf_labels)):
        leaf_labels[i] = re.sub("\(", "{", leaf_labels[i])
        leaf_labels[i] = re.sub("\)", "}", leaf_labels[i])
    
    tree = to_tree(linkage_matrix, False)
    return getNewick(tree, "", tree.dist, leaf_labels)


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
    
#%%
def network_plot(group, labels, 
                 dist_func=None, sim=True,
                 min_edges=None, max_edges=None, threshold=None,
                 method='spring', coordpos=True, dimensions=2, seed=1,
                 edgelabels=False, edge_label_dist=True, 
                 scale_dist=100, edge_decimals=1,
                 scale_nodes=False, node_sizes=None, node_colors=None,
                 invert_yaxis=False, invert_xaxis=False,
                 title=None, save_directory='',
                 **kwargs):

    #warnings.filterwarnings("ignore", category=UserWarning)
    
    #Determine the minimum number of edges per node to display
    #By default, take the square root of total number of network nodes
    #for spring networks, and the total number of network nodes for coordinate networks
    if min_edges == None:
        if method == 'coords':
            min_edges = len(group)
        else:
            min_edges = round(math.sqrt(len(group)))
            
    #Determine the maximum number of edges to display per node
    #By default, set the maximum to the total number of nodes
    if max_edges == None:
        max_edges = len(group)
    
    #Create dictionary of node indices and their labels
    item_labels = {n:labels[n] for n in range(len(labels))}
    
    #Calculate initial coordinates for nodes from a distance matrix using MDS
    dm = distance_matrix(group, dist_func, sim, **kwargs)
    amax = np.amax(dm)
    dm /= amax
    mds = manifold.MDS(n_components=dimensions, dissimilarity="precomputed", random_state=42) #if an integer, random state parameter controls that multiple function calls will produce consistent mappings; popular values are 0 and 42
    results = mds.fit(dm)
    coords = results.embedding_
    coordinates = {}
    for n, x, y in zip(item_labels, coords[:, 0], coords[:, 1]):
        coordinates[n] = (x, y)
        
    #Calculate the threshold for plotting edges: the mean distance among items in the network
    if threshold == None:
        dists = [dm[i][j] for i in range(len(dm)) for j in range(len(dm[i])) if i != j]
        threshold = mean(dists) + stdev(dists)
    
    #Create a figure for the network; larger plot if >30 nodes
    if len(group) >= 30:
        plt.figure(figsize=(15,12))
    else:
        plt.figure(figsize=(10, 8))
    
    #Initialize the network graph
    gr = nx.Graph()
    
    #Iterate through pairs of nodes and adding edges between them
    #For every node, add edges connecting it to the n least distance node (min_edges)
    #And then add more edges up until the maximum number of edges if their distance is lower than the threshold
    #Label edges with distances/similarities
    edge_labels = {}
    item_edges = defaultdict(lambda:0)
    edges = {}
    
    def add_edge(node_i, node_j, dist):
        gr.add_edge(node_i, node_j, distance=dist, weight=(1-dist)**2)
        
        #Label edges with distances; scale and round according to parameter specifications
        if edge_label_dist == True:
            edge_labels[(node_i, node_j)] = str(round(dist*scale_dist, edge_decimals))
        
        #Label edges with similarities; scale and round according to parameter specifications
        else: 
            edge_labels[(node_i, node_j)] = str(round(dist*scale_dist, edge_decimals))
        

    for i in range(len(dm)):
        i_dists = list(enumerate(dm[i]))
        i_dists.sort(key=lambda x: x[1])
        i_dists = [item for item in i_dists if item[0] != i]
        min_i_dists = i_dists[:min_edges]
        extra_i_dists = i_dists[min_edges:max_edges]
        for j, dist in min_i_dists:
            add_edge(i, j, dist)
        for j, dist in extra_i_dists:
            if dist <= threshold:
                add_edge(i, j, dist)
                
    #Add any nodes which were skipped in the preceding iteration due to not 
    #meeting the similarity threshold with any other node
    for i in range(len(group)):
        if i not in gr.nodes():
            gr.add_node(i)

    #Generate node positions according to method
    #coords: use coordinate positions from MDS
    if method == 'coords':
        pos = coordinates
    
    #spring: use spring layout positions
    elif method == 'spring':
        
        #Initialize either using MDS coordinates or random initialization
        if coordpos==True:
            pos = nx.spring_layout(gr, seed=seed, pos=coordinates)
        else:
            pos = nx.spring_layout(gr, seed=seed)
    
    #Raise error for unrecognized methods
    else:
        print(f'Method {method} is not recognized!')
        raise ValueError
        
    #Get lists of edges and their distances for color-coding 
    edgeList, colorsList = zip(*nx.get_edge_attributes(gr,'distance').items())
    
    #Scale nodes according to specified sizes, if given
    if scale_nodes == True:
        if node_sizes == None:
            print('Provide a list of node sizes in order to scale nodes!')
            raise ValueError
        node_sizes = [node_sizes[node] for node in gr.nodes()]
        nz_node_sizes = [rescale(i, node_sizes, 200, 2000) for i in node_sizes]
    
    #Otherwise plot all nodes with equal size, either specified through 
    #node_sizes parameter or 300 by default
    else:
        if node_sizes == None:
            nz_node_sizes = [300 for i in range(len(group))]
        else:
            nz_node_sizes = [node_sizes for i in range(len(group))]
    
    #Color all nodes light blue by default if no other color is specified 
    if node_colors == None:
        node_colors = ['#70B0F0' for i in range(len(group))]
    
    #Draw the network
    nx.draw(gr, pos=pos, edgelist = edgeList, edge_color=colorsList, font_size=8, 
            edge_cmap = plt.cm.hot, vmin = 0, vmax = 1, labels=item_labels,
            node_color=node_colors, font_weight='bold', node_size=nz_node_sizes)
    
    #Add edge labels
    if edgelabels == True:
        nx.draw_networkx_edge_labels(gr, pos=pos, edge_labels=edge_labels, font_size=8)
    
    #Invert axes
    if invert_yaxis == True:    
        plt.gca().invert_yaxis()
    if invert_xaxis == True:
        plt.gca().invert_xaxis()
    
    #Add title to the plot and save 
    if title != None:
        plt.title(f'{title}: (method = {method}, {dimensions}-D, {min_edges} min edges, {max_edges} max edges, threshold = {round(threshold, 3)})', fontsize=20)
        plt.savefig(f'{save_directory}{title}.png', bbox_inches='tight', dpi=600)
    
    #Show the network plot and then close
    plt.show()
    plt.close()