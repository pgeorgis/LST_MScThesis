#TREEDIST TUTORIAL
#Based on: https://cran.r-project.org/web/packages/TreeDist/vignettes/Using-TreeDist.html

library(TreeDist)

#Load two example trees
tree1 <- ape::read.tree(text = '(A, ((B, (C, (D, E))), ((F, G), (H, I))));')
tree2 <- ape::read.tree(text = '(A, ((B, (C, (D, (H, I)))), ((F, G), E)));')

#Calculate the distance between the two trees
distance <- TreeDistance(tree1, tree2)
#0.660383
#two identical trees would have distance = 0

#Comparing multiple trees
#Use TreeDistance() on lists of trees; will compare each pair of trees from both lists
oneTree <- ape::rtree(11)
twoTrees <- structure(list(one = ape::rtree(11), two = ape::rtree(11)),
                      class = 'multiPhylo')
threeTrees <- list(a = ape::rtree(11), b = ape::rtree(11), c = ape::rtree(11))

TreeDistance(oneTree, twoTrees)
TreeDistance(oneTree, threeTrees)
TreeDistance(twoTrees, threeTrees)

#Plot a visualization of the differences between two trees
VisualizeMatching(ClusteringInfoDistance, tree1, tree2)
#Each split is labeled with measure of its similarity, contributing to overall tree similarity score
tree3 <- ape::read.tree(text = '(E, ((B, (C, (D, (H, I)))), ((F, G), A)));')
VisualizeMatching(ClusteringInfoDistance, tree2, tree3)

#Example using trees of Romance/Italic languages
romance_tree1 <- ape::read.tree(text = '(Latin, (Sardinian, (Romanian, (Italian, ((French, Catalan), (Spanish, Portuguese))))));')
romance_tree2 <- ape::read.tree(text = '(Latin, (Romanian, ((French, Catalan), ((Italian, Sardinian), (Spanish, Portuguese)))));')
romance_tree3 <- ape::read.tree(text = '(Latin, (Sardinian, (Romanian, ((French, Catalan), (Italian, (Spanish, Portuguese))))));')
TreeDistance(romance_tree1, romance_tree2) #0.4438444
VisualizeMatching(ClusteringInfoDist, romance_tree1, romance_tree2)

TreeDistance(romance_tree1, romance_tree3) #0.2126733
VisualizeMatching(ClusteringInfoDist, romance_tree1, romance_tree3)
#e.g. split 1 is matched between the two, as the split which separates Sardinian and Latin from the rest
#split 2 separates Romanian from Italo-Western Romance
#split 3 separates Italian from Western romance in tree 1, but it is not matched in tree2
#split 4 separates Gallo-Romance from Ibero-Romance (and Italian, in tree 2)
#split 5 separates Ibero-Romance from Gallo-Romance/Italian

#Print the information displayed in the visualization, to access for further examination in R
ClusteringInfoDistance(romance_tree1, romance_tree2, reportMatching = TRUE)
#pairScores attribute lists the score of each possible matching of splits


