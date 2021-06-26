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

baltoslav_tree <- read.newick('Gold/Balto-Slavic.tre')
baltoslav_data <- filter(lang_data, grepl('Balto-Slavic', lang_data$Classification, fixed=TRUE))
baltoslav_names <- as.vector(baltoslav_data$Glottolog.Name)

#Still to do:
#iterate through names of languages in dataset
#if the language is not in the tree's list of tips, then add it as a tip 
#will need to specify where to add it: use the index of the node where the language is currently (it is usually a node, not a tip)
#then remove all extra tips which are not in the list of languages in the dataset
#finally, turn this into a for loop so that it is done automatically for all families
#ideally: rename the languages to local name