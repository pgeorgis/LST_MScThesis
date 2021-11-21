library(ggtree)
library(stringr)

#Set initial working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))

#Designate the directory where the tree results are saved
setwd('..')
tree_dir <- paste(getwd(), '/Results/Trees', sep='')

#Load CSV with data about the languages
lang_data <- read.csv("Datasets/Languages.csv", sep="\t")

#Function for modifying format of tree tip labels (doculect names) 
#in order to match how they are written in the CSV
reformat_tips <- function(tree) {
  #Replace "_" with spaces in tree tip labels
  tree$tip.label <- str_replace_all(tree$tip.label, '_', ' ')
  
  #Replace curly brackets with parentheses
  tree$tip.label <- str_replace_all(tree$tip.label, '\\{', '(')
  tree$tip.label <- str_replace_all(tree$tip.label, '\\}', ')')
  
  return(tree)
}


#ARABIC
family <- 'Arabic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset=='Arabic',]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 4)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.82), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.05)
dev.off()

#BALTO-SLAVIC
family <- 'Balto-Slavic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[grep('Balto-Slavic', lang_data$Classification),]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.88), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

#BANTU
family <- 'Bantu'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset=='Bantu',]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups,tail, n=1) #,"[", 4)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_minor.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.95), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups,"[", 4)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_major.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.95), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

#DRAVIDIAN
family <- 'Dravidian'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.9), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1)
dev.off()

#HELLENIC
family <- 'Hellenic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.53), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.7)
dev.off()

#HOKAN
family <- 'Hokan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, "[", 1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.96), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.2)
dev.off()

#ITALIC
family <- 'Italic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
subgroups[grep('Catalan', family_data$Name)] = 'Ibero-Romance'
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.825), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

#JAPONIC
family <- 'Japonic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=800)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1.65), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.8)
dev.off()

#POLYNESIAN
family <- 'Polynesian'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Austral (Raivavae)')] = "Austral (Ra'ivavae)"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'RennellBellona')] = "Rennell-Bellona"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'RakahangaManihiki')] = "Rakahanga-Manihiki"
family_data <- lang_data[lang_data$Dataset==family,]
family_data$Name[which(family_data$Name == 'RennellBellona')] =  "Rennell-Bellona"
family_data$Name[which(family_data$Name == 'RakahangaManihiki')] =  "Rakahanga-Manihiki"
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1.1), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.4)
dev.off()

#QUECHUAN
family <- 'Quechuan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_major.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.39), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.5)
dev.off()

subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_minor.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.39), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.5)
dev.off()

#SINITIC
family <- 'Sinitic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Haerbin')] = "Ha'erbin"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Xian')] = "Xi'an"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.78), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.9)
dev.off()

#TURKIC
family <- 'Turkic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.69), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.8)
dev.off()

#URALIC
family <- 'Uralic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.9), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

#UTO-AZTECAN
family <- 'Uto-Aztecan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Tohono Oodham')] = "Tohono O'odham"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.94), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  #geom_cladelabel(node=53, label='Northern Uto-Aztecan', offset=0.34, align=TRUE) +
  #geom_cladelabel(node=36, label='Southern Uto-Aztecan', offset=0.34, align=TRUE) +
  xlim(0, 1.2)
dev.off()

#VIETIC
family <- 'Vietic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.95), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

#POMOAN
family <- 'Pomoan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[grep('Pomoan', lang_data$Classification),]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.78), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1)
dev.off()

#YUMAN
family <- 'Yuman'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[grep('Yuman', lang_data$Classification),]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.57), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.65)
dev.off()