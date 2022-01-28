library(lingtypology)
setwd('/Users/phgeorgis/Documents/School/MSc/Saarland_University/Courses/Thesis/Datasets/')
lang_data <- read.csv("Languages.csv", sep="\t")

#Rename Family field of Hokan dataset to "Hokan"
lang_data[lang_data$Dataset=='Hokan',"Family"] = 'Hokan'

#Rename Niger-Congo --> Atlantic-Congo
lang_data[lang_data$Dataset=='Bantu',"Family"] = 'Atlantic-Congo'

#Map all languages by top-level family
map.feature(languages=lang_data$Name, features=lang_data$Family, latitude=lang_data$Latitude, longitude=lang_data$Longitude, color='Accent', zoom.control = TRUE)

#Map languages by dataset
lang_data[lang_data$Dataset=='Baltic',"Dataset"] = 'Balto-Slavic'
lang_data[lang_data$Dataset=='Slavic',"Dataset"] = 'Balto-Slavic'
lang_data[lang_data$Dataset=='NorthEuraLex',"Dataset"] = 'Balto-Slavic'
map.feature(languages=lang_data$Name, features=lang_data$Dataset, latitude=lang_data$Latitude, longitude=lang_data$Longitude, color='Accent', zoom.control = TRUE,
            map.orientation = "Pacific")


#Map Hokan
hokan = lang_data[lang_data$Dataset=='Hokan',]
hokan_subfamilies = hokan$Classification
hokan_subfamilies = strsplit(hokan_subfamilies, ",")
hokan_subfamilies = sapply(hokan_subfamilies, "[", 1)
map.feature(languages=hokan$Name, features=hokan_subfamilies, latitude=hokan$Latitude, longitude=hokan$Longitude)

#Map Italic
italic <- lang_data[lang_data$Dataset=='Italic',]
italic_subfamilies = italic$Classification
italic_subfamilies = strsplit(italic_subfamilies, ",")
italic_subfamilies = sapply(italic_subfamilies, tail, n=1)
map.feature(languages=italic$Name, features=italic_subfamilies, latitude=italic$Latitude, longitude=italic$Longitude)

#Map Arabic
arabic <- lang_data[lang_data$Dataset=='Arabic',]
arabic_subfamilies = arabic$Classification
arabic_subfamilies = strsplit(arabic_subfamilies, ", ")
arabic_subfamilies = sapply(arabic_subfamilies, "[", 4)
map.feature(languages=arabic$Name, features=arabic_subfamilies, latitude=arabic$Latitude, longitude=arabic$Longitude)

#Map Turkic
turkic <- lang_data[lang_data$Dataset=='Turkic',]
turkic_subfamilies = turkic$Classification
turkic_subfamilies = strsplit(turkic_subfamilies, ",")
turkic_subfamilies = sapply(turkic_subfamilies, "[", 2)
map.feature(languages=turkic$Name, features=turkic_subfamilies, latitude=turkic$Latitude, longitude=turkic$Longitude)

#Map Sinitic
sinitic <- lang_data[lang_data$Dataset=='Sinitic',]
sinitic_subfamilies = sinitic$Classification
sinitic_subfamilies = strsplit(sinitic_subfamilies, ",")
sinitic_subfamilies = sapply(sinitic_subfamilies, "[", 3)
map.feature(languages=sinitic$Name, features=sinitic_subfamilies, latitude=sinitic$Latitude, longitude=sinitic$Longitude,
            zoom.control = TRUE)

#Map Polynesian
polynesian <- lang_data[lang_data$Dataset=='Polynesian',]
polynesian_subfamilies = polynesian$Classification
polynesian_subfamilies = strsplit(polynesian_subfamilies, ",")
polynesian_subfamilies = sapply(polynesian_subfamilies, "[", 3)
map.feature(languages=polynesian$Name, features=polynesian_subfamilies, 
            latitude=polynesian$Latitude, longitude=polynesian$Longitude, 
            zoom.control = TRUE, map.orientation = "Pacific")

