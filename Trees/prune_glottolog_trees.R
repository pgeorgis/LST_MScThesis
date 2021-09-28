library(ape) #Analysis of Phylogenetics and Evolution in R
library(phangorn)
library(phytools)
library(geiger)
library(dplyr)
library(stringi)
library(stringr)

#Set working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))
local_dir <- getwd()

#Load csv with language data
setwd("..")
lang_data <- read.csv('Datasets/Languages.csv', sep='\t')
setwd(local_dir)

#Function from: https://rdrr.io/github/bstaggmartin/backwards-BM-simulator/src/R/mis_multi.bind.tip.R
multi.bind.tip<-function(tree,names,edge.lengths=NULL,nodes,positions=0){
  if(is.null(edge.lengths)){
    edge.lengths<-NA
  }
  args.list<-list(names=names,edge.lengths=edge.lengths,nodes=nodes,positions=positions)
  max.len<-max(sapply(args.list,length))
  for(i in 1:length(args.list)){
    args.list[[i]]<-rep(args.list[[i]],length.out=max.len)
  }
  nodes<-args.list$nodes
  positions<-args.list$positions
  names(nodes)<-ifelse(nodes<=length(tree$tip.label),nodes+tree$Nnode,nodes-length(tree$tip.label))
  args.list<-lapply(args.list,function(ii) ii[order(as.numeric(names(nodes)),-positions)])
  nodes<-nodes[order(as.numeric(names(nodes)))]
  int.nodes<-nodes>length(tree$tip.label)
  tips<-nodes<=length(tree$tip.label)
  for(i in 1:max.len){
    try.tree<-try(phytools::bind.tip(tree,args.list$names[i],
                                     if(is.na(args.list$edge.lengths[i])) NULL else args.list$edge.lengths[i],
                                     args.list$nodes[i],
                                     args.list$positions[i]),silent=T)
    if(inherits(try.tree,'try-error')){
      warning("failed to bind tip '",args.list$names[i],"' to node ",nodes[i],' due to following error:\n',
              try.tree)
    }else{
      tree<-try.tree
      args.list$nodes[int.nodes]<-args.list$nodes[int.nodes]+if(args.list$positions[i]<=0) 1 else 2
      tmp<-which(tree$tip.label==args.list$names[i])
      tmp<-args.list$nodes>=tmp
      args.list$nodes[tips&tmp]<-args.list$nodes[tips&tmp]+1
    }
  }
  tree
}


#Function to turn nodes into tips and prune off extra tips
reformat_tree <- function(tree, languages) { 
  #Remove any languages which couldn't be found in Glottolog (and thus have no Glottolog name)
  languages <- stri_remove_empty(languages)
  
  #Replace parentheses in language names with curly brackets in order to match name in Newick format
  #(parentheses are used for grouping taxa, so parentheses in language names are written as curly brackets instead)
  languages <- lapply(languages, gsub, pattern="\\(", replacement="{")
  languages <- lapply(languages, gsub, pattern="\\)", replacement="}")
  
  #Turn named list of languages resulting from lapply back into character vector, using values
  languages <- unlist(languages, use.names=FALSE)
  
  #Identify languages from dataset which are missing as tips in the tree
  missing_langs <- languages[!languages %in% tree$tip.label]
  
  if (length(missing_langs)>0) {
    #Get indices of the nodes with the names of the missing languages
    node_indices <- sapply(missing_langs, match, tree$node.label) 
    node_indices <- node_indices + Ntip(tree) 
    
    #Languoids whose node index could not be found (node_index = NA) are typically dialects 
    #which were not listed in the original Glottolog tree
    #e.g. Ligurian {Rapallo}, Piedmontese {Barbania}
    #Note that they all include curly brackets in their names
    #Check whether there are any such languoids by checking for NA indices
    NA_langs <- which(is.na(node_indices))
    if (length(NA_langs)>0) {
      #Get the node index of the dialects' parent language by splitting by the " {"
      #and finding a match with the first part
      #e.g. "Piedmontese {Barbania}" --> "Piedmontese"
      NA_names <- names(NA_langs)
      split_names <- strsplit(NA_names, " \\{")
      parents <- sapply(split_names, "[", 1)
      parent_node_indices <- sapply(parents, grep, tree$node.label) 
      parent_node_indices <- sapply(parent_node_indices, "[", 1)
      parent_node_indices <- parent_node_indices + Ntip(tree)
      
      #Address languages which still have not been matched, e.g. "Piedmontese"
      #In this case the parent is a tip of the tree rather than a node, so we find this instead
      still_NA_langs <- which(is.na(parent_node_indices))
      if (length(still_NA_langs)>0) {
        still_NA_names <- names(still_NA_langs)
        
        #Arbitrarily choose the last match -- this yields the correct match/position in the tree
        #for the Turinese Piedmontese dialects, but may not always work (unclear how to resolve definitively)
        parent_tip_indices <- sapply(still_NA_names, grep, tree$tip.label)
        parent_tip_indices <- parent_tip_indices[length(parent_tip_indices)]
        parent_tip_indices <- sapply(parent_tip_indices, "[", 1)
        parent_node_indices[still_NA_langs] <- parent_tip_indices
      }
      
      for (i in seq(length(NA_langs))) {
        node_indices[[NA_langs[[i]]]] <- parent_node_indices[[i]]
      }
    }
    
    
    
    #Add the missing languages as tips of the tree under their own nodes
    tree <- multi.bind.tip(tree=tree,
                           names=missing_langs,
                           edge.lengths=rep(1,length(node_indices)),
                           nodes=node_indices,
                           positions=rep(0,length(node_indices)))
  }
  
  #Prune all tips not in the given list of languages and return the pruned tree
  tree <- drop.tip(tree, setdiff(tree$tip.label,languages))
  return(tree)
}

#Get list of families
families <- c('Arabic', 
              'Balto-Slavic', 
              'Dravidian',
              'Italic', 
              'Polynesian', 
              'Sinitic',
              'Turkic', 
              'Uralic',
              
              #Hokan non-isolate subfamilies
              #'Chimariko',
              'Cochimi-Yuman',
              #'Karuk',
              'Pomoan',
              #'Seri',
              #'Shastan',
              'Tequistlatecan',
              'Yana')

for (family in families) {
  
  #Load original Glottolog tree for family
  tree <- read.newick(paste(local_dir, '/Gold/', family, '.tre', sep=""))
  
  #Plot the original Glottolog tree
  #plot(tree)
  
  #Extract data for this family
  family_data <- filter(lang_data, grepl(family, lang_data$Classification, fixed=TRUE))
  
  #Get list of languages included in family's dataset
  langs <- as.vector(family_data$Name)
  
  #Load the preprocessed Glottolog tree for family
  preprocessed_tree <- read.newick(paste(local_dir, '/Gold/', family, '_preprocessed.tre', sep=""))
  
  #Plot the preprocessed tree before reformatting and pruning
  #plot(preprocessed_tree)
  
  #Reformat the tree
  new_tree <- reformat_tree(preprocessed_tree, langs)
  
  #Plot and save the new tree if there are at least 2 tips (would raise error otherwise)
  if (Ntip(new_tree) > 1) {
    plot_path <- paste('Gold/Plots/', family, "_pruned.png", sep='')
    png(filename=plot_path, width=960, height=960)
    plot(new_tree)
    dev.off()
  }
  
  #Write the reformatted/pruned tree in Newick format
  write.tree(new_tree, file=paste("Gold/", family, "_pruned.tre", sep=""))
}

