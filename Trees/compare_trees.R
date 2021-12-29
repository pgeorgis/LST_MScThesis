#Load packages for loading and evaluating phylogenetic trees
library(Quartet)
library(phytools)
library(phangorn)
library(TreeDist)

#Set working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))
local_dir <- getwd()


gen_quartet_distance <- function(non_binary_tree, binary_tree, add_root = FALSE) {
  #Generalized Quartet Distance (GQD), as described by Pompei, Loreto, & Tria (2011)
  #between a reference tree which may have non-binary branching and a binary-branching test tree
  #add_root : logical, adds a labeled root node to both trees in order to ensure that the position
  #of the top-level clade is accounted for in the GQD value
  
  if (add_root == TRUE) {
    
    #Can't add a ROOT node to non-binary trees
    if (is.binary(binary_tree) == TRUE) {
      
      #Add labeled ROOT node to both trees and reroot around it
      rooted_nonbinary <- bind.tip(non_binary_tree, 'ROOT', edge.length=1)
      rooted_nonbinary <- reroot(rooted_nonbinary, node.number=Ntip(non_binary_tree)+1)
      non_binary_tree <- rooted_nonbinary
      
      rooted_binary <- bind.tip(binary_tree, 'ROOT', edge.length=1)
      rooted_binary <- reroot(rooted_binary, node.number=Ntip(binary_tree)+1)
      binary_tree <- rooted_binary
    } 
  }
  
  #norm : number of resolved ("butterfly") quartets in reference/non-binary tree
  norm <- ResolvedQuartets(non_binary_tree)[[1]]
  
  #diff_butterflies : number of resolved ("butterfly") quartets which differ between the two trees
  butterflies <- SharedQuartetStatus(cf=non_binary_tree, trees=c(binary_tree))
  diff_butterflies <- butterflies[[4]]
  
  return(diff_butterflies/norm)
}

#Function for loading a series of Newick tree files into a MultiPhylo object
load_forest <- function(newick_files) {
  forest <- c()
  for (file in newick_files) {
    forest <- append(forest, read.newick(file, quiet=TRUE))
  }
  return(forest)
}

#Function for automatically evaluating a series of trees against one gold tree using GQD
#Returns the tree which best matches the gold tree
best_matching_tree <- function(gold_tree, test_forest, method=gen_quartet_distance, forest_names=NULL, add_root=TRUE) {
  
  #Create lists for tree evaluation scores
  scores <- c()
  
  #Iterate through test trees and evaluate distance from gold tree
  for (i in seq(length(test_forest))) {
    test_tree <- test_forest[[i]]
    score <- method(gold_tree, test_tree, add_root=add_root)
    scores <- append(scores, score)
  }
  #for (test_tree in test_forest) {
  #  score <- method(gold_tree, test_tree, add_root=add_root)
  #  scores <- append(scores, score)
  #}
  
  #Get index of the tree with the minimum distance from the gold tree
  min_index <- which.min(scores)
  
  #Print the name of the best tree if the corresponding names were supplied
  if(!is.null(forest_names)) {
    print(paste('Best match:', forest_names[[min_index]]))
  }
  
  #Print the best tree's score
  print(paste('Distance:', round(scores[[min_index]],2)))
  
  #Return the tree with the minimum distance score from the gold tree
  return(test_forest[[min_index]])
}

#Get list of families
families <- c('Arabic', 
              'Balto-Slavic', 
              'Dravidian',
              'Hokan',
              'Italic', 
              'Polynesian', 
              'Sinitic',
              'Turkic', 
              'Uralic',
              
              #Validation datasets
              'Bantu',
              'Hellenic',
              'Japonic',
              'Quechuan',
              'Uto-Aztecan',
              'Vietic',
              
              #Additional sub-datasets (not Yana, all non-binary branching)
              'Pomoan',
              'Yuman'
              )


