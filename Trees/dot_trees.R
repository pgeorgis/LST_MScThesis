library(ggtree)
library(stringr)
library(ggplot2)

#Set initial working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))

#Designate the directory where the tree results are saved
setwd('..')
tree_dir <- paste(getwd(), '/Results/Trees', sep='')
gold_tree_dir <- paste(getwd(), '/Trees/Gold', sep='')

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
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.4)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Arabic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 5)
ggsave(png_path, dpi=300)


#BALTO-SLAVIC
family <- 'Balto-Slavic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[grep('Balto-Slavic', lang_data$Classification),]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.3)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Balto-Slavic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 9)
ggsave(png_path, dpi=300)

#BANTU
family <- 'Bantu'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset=='Bantu',]
subgroups = strsplit(family_data$Classification, ", ")
major_subgroups = sapply(subgroups,tail, n=1) #,"[", 4)
minor_subgroups = sapply(subgroups,"[", 4)
dd <- data.frame(Taxa=family_data$Name, Major_Classification=major_subgroups, Classification=minor_subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1), size=4, show.legend=TRUE) + 
  geom_tippoint(aes(color=Major_Classification, x=1.03), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Major_Classification), offset=0.05, align=FALSE, show.legend=FALSE) + 
  xlim(0, 1.3)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Bantu
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification, x=6), size=4, show.legend=TRUE) + 
  geom_tippoint(aes(color=Major_Classification, x=6.23), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Major_Classification), offset=0.33, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 8)
ggsave(png_path, dpi=300)

#subgroups = strsplit(family_data$Classification, ", ")
#subgroups = sapply(subgroups,"[", 4)
#dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
#png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_major.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
#ggtree(best_auto_tree) %<+% dd + 
#  geom_tippoint(aes(color=Classification, x=1), size=5, show.legend=TRUE) + 
#  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
#  xlim(0, 1.2)
#dev.off()

#DRAVIDIAN
family <- 'Dravidian'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.55)
#dev.off()

best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto_rooted.tre', sep='_'), sep='/'))
best_alt_tree <- reformat_tips(best_alt_tree)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_alt_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.015, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.6)
#dev.off()
ggsave(png_path, dpi=300)


#Gold Dravidian
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 10.5)
ggsave(png_path, dpi=300)

#HELLENIC
family <- 'Hellenic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto_rooted.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.5)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Hellenic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 6)
ggsave(png_path, dpi=300)

#HOKAN
family <- 'Hokan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, "[", 1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
dd$Classification[which(dd$Classification == 'Cochimi-Yuman')] = 'Yuman'
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.99), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.2)
#dev.off()
ggsave(png_path, dpi=300)

best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto.tre', sep='_'), sep='/'))
best_alt_tree <- reformat_tips(best_alt_tree)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_alt_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.92), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.11)
#dev.off()
ggsave(png_path, dpi=300)

consensus_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'majority_consensus.tre', sep='_'), sep='/'))
consensus_tree <- reformat_tips(consensus_tree)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_majority_consensus.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=700)
ggtree(consensus_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.07, align=TRUE, show.legend=FALSE) + 
  xlim(0, 5)
dev.off()

#Gold Hokan
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 6.5)
ggsave(png_path, dpi=300)

#ITALIC
family <- 'Italic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
best_auto_tree <- reroot(best_auto_tree, 13)#72)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
subgroups[grep('Catalan', family_data$Name)] = 'Ibero-Romance'
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_rerooted.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  #xlim(0, 0.48)
  xlim(0, 1)
#dev.off()
ggsave(png_path, dpi=300, height=8)

#best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto.tre', sep='_'), sep='/'))
#best_alt_tree <- reformat_tips(best_alt_tree)
#png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
#ggtree(best_alt_tree) %<+% dd + 
#  geom_tippoint(aes(color=Classification, x=1.8), size=3, show.legend=TRUE) + 
#  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
#  xlim(0, 2.2)
#dev.off()

#Gold Italic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
subgroups[grep('Occitan', family_data$Name)] = 'Ibero-Romance'
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
dd[which(dd$Classification == 'Gallo-Romance'), 2] = 'Gallo-Rhaetian'
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=3) +
  theme(legend.text=element_text(size=8), legend.title=element_text(size=12)) +
  xlim(0, 15)
ggsave(png_path, dpi=300, height=8)

#JAPONIC
family <- 'Japonic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
dd$Classification[which(dd$Classification == ' Japanesic')] = ' Old Japanese'
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
png(filename=png_path, width=900, height=800)
ggtree(ladderize(best_auto_tree)) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.57)
dev.off()

best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto_rerooted.tre', sep='_'), sep='/'))
best_alt_tree <- reformat_tips(best_alt_tree)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(ladderize(best_alt_tree)) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.48)
#dev.off()
ggsave(png_path, dpi=300, height=8.5)

#Gold Japonic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=3) +
  theme(legend.text=element_text(size=8), legend.title=element_text(size=12)) +
  xlim(0, 7)
ggsave(png_path, dpi=300, height=8)

#POLYNESIAN
family <- 'Polynesian'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Austral (Raivavae)')] = "Austral (Ra'ivavae)"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'RennellBellona')] = "Rennell-Bellona"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'RakahangaManihiki')] = "Rakahanga-Manihiki"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Maori')] = "Māori"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Hawaiian')] = "Hawaiʻian"
family_data <- lang_data[lang_data$Dataset==family,]
family_data$Name[which(family_data$Name == 'RennellBellona')] =  "Rennell-Bellona"
family_data$Name[which(family_data$Name == 'RakahangaManihiki')] =  "Rakahanga-Manihiki"
family_data$Name[which(family_data$Name == 'Maori')] =  "Māori"
family_data$Name[which(family_data$Name == 'Hawaiian')] =  "Hawaiʻian"
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(ladderize(best_auto_tree)) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.015, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.65)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Polynesian
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
gold_tree$tip.label[which(gold_tree$tip.label == 'Austral (Raivavae)')] = "Austral (Ra'ivavae)"
gold_tree$tip.label[which(gold_tree$tip.label == 'RennellBellona')] = "Rennell-Bellona"
gold_tree$tip.label[which(gold_tree$tip.label == 'RakahangaManihiki')] = "Rakahanga-Manihiki"
gold_tree$tip.label[which(gold_tree$tip.label == 'Maori')] = "Māori"
gold_tree$tip.label[which(gold_tree$tip.label == 'Hawaiian')] = "Hawaiʻian"
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.2, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=8), legend.title=element_text(size=10)) +
  xlim(0, 12)
ggsave(png_path, dpi=300)

#QUECHUAN
family <- 'Quechuan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
major_subgroups = sapply(subgroups, "[", 2)
minor_subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Major_Classification=major_subgroups, Classification=minor_subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.505), size=5, show.legend=TRUE) + 
  geom_tippoint(aes(color=Major_Classification, x=0.485), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.025, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.65)
#dev.off()
ggsave(png_path, dpi=300)

#subgroups = strsplit(family_data$Classification, ", ")
#subgroups = sapply(subgroups, "[", 3)
#dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
#png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto_minor.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
#ggtree(best_auto_tree) %<+% dd + 
#  geom_tippoint(aes(color=Classification, x=0.49), size=5, show.legend=TRUE) + 
#  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
#  xlim(0, 0.6)
#dev.off()

#Gold Quechuan
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification, x=8.25), size=4, show.legend=TRUE) + 
  geom_tippoint(aes(color=Major_Classification, x=8), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.35, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 11)
ggsave(png_path, dpi=300)

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
  geom_tippoint(aes(color=Classification, x=1.11), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.3)
dev.off()