#Map Uralic
uralic <- lang_data[lang_data$Dataset=='Uralic',]
uralic_subfamilies = uralic$Classification
uralic_subfamilies = strsplit(uralic_subfamilies, ",")
uralic_subfamilies = sapply(uralic_subfamilies, "[", 2)
map.feature(languages=uralic$Name, features=uralic_subfamilies, latitude=uralic$Latitude, longitude=uralic$Longitude)

#Map Balto-Slavic
baltoslavic <- lang_data[grep('Balto-Slavic', lang_data$Classification),]
baltoslavic_subfamilies = baltoslavic$Classification
baltoslavic_subfamilies = strsplit(baltoslavic_subfamilies, ",")
baltoslavic_subfamilies = sapply(baltoslavic_subfamilies, tail, n=1)
map.feature(languages=baltoslavic$Name, features=baltoslavic_subfamilies, latitude=baltoslavic$Latitude, longitude=baltoslavic$Longitude,
            color='magma', zoom.control = TRUE)

#Map Dravidian
dravidian <- lang_data[lang_data$Dataset=='Dravidian',]
dravidian_subfamilies = dravidian$Classification
dravidian_subfamilies = strsplit(dravidian_subfamilies, ",")
dravidian_subfamilies = sapply(dravidian_subfamilies, tail, n=1)
map.feature(languages=dravidian$Name, features=dravidian_subfamilies, latitude=dravidian$Latitude, longitude=dravidian$Longitude)

#Map Quechuan
quechuan <- lang_data[lang_data$Dataset=='Quechuan',]
quechuan_subfamilies = quechuan$Classification
quechuan_subfamilies = strsplit(quechuan_subfamilies, ",")
quechuan_subfamilies = sapply(quechuan_subfamilies, "[", 3)
map.feature(languages=quechuan$Name, features=quechuan_subfamilies, latitude=quechuan$Latitude, longitude=quechuan$Longitude, zoom.control = TRUE)

#Map Japonic
japonic <- lang_data[lang_data$Dataset=='Japonic',]
japonic <- japonic[japonic$Name != 'Old Japanese',] #don't map Old Japanese
japonic_subfamilies = japonic$Classification
japonic_subfamilies = strsplit(japonic_subfamilies, ",")
japonic_subfamilies = sapply(japonic_subfamilies, tail, n=1)
map.feature(languages=japonic$Name, features=japonic_subfamilies, latitude=japonic$Latitude, longitude=japonic$Longitude)

#Map Uto-Aztecan
utoaztecan <- lang_data[lang_data$Dataset=='Uto-Aztecan',]
utoaztecan_subfamilies = utoaztecan$Classification
utoaztecan_subfamilies = strsplit(utoaztecan_subfamilies, ",")
utoaztecan_subfamilies = sapply(utoaztecan_subfamilies, tail, n=1)
map.feature(languages=utoaztecan$Name, features=utoaztecan_subfamilies, latitude=utoaztecan$Latitude, longitude=utoaztecan$Longitude)

#Map Hellenic
hellenic <- lang_data[lang_data$Dataset=='Hellenic',]
hellenic_subfamilies = hellenic$Classification
hellenic_subfamilies = strsplit(hellenic_subfamilies, ",")
hellenic_subfamilies = sapply(hellenic_subfamilies, tail, n=1)
map.feature(languages=hellenic$Name, features=hellenic_subfamilies, latitude=hellenic$Latitude, longitude=hellenic$Longitude)

#Map Bantu
bantu <- lang_data[lang_data$Dataset=='Bantu',]
bantu_subfamilies = bantu$Classification
bantu_subfamilies = strsplit(bantu_subfamilies, ",")
bantu_subfamilies = sapply(bantu_subfamilies, "[", 4)
map.feature(languages=bantu$Name, features=bantu_subfamilies, latitude=bantu$Latitude, longitude=bantu$Longitude)

#Map Vietic
vietic <- lang_data[lang_data$Dataset=='Vietic',]
vietic_subfamilies = vietic$Classification
vietic_subfamilies = strsplit(vietic_subfamilies, ",")
vietic_subfamilies = sapply(vietic_subfamilies, "[", 3)
map.feature(languages=vietic$Name, features=vietic_subfamilies, latitude=vietic$Latitude, longitude=vietic$Longitude, zoom.control = TRUE)