#Initialize empty data frame to store results of tree evaluation  
tree_results <- data.frame(family=character(),
                           cognate_method=character(),
                           eval_method=character(),
                           min_similarity=character(),
                           tree_type=character(),
                           TreeDist=numeric(),
                           GenQuartetDist=numeric()
                           )

#Iterate through families, identify the best tree
for (family in families) {
  
  print(family)

  #Load gold Glottolog tree
  family_gold <- read.newick(paste('Gold/', family, '_pruned.tre', sep=''), quiet=TRUE)
  
  #Load distance-based (exclude binary) trees into a MultiPhylo forest
  setwd('..')
  tree_dir <- paste(getwd(), '/Results/Trees/', family, sep='')
  family_trees <- list.files(path=tree_dir)
  family_trees <- family_trees[grep('.tre', family_trees)]
  
  family_trees <- paste(tree_dir, family_trees, sep='/')
  
  #Sort trees by cognate detection and evaluation method
  cognate_methods <- c('none', 'Phonetic', 'PMI', 'Surprisal', 'Hybrid', 'Levenshtein', 'gold')
  eval_methods <- c('Phonetic-calibrated', 'Phonetic-uncalibrated', 
                    'PMI-calibrated', 'PMI-uncalibrated',
                    'Surprisal-calibrated', 'Surprisal-uncalibrated',
                    'Hybrid-calibrated', 'Hybrid-uncalibrated',
                    'Levenshtein-calibrated', 'Levenshtein-uncalibrated')
  all_trees <- c()
  for (cognate_method in cognate_methods) {
    for (eval_method in eval_methods) {
      method <- paste(cognate_method, eval_method, sep='_')
      method_trees <- family_trees[grep(method, family_trees)]
      
      #Load this forest of trees
      method_forest <- load_forest(method_trees)
      
      #Evaluate each individual tree for TreeDistance and Generalized Quartet Distance
      for (i in seq(length(method_forest))) {
        linkage <- strsplit(tail(strsplit(method_trees[[i]], '_')[[1]], n=1), '.tre')[[1]]
        min_sim <- tail(strsplit(method_trees[[i]], '_')[[1]], n=2)[[1]]
        tree <- method_forest[[i]]
        TD <- TreeDistance(family_gold, tree)
        GQD <- gen_quartet_distance(family_gold, tree, add_root=TRUE)
        
        #Add a row to the tree_results data frame with these values
        row <- list(family=family, 
                    cognate_method=cognate_method, eval_method=eval_method, 
                    min_similarity=min_sim, tree_type=linkage,
                    TreeDist=TD, GenQuartetDist=GQD)
        tree_results <- rbind(tree_results, row)
        
        #Save the tree to list for overall comparison
        all_trees[[paste(method, paste('min', min_sim, sep='-'), linkage, sep='_')]] = tree
        
      }

      #Find the maximum clade credibility (MCC) tree among these
      mcc_tree <- maxCladeCred(method_forest)
      
      #Evaluate the MCC and consensus trees for TreeDist and Generalized Quartet Distance
      TD_MCC <- TreeDistance(family_gold, mcc_tree)
      GQD_MCC <- gen_quartet_distance(family_gold, mcc_tree, add_root=TRUE)
      
      #Add a row to the tree_results data frame with these values
      row_MCC <- list(family=family, 
                      cognate_method=cognate_method, eval_method=eval_method, 
                      min_similarity='N/A',
                      tree_type='MaxCladeCredibility',
                      TreeDist=TD_MCC, GenQuartetDist=GQD_MCC)
      tree_results <- rbind(tree_results, row_MCC)
    }
  } 
  
  #Evaluate and determine the best trees
  none_trees <- all_trees[grep('none', names(all_trees))]
  gold_trees <- all_trees[grep('gold', names(all_trees))]
  ld_trees <- all_trees[grep('Levenshtein', names(all_trees))]
  ld_trees <- ld_trees[-grep('gold', names(ld_trees))]
  auto_trees <- all_trees[-grep('gold', names(all_trees))]
  auto_trees <- auto_trees[-grep('none', names(auto_trees))]
  auto_trees <- auto_trees[-grep('Levenshtein', names(auto_trees))]
  best_auto_tree <- best_matching_tree(gold_tree=family_gold, test_forest=auto_trees, forest_names=names(auto_trees), add_root=TRUE)
  best_ld_tree <- best_matching_tree(gold_tree=family_gold, test_forest=ld_trees, forest_names=names(ld_trees), add_root=TRUE)
  best_none_tree <- best_matching_tree(gold_tree=family_gold, test_forest=none_trees, forest_names=names(none_trees), add_root=TRUE)
  best_gold_tree <- best_matching_tree(gold_tree=family_gold, test_forest=gold_trees, forest_names=names(gold_trees), add_root=TRUE)
  cat('\n')
  
  #Plot and save the evaluation of the best tree using QuartetDivergence diagram
  png_plot_path <- paste(tree_dir, '/', family, "_best_auto.png", sep='')
  tre_plot_path <- paste(tree_dir, '/', family, "_best_auto.tre", sep='')
  png(filename=png_plot_path, width=1000, height=700)
  VisualizeQuartets(ladderize(family_gold), ladderize(best_auto_tree), style='size', spectrum=rainbow(300)[1:101])
  dev.off()
  write.tree(best_auto_tree, file=tre_plot_path)
  
  png_plot_path <- paste(tree_dir, '/', family, "_best_gold.png", sep='')
  tre_plot_path <- paste(tree_dir, '/', family, "_best_gold.tre", sep='')
  png(filename=png_plot_path, width=1000, height=700)
  VisualizeQuartets(ladderize(family_gold), ladderize(best_gold_tree), style='size', spectrum=rainbow(300)[1:101])
  dev.off()
  write.tree(best_gold_tree, file=tre_plot_path)
  
  #Plot densiTree based on automatic trees, using gold tree as consensus
  class(auto_trees) <- "multiPhylo"
  png_plot_path <- paste(tree_dir, '/', family, "_auto_densiTree.png", sep='')
  png(filename=png_plot_path, width=1000, height=700)
  if (family != 'Hokan') {
    densiTree(auto_trees, consensus=ladderize(family_gold), alpha=0.01)
  } else {
    densiTree(auto_trees, alpha=0.01)
  }
  dev.off()
  setwd(local_dir)
}

