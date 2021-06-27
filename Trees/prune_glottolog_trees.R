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

#Get list of files in Gold tree directory
#files <- list.files(paste(local_dir, "/Gold", sep=""))

#Get list of families
families <- c('Arabic', 
              'Balto-Slavic', 
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
  
  #Load tree for family
  tree <- read.newick(paste(local_dir, '/Gold/', family, '.tre', sep=""))
  
  #Plot the original Glottolog tree
  plot(tree)
  
  #Extract data for this family
  family_data <- filter(lang_data, grepl(family, lang_data$Classification, fixed=TRUE))
  
  #Get list of languages included in family's dataset
  langs <- as.vector(family_data$Glottolog.Name)
  
  #Reformat the tree
  new_tree <- reformat_tree(tree, langs)
  
  #Plot the new tree if there are at least 2 tips (would raise error otherwise)
  if (Ntip(new_tree) > 1) {
    plot(new_tree)
  }
  
  #Write the reformatted/pruned tree in Newick format
  write.tree(new_tree, file=paste("Gold/", family, "_pruned.tre", sep=""))
}

