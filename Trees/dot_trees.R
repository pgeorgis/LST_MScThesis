library(ggtree)
library(stringr)

#Set working directory to location where this script is saved
library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))
local_dir <- getwd()

lang_data <- read.csv("/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Datasets/Languages.csv", sep="\t")

#ARABIC
family <- 'Arabic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset=='Arabic',]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 4)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.8), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE) + 
  xlim(0, 1.1)

#BALTO-SLAVIC
family <- 'Balto-Slavic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[grep('Balto-Slavic', lang_data$Classification),]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.84), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.1)

#BANTU
family <- 'Bantu'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset=='Bantu',]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups,tail, n=1) #,"[", 4)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.81), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE) + 
  xlim(0, 0.95)

#DRAVIDIAN
family <- 'Dravidian'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.78), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.9)

#HELLENIC
family <- 'Hellenic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.35), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, .5)

#HOKAN
family <- 'Hokan'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Tohono Oodham')] = "Tohono O'odham"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, "[", 1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.69), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, .8)

#ITALIC
family <- 'Italic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
best_gold_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_gold.tre', sep='_'), sep='/'))
best_gold_tree$tip.label <- str_replace_all(best_gold_tree$tip.label, '_', ' ')
best_gold_tree$tip.label <- str_replace_all(best_gold_tree$tip.label, '\\{', '(')
best_gold_tree$tip.label <- str_replace_all(best_gold_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, tail, n=1)
subgroups[grep('Catalan', family_data$Name)] = 'Ibero-Romance'
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1.34), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.8)
ggtree(best_gold_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=.78), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1)

#JAPONIC
family <- 'Japonic'
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_gold_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_gold.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_gold_tree$tip.label <- str_replace_all(best_gold_tree$tip.label, '_', ' ')
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1.43), size=3, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.6)

#POLYNESIAN
family <- 'Polynesian'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Austral (Raivavae)')] = "Austral (Ra'ivavae)"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=1.1), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1.5)

#QUECHUAN
family <- 'Quechuan'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.26), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.005, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.4)

#SINITIC
family <- 'Sinitic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Haerbin')] = "Ha'erbin"
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Xian')] = "Xi'an"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.44), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.5)

#TURKIC
family <- 'Turkic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.43), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 0.5)

alt_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'alt_auto.tre', sep='_'), sep='/'))
alt_auto_tree$tip.label <- str_replace_all(alt_auto_tree$tip.label, '_', ' ')
alt_auto_tree$tip.label <- str_replace_all(alt_auto_tree$tip.label, '\\{', '(')
alt_auto_tree$tip.label <- str_replace_all(alt_auto_tree$tip.label, '\\}', ')')
ggtree(alt_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=.75), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE, show.legend=FALSE) + 
  xlim(0, 1)

#URALIC
family <- 'Uralic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, "[", 2)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.82), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  #scale_color_manual(values=c(Finnic = '#FF6699', #pink
  #                            Saami = '#99FFFF', #light blue
  #                            Mordvin = '#66CC33', #green
  #                            Mari = '#CC9900', #burnt yellow
  #                            Permic = '#339999', #teal
  #                            Ugric = '#9933CC', #purple
  #                            Samoyedic = '99CCCC')) + #blue gray 
  
  xlim(0, 1)

#UTO-AZTECAN
family <- 'Uto-Aztecan'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label[which(best_auto_tree$tip.label == 'Tohono Oodham')] = "Tohono O'odham"
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ",")
subgroups = sapply(subgroups, tail, n=1)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.95), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.02, align=TRUE, show.legend=FALSE) + 
  geom_cladelabel(node=53, label='Northern Uto-Aztecan', offset=0.34, align=TRUE) +
  geom_cladelabel(node=36, label='Southern Uto-Aztecan', offset=0.34, align=TRUE) +
  xlim(0, 1.5)

#VIETIC
family <- 'Vietic'
best_auto_tree <- read.tree(file=paste(local_dir, 'Results', family, paste(family, 'best_auto.tre', sep='_'), sep='/'))
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '_', ' ')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\{', '(')
best_auto_tree$tip.label <- str_replace_all(best_auto_tree$tip.label, '\\}', ')')
family_data <- lang_data[lang_data$Dataset==family,]
subgroups = strsplit(family_data$Classification, ", ")
subgroups = sapply(subgroups, "[", 3)
dd <- data.frame(Taxa=family_data$Name, Classification=subgroups)
ggtree(best_auto_tree) %<+% dd + 
  geom_tippoint(aes(color=Classification, x=0.76), size=5, show.legend=TRUE) + 
  geom_tiplab(aes(color=Classification), offset=0.01, align=TRUE) + 
  xlim(0, 1)

#tree <- best_auto_tree
#ggtree(tree) + geom_text(aes(label=node), hjust=-.3) + geom_tiplab()
#53, 36