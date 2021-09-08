library(TreeDist)
library(Quartet)
library(phytools)

gold_uralic <- '(((Livonian:2,((Estonian:2,Votic:2)Central_Finnic:1,((Veps:3,Ingrian:2,Karelian:2)Ladogan:1,Finnish:3)North_Finnic:1)Neva:1)Coastal_Finnic:1,Võro:2)Finnic:1,Hungarian:2,Khanty:4,Mansi:4,Meadow Mari:3,Erzya:2,((Komi-Permyak:2,Komi-Zyrian:1)Komi:1,Udmurt:2)Permian:1,((Skolt Saami:3,Kildin Saami:2)Eastern_Saami:1,(North Saami:3,South Saami:2)Western_Saami:1)Saami:1,(Tundra Nenets:4,Selkup:3,Nganasan:2)Samoyedic:1)Uralic;
'
gold_uralic = ape::read.tree(text = gold_uralic)


my_uralic = '(((((Meadow Mari:4.13,Erzya:4.13):0.19,(((Skolt Saami:2.78,Kildin Saami:2.78):0.34,(North Saami:2.56,South Saami:2.56):0.56):0.97,((((Võro:1.82,Estonian:1.82):0.26,Votic:2.08):0.32,(((Karelian:1.13,Ingrian:1.13):0.26,Finnish:1.39):0.57,Veps:1.97):0.43):0.43,Livonian:2.83):1.27):0.23):0.14,((Komi-Permyak:1.40,Komi-Zyrian:1.40):1.16,Udmurt:2.56):1.90):0.13,((Mansi:3.67,Khanty:3.67):0.78,Hungarian:4.45):0.14):0.07,((Tundra Nenets:3.86,Nganasan:3.86):0.32,Selkup:4.18):0.48);'
my_uralic = ape::read.tree(text = my_uralic)

#Note: gold_uralic had underscores where my_uralic had spaces; labels have to be identical
#so I just changed the underscores to spaces manually so that the tips match

VisualizeMatching(ClusteringInfoDistance, gold_uralic, my_uralic)
TreeDistance(gold_uralic, my_uralic)
VisualizeQuartets(gold_uralic, my_uralic)