#Write tree evaluation results to a csv file
setwd('..')
tree_dir <- paste(getwd(), '/Results/Trees/', sep='')
write.csv(tree_results, paste(tree_dir, 'tree_evaluation_results.csv', sep='/'), row.names = FALSE)
setwd(local_dir)

#Evaluate Bayesian inference trees
bayesian_path <- '../Results/Trees/Bayesian'
bayesian_results <- data.frame(family=character(),
                               tree_type=character(),
                               TreeDist=numeric(),
                               GenQuartetDist=numeric())
for (family in families) {
  
  #Skip Hokan, because the Bayesian trees are based on gold cognate sets, which are unavailable for Hokan
  if (family != 'Hokan') {
    print(family)
    
    #Load gold reference tree and Nexus file containing Bayesian character-based trees
    family_gold <- read.newick(paste('Gold/', family, '_pruned.tre', sep=''), quiet=TRUE)
    family_bayesian <- read.nexus(file=paste(bayesian_path, family, paste(family, 'gold_common-concepts.nex', sep='_'), sep='/'))
    
    #Replace curly brackets with parentheses in gold tree, which is how they appear in Bayesian trees
    family_gold$tip.label <- str_replace_all(family_gold$tip.label, '\\{', '(')
    family_gold$tip.label <- str_replace_all(family_gold$tip.label, '\\}', ')')
    
    #Make replacements for specific families in order to match Bayesian trees formatting
    if (family == 'Polynesian') {
      family_gold$tip.label[which(family_gold$tip.label == "Austral_(Ra'ivavae)")] = "Austral_(Raivavae)"
    } else if (family == 'Sinitic') {
      family_gold$tip.label[which(family_gold$tip.label == "Xi'an")] = "Xian"
      family_gold$tip.label[which(family_gold$tip.label == "Ha'erbin")] = "Haerbin"
    } else if (family == 'Uto-Aztecan') {
      family_gold$tip.label[which(family_gold$tip.label == "Tohono_O'odham")] = 'Tohono_Oodham'
    }
    
    #Calculate maximum clade credibility tree and its distances from the gold tree
    family_mcc <- maxCladeCred(family_bayesian)
    mcc_TD <- TreeDistance(family_gold, family_mcc)
    mcc_GQD <- gen_quartet_distance(family_gold, family_mcc, add_root=TRUE)
    
    #Save the MCC tree and plot to file
    write.tree(family_mcc, file=paste(bayesian_path, family, paste(family, 'MCC.tre', sep='_'), sep='/'))
    png_plot_path <- paste(bayesian_path, family, paste(family, 'MCC.png', sep='_'), sep='/')
    png(filename=png_plot_path, width=1000, height=700)
    VisualizeQuartets(ladderize(family_gold), ladderize(family_mcc), style='size', spectrum=rainbow(300)[1:101])
    dev.off()
    
    #Add MCC measurements to dataframe
    row_MCC <- list(family=family,
                    tree_type='MCC',
                    TreeDist=mcc_TD,
                    GenQuartetDist=mcc_GQD)
    bayesian_results <- rbind(bayesian_results, row_MCC)
    
    #Identify the single tree which best matches the gold reference tree
    #and take its measurements; save to the dataframe
    best_bayesian <- best_matching_tree(family_gold, family_bayesian)
    best_TD <- TreeDistance(family_gold, best_bayesian)
    best_GQD <- gen_quartet_distance(family_gold, best_bayesian, add_root=TRUE)
    row_best <- list(family=family,
                     tree_type='best',
                     TreeDist=best_TD,
                     GenQuartetDist=best_GQD)
    bayesian_results <- rbind(bayesian_results, row_best)
    
    #Save the best tree and plot to file
    write.tree(best_bayesian, file=paste(bayesian_path, family, paste(family, 'best_bayesian.tre', sep='_'), sep='/'))
    png_plot_path <- paste(bayesian_path, family, paste(family, 'best_bayesian.png', sep='_'), sep='/')
    png(filename=png_plot_path, width=1000, height=700)
    VisualizeQuartets(ladderize(family_gold), ladderize(best_bayesian), style='size', spectrum=rainbow(300)[1:101])
    dev.off()
    
    #Plot densiTree based on Bayesian inference trees, using gold tree as consensus
    class(family_bayesian) <- "multiPhylo"
    png_plot_path <- paste(bayesian_path, family, paste(family, 'densiTree.png', sep='_'), sep='/')
    png(filename=png_plot_path, width=1000, height=700)
    densiTree(family_bayesian, consensus=ladderize(family_gold), alpha=0.01)
    dev.off()
    setwd(local_dir)
    cat('\n')
  }
}

#Write Bayesian tree evaluation results to a csv file
setwd('..')
tree_dir <- paste(getwd(), '/Results/Trees', sep='')
write.csv(bayesian_results, paste(tree_dir, 'bayesian_tree_evaluation_results.csv', sep='/'), row.names = FALSE)
setwd(local_dir)


#Random trees
for (family in families) {
  family_gold <- read.newick(paste('Gold/', family, '_pruned.tre', sep=''), quiet=TRUE)
  n_langs <- length(family_gold$tip.label)
  random_tree <- rtree(n=n_langs)
  for (i in seq(n_langs)) {
    random_tree$tip.label[which(random_tree$tip.label == paste('t', i, sep=''))] = family_gold$tip.label[[i]]
  }
  plotTree(random_tree)
  print(paste(family, round(gen_quartet_distance(family_gold, random_tree), 2)))
}