best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto.tre', sep='_'), sep='/'))
best_alt_tree <- reformat_tips(best_alt_tree)
best_alt_tree$tip.label[which(best_alt_tree$tip.label == 'Haerbin')] = "Ha'erbin"
best_alt_tree$tip.label[which(best_alt_tree$tip.label == 'Xian')] = "Xi'an"
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_alt_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.35)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Sinitic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
gold_tree$tip.label[which(gold_tree$tip.label == 'Haerbin')] = "Ha'erbin"
gold_tree$tip.label[which(gold_tree$tip.label == 'Xian')] = "Xi'an"
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 5)
ggsave(png_path, dpi=300)

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
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  xlim(0, 1)
dev.off()

best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto_rerooted.tre', sep='_'), sep='/'))
best_alt_tree <- reformat_tips(best_alt_tree)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_alt_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  xlim(0, 0.6)
#dev.off()
ggsave(png_path, dpi=300, height=6)

#Gold Turkic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 7.5)
ggsave(png_path, dpi=300)

#URALIC
family <- 'Uralic'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.86), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Uralic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
dd[which(dd$Taxa == 'Hungarian'), 2] = ' Hungarian'
dd[which(dd$Taxa == 'Khanty'), 2] = ' Khantyic'
dd[which(dd$Taxa == 'Mansi'), 2] = ' Mansic'
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 7.5)
ggsave(png_path, dpi=300)

#UTO-AZTECAN
family <- 'Uto-Aztecan'
best_auto_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto_rooted.tre', sep='_'), sep='/'))
best_auto_tree <- reformat_tips(best_auto_tree)
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Tohono Oodham')] = "Tohono O'odham"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_auto_tree) %<+% dd + 
  #geom_tippoint(aes(color=Classification, x=1), size=5, show.legend=TRUE) + 
  geom_tippoint(aes(color=Classification), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=FALSE, show.legend=FALSE) + 
  #geom_cladelabel(node=53, label='Northern Uto-Aztecan', offset=0.34, align=TRUE) +
  #geom_cladelabel(node=36, label='Southern Uto-Aztecan', offset=0.34, align=TRUE) +
  #xlim(0, 1.2)
  xlim(0, 0.65)
#dev.off()
ggsave(png_path, dpi=300, height=6.5)

#Gold Uto-Aztecan
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
gold_tree$tip.label[which(gold_tree$tip.label == 'Tohono Oodham')] = "Tohono O'odham"
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 8)
ggsave(png_path, dpi=300)

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
  geom_tippoint(aes(color=Classification, x=0.85), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)
dev.off()

best_alt_tree <- read.tree(file=paste(tree_dir, family, paste(family, 'best_alt_auto.tre', sep='_'), sep='/'))
best_alt_tree <- reformat_tips(best_alt_tree)
png_path <- paste(tree_dir, family, paste(family, 'dot_tree_best_alt_auto.png', sep='_'), sep='/')
#png(filename=png_path, width=900, height=700)
ggtree(best_alt_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1.03), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.015, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.25)
#dev.off()
ggsave(png_path, dpi=300)

#Gold Vietic
gold_tree <- read.tree(file=paste(gold_tree_dir, paste(family, '_pruned.tre', sep=''), sep='/'))
gold_tree <- reformat_tips(gold_tree)
png_path <- paste(gold_tree_dir, 'Plots', paste(family, 'dot_tree.png', sep='_'), sep='/')
ggtree(gold_tree, branch.length="none") %<+% dd + 
  geom_tippoint(aes(color=Classification), size=4, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.1, align=FALSE, show.legend=FALSE, size=4) +
  theme(legend.text=element_text(size=10), legend.title=element_text(size=12)) +
  xlim(0, 6)
ggsave(png_path, dpi=300)

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
  geom_tippoint(aes(color=Classification, x=0.85), size=5, show.legend=TRUE) + 
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
  geom_tippoint(aes(color=Classification, x=0.6), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.65)
dev.off()
