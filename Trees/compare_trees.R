#Load packages for loading and evaluating phylogenetic trees
library(TreeDist)
library(Quartet)
library(phytools)
library(phangorn)

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
    #Add labeled ROOT node to both trees and reroot around it
    rooted_nonbinary <- bind.tip(non_binary_tree, 'ROOT', edge.length=1)
    rooted_nonbinary <- reroot(rooted_nonbinary, node.number=Ntip(non_binary_tree)+1)
    non_binary_tree <- rooted_nonbinary
    
    rooted_binary <- bind.tip(binary_tree, 'ROOT', edge.length=1)
    rooted_binary <- reroot(rooted_binary, node.number=Ntip(binary_tree)+1)
    binary_tree <- rooted_binary
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

#Function for automatically evaluating a series of trees against one gold tree
#Return the tree which best matches the gold tree
best_matching_tree <- function(gold_tree, test_forest, forest_names=NULL, add_root=TRUE) {
  
  #Create lists for TreeDist and QuartetDivergence scores
  TD_scores <- c()
  QD_scores <- c()
  
  #Iterate through test trees and measure TreeDist and QuartetDivergence
  for (test_tree in test_forest) {
    
    tree_dist <- TreeDistance(gold_tree, test_tree)
    #statuses <- QuartetStatus(gold_tree, test_tree)
    #QD <- QuartetDivergence(statuses, similarity = FALSE)
    GQD <- gen_quartet_distance(gold_tree, test_tree, add_root=add_root)
    TD_scores <- append(TD_scores, tree_dist)
    QD_scores <- append(QD_scores, GQD)
  }
  
  #Get overall scores by averaging TreeDist and QuartetDivergence
  #scores <- (TD_scores + QD_scores) / 2
  
  #Only consider the Generalized Quartet Distances
  scores <- QD_scores
  
  #Get index of the tree with the minimum distance from the gold tree
  min_index <- which.min(scores)
  
  #Print the name of the best tree if the corresponding names were supplied
  if(!is.null(forest_names)) {
    print(paste('Best match:', forest_names[[min_index]]))
  }
  
  #Print the best tree's scores
  print(paste('TreeDist:', round(TD_scores[[min_index]],2)))
  print(paste('QuartetDivergence:', round(QD_scores[[min_index]],2)))
  
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
  family_trees <- list.files(path=paste('Results/', family, sep=''))
  family_trees <- family_trees[grep('.tre', family_trees)]
  if (length(family_trees[grep('binary', family_trees)]) > 0) {
    family_trees <- family_trees[-grep('binary', family_trees)]
  }
  family_trees <- paste(local_dir, '/Results/', family, '/', family_trees, sep='')
  
  #Sort trees by cognate detection and evaluation method
  cognate_methods <- c('none', 'Phonetic', 'PMI', 'Surprisal', 'Hybrid', 'gold')
  eval_methods <- c('Phonetic-calibrated', 'Phonetic-uncalibrated', 
                    'PMI-calibrated', 'PMI-uncalibrated',
                    'Surprisal-calibrated', 'Surprisal-uncalibrated',
                    'Hybrid-calibrated', 'Hybrid-uncalibrated')
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
        tree <- method_forest[[i]]
        TD <- TreeDistance(family_gold, tree)
        GQD <- gen_quartet_distance(family_gold, tree, add_root=TRUE)
        
        #Add a row to the tree_results data frame with these values
        row <- list(family=family, 
                    cognate_method=cognate_method, eval_method=eval_method, tree_type=linkage,
                    TreeDist=TD, GenQuartetDist=GQD)
        tree_results <- rbind(tree_results, row)
        
        #Save the tree to list for overall comparison
        all_trees[[paste(method, linkage, sep='_')]] = tree
        
      }

      #Find the maximum clade credibility (MCC) tree among these
      mcc_tree <- maxCladeCred(method_forest)
      
      #Generate a majority consensus tree from these
      #consensus_tree <- consensus(method_forest, p=0.5)
      
      #Evaluate the MCC and consensus trees for TreeDist and Generalized Quartet Distance
      TD_MCC <- TreeDistance(family_gold, mcc_tree)
      GQD_MCC <- gen_quartet_distance(family_gold, mcc_tree, add_root=TRUE)
      #TD_consensus <- TreeDistance(family_gold, consensus_tree)
      #GQD_consensus <- gen_quartet_distance(family_gold, consensus_tree, add_root=TRUE)
      
      #Add a row to the tree_results data frame with these values
      row_MCC <- list(family=family, 
                      cognate_method=cognate_method, eval_method=eval_method, 
                      tree_type='MaxCladeCredibility',
                      TreeDist=TD_MCC, GenQuartetDist=GQD_MCC)
      tree_results <- rbind(tree_results, row_MCC)
      
      #row_consensus <- list(family=family, 
      #                      cognate_method=cognate_method, eval_method=eval_method, 
      #                      tree_type='MajorityConsensus',
      #                      TreeDist=TD_consensus, GenQuartetDist=GQD_consensus)
      #tree_results <- rbind(tree_results, row_consensus)
    }
  } 
  
  
  #Evaluate and determine the best trees
  auto_trees <- all_trees[-grep('gold', names(all_trees))]
  gold_trees <- all_trees[grep('gold', names(all_trees))]
  best_auto_tree <- best_matching_tree(family_gold, auto_trees, names(auto_trees), add_root=TRUE)
  best_gold_tree <- best_matching_tree(family_gold, gold_trees, names(gold_trees), add_root=TRUE)
  cat('\n')
  
  #Plot and save the evaluation of the best tree using QuartetDivergence diagram
  png_plot_path <- paste('Results/', family, '/', family, "_best_auto.png", sep='')
  tre_plot_path <- paste('Results/', family, '/', family, "_best_auto.tre", sep='')
  png(filename=png_plot_path, width=700, height=700)
  VisualizeQuartets(ladderize(family_gold), ladderize(best_auto_tree), style='size', spectrum=rev(terrain.colors(101)))
  dev.off()
  write.tree(best_auto_tree, file=tre_plot_path)
  
  png_plot_path <- paste('Results/', family, '/', family, "_best_gold.png", sep='')
  tre_plot_path <- paste('Results/', family, '/', family, "_best_gold.tre", sep='')
  png(filename=png_plot_path, width=700, height=700)
  VisualizeQuartets(ladderize(family_gold), ladderize(best_gold_tree), style='size', spectrum=rev(terrain.colors(101)))
  dev.off()
  write.tree(best_gold_tree, file=tre_plot_path)
  
}

#Write tree evaluation results to a csv file
write.csv(tree_results, paste(local_dir, 'Results/tree_evaluation_results.csv', sep='/'), row.names = FALSE)
