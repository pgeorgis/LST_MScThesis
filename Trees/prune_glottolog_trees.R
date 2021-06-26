library(ape) #Analysis of Phylogenetics and Evolution in R
library(phangorn)
library(phytools)
library(geiger)
library(dplyr)

#Set working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))
local_dir <- getwd()

#Load csv with language data
setwd("..")
lang_data <- read.csv('Datasets/Languages.csv', sep='\t')
setwd(local_dir)

#Function to turn nodes into tips and prune off extra tips
reformat_tree <- function(tree, languages) {
  #Iterate through the list of languages
  for (lang in languages) {
    
    #Check whether the language name is already a tip of the tree
    if (lang %in% tree$tip.label == FALSE) { 
      
      #If not, we assume it is instead a node of the tree and extract its node number
      node_index <- match(lang, tree$node.label) + Ntip(tree)
      
      #Add the language as a tip of the tree under its own node
      tree <- bind.tip(tree, lang, edge.length=1, where=node_index, position=0)
    }
  }
  
  #Prune all tips not in the given list of languages
  tree <- drop.tip(tree, setdiff(tree$tip.label,languages))
  
  #Return the reformatted tree
  return(tree)
}

#BALTO-SLAVIC
baltoslav_tree <- read.newick('Gold/Balto-Slavic.tre')
baltoslav_data <- filter(lang_data, grepl('Balto-Slavic', lang_data$Classification, fixed=TRUE))
baltoslav_langs <- as.vector(baltoslav_data$Glottolog.Name)
new_baltoslav <- reformat_tree(baltoslav_tree, baltoslav_langs)
write.tree(new_baltoslav,file="Gold/Balto-Slavic_pruned.tre")

#ARABIC
arabic_tree <- read.newick('Gold/Arabic.tre')
arabic_data <- filter(lang_data, grepl('Semitic', lang_data$Classification, fixed=TRUE))
arabic_langs <- as.vector(arabic_data$Glottolog.Name)
new_arabic <- reformat_tree(arabic_tree, arabic_langs)
#write.tree(new_arabic,file="Gold/Arabic_pruned.tre")

#ITALIC
italic_tree <- read.newick('Gold/Italic.tre')
italic_data <- filter(lang_data, grepl('Italic', lang_data$Classification, fixed=TRUE))
italic_langs <- as.vector(italic_data$Glottolog.Name)
new_italic <- reformat_tree(italic_tree, italic_langs)
#write.tree(new_italic,file="Gold/Italic_pruned.tre")

#POLYNESIAN
polynesian_tree <- read.newick('Gold/Polynesian.tre')
polynesian_data <- filter(lang_data, grepl('Polynesian', lang_data$Classification, fixed=TRUE))
polynesian_langs <- as.vector(polynesian_data$Glottolog.Name)
new_polynesian <- reformat_tree(polynesian_tree, polynesian_langs)
#write.tree(new_polynesian,file="Gold/Polynesian_pruned.tre")

#SINITIC
sinitic_tree <- read.newick('Gold/Sinitic.tre')
sinitic_data <- filter(lang_data, grepl('Sinitic', lang_data$Classification, fixed=TRUE))
sinitic_langs <- as.vector(sinitic_data$Glottolog.Name)
new_sinitic <- reformat_tree(sinitic_tree, sinitic_langs)
write.tree(new_sinitic,file="Gold/Sinitic_pruned.tre")

#TURKIC
turkic_tree <- read.newick('Gold/Turkic.tre')
turkic_data <- filter(lang_data, grepl('Turkic', lang_data$Classification, fixed=TRUE))
turkic_langs <- as.vector(turkic_data$Glottolog.Name)
new_turkic <- reformat_tree(turkic_tree, turkic_langs)
#write.tree(new_turkic,file="Gold/Turkic_pruned.tre")

#URALIC
uralic_tree <- read.newick('Gold/Uralic.tre')
uralic_data <- filter(lang_data, grepl('Uralic', lang_data$Classification, fixed=TRUE))
uralic_langs <- as.vector(uralic_data$Glottolog.Name)
new_uralic <- reformat_tree(uralic_tree, uralic_langs)
#write.tree(new_uralic,file="Gold/Uralic_pruned.tre")

#Still to do:
#figure out why it's not working for other families (Arabic, Uralic, Polynesian, Italic, Turkic)
#why only working for Balto-Slavic and Sinitic?
#test Hokan last

#once that's done:
#turn this into a for loop so that it is done automatically for all families
#ideally: rename the languages to local name