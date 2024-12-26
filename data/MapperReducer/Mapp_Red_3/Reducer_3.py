#!/usr/bin/python3

import sys

max_sales = 0
max_store = None
current_store = None
total_sales = 0

# Parcourir les paires clé-valeur en entrée
for line in sys.stdin:
    data = line.strip().split("\t")
    if len(data) != 2:
        continue
    
    store, sales = data
    sales = float(sales)
    
    if store == current_store:
        total_sales += sales
    else:
        if current_store:
            # Vérifier si le magasin précédent a la vente la plus élevée
            if total_sales > max_sales:
                max_sales = total_sales
                max_store = current_store
        current_store = store
        total_sales = sales

# Ne pas oublier de vérifier le dernier magasin
if current_store and total_sales > max_sales:
    max_sales = total_sales
    max_store = current_store

# Afficher le magasin avec la vente maximale
if max_store:
    print("{0}\t{1}".format(max_store, max_sales))
