#Load packages for loading and evaluating phylogenetic trees
library(TreeDist)
library(Quartet)
library(phytools)

#Set working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))
local_dir <- getwd()

#Generalized Quartet Distance, as described by Pompei, Loreto, & Tria (2011)
gen_quartet_distance <- function(non_binary_tree, binary_tree) {
  
  #norm : number of resolved ("butterfly") quartets in reference/non-binary tree
  norm <- ResolvedQuartets(non_binary_tree)[[1]]
  
  #diff_butterflies : number of resolved ("butterfly") quartets which differ between the two trees
  butterflies <- SharedQuartetStatus(cf=non_binary_tree, trees=c(binary_tree))
  diff_butterflies <- butterflies[[4]]
  
  return(diff_butterflies/norm)
}

#Generalized Robinson-Foulds 


#Function for loading a series of Newick tree files into a MultiPhylo object
load_forest <- function(newick_files) {
  forest <- c()
  for (file in newick_files) {
    forest <- append(forest, read.newick(file))
  }
  return(forest)
}

#Function for automatically evaluating a series of trees against one gold tree
#Return the tree which best matches the gold tree
best_matching_tree <- function(gold_tree, test_forest, forest_names=NULL) {
  
  #Create lists for TreeDist and QuartetDivergence scores
  TD_scores <- c()
  QD_scores <- c()
  
  #Add labeled root to gold tree and reroot around it
  rooted_gold <- bind.tip(gold_tree, 'ROOT', edge.length=1)
  rooted_gold <- reroot(rooted_gold, node.number=Ntip(gold_tree)+1)
  gold_tree <- rooted_gold

  #Iterate through test trees and measure TreeDist and QuartetDivergence
  for (test_tree in test_forest) {
    
    #Add labeled root to test tree and reroot around it
    rooted_tree <- bind.tip(test_tree, 'ROOT', edge.length=1)
    rooted_tree <- reroot(rooted_tree, node.number=Ntip(test_tree)+1)
    test_tree <- rooted_tree
    
    tree_dist <- TreeDistance(gold_tree, test_tree)
    #statuses <- QuartetStatus(gold_tree, test_tree)
    #QD <- QuartetDivergence(statuses, similarity = FALSE)
    QD <- gen_quartet_distance(gold_tree, test_tree)
    TD_scores <- append(TD_scores, tree_dist)
    QD_scores <- append(QD_scores, QD)
  }
  
  #Get overall scores by averaging TreeDist and QuartetDivergence
  #scores <- (TD_scores + QD_scores) / 2
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
              'Quechuan',
              'Japonic',
              'Uto-Aztecan',
              'Vietic'
              )

#Iterate through families, identify the best tree
for (family in families) {

  #Load gold Glottolog tree
  family_gold <- read.newick(paste('Gold/', family, '_pruned.tre', sep=''))
  
  #Load distance-based trees into a MultiPhylo forest
  #Filter only trees not based on gold cognate sets
  family_trees <- list.files(path=paste('Results/', family, sep=''))
  family_trees <- family_trees[grep('.tre', family_trees)]
  gold_trees <- family_trees[grep('gold', family_trees)]
  gold_trees <- paste(local_dir, '/Results/', family, '/', gold_trees, sep='')
  gold_forest <- load_forest(gold_trees)
  
  family_trees <- family_trees[-grep('gold', family_trees)]
  family_trees <- paste(local_dir, '/Results/', family, '/', family_trees, sep='')
  family_forest <- load_forest(family_trees)
  
  #Remove full filepath from tree names
  family_trees <- strsplit(family_trees, '/')
  family_trees <- sapply(family_trees, tail, 1)
  gold_trees <- strsplit(gold_trees, '/')
  gold_trees <- sapply(gold_trees, tail, 1)
  
  #Evaluate and determine the best tree
  best_tree <- best_matching_tree(family_gold, family_forest, family_trees)
  best_gold_tree <- best_matching_tree(family_gold, gold_forest, gold_trees)
  
  #Plot and save the evaluation of the best tree using QuartetDivergence diagram
  plot_path <- paste('Results/', family, '/', family, "_best_auto.png", sep='')
  png(filename=plot_path, width=960, height=960)
  VisualizeQuartets(ladderize(family_gold), ladderize(best_tree))
  dev.off()
  
  plot_path <- paste('Results/', family, '/', family, "_best_gold.png", sep='')
  png(filename=plot_path, width=960, height=960)
  VisualizeQuartets(ladderize(family_gold), ladderize(best_gold_tree))
  dev.off()
  
}

for (family in families) { 
  family_gold <- read.newick(paste('Gold/', family, '_pruned.tre', sep='')) 
  print(family)
  dm <- cophenetic(family_gold)
  dv <- 0
  total <- 0
  for (i in seq(1,Ntip(family_gold))) {
    for (j in seq(1,Ntip(family_gold))) {
      if (i != j) {
        d <- dm[i,j]
        dv <- dv + d
        total <- total + 1
      }
      
      
    }
  }
  #print(sum(cophenetic(family_gold)) / length(cophenetic(family_gold)))
  print(dv/Ntip(family_gold))
}
