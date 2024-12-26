#!/usr/bin/python3
# Format de chaque ligne : date\ttime\tstore name\titem description\tcost\tpayment method

import sys

for line in sys.stdin:
    data = line.strip().split("\t")
    if len(data) == 6:
        date, time, store, item, cost, payment = data
        try:
            cost = float(cost)  # Convertir le coût en nombre
            # Émettre le magasin comme clé et le coût de la vente comme valeur
            print("{0}\t{1}".format(store, cost))
        except ValueError:
            # Si le coût n'est pas un nombre valide, ignorer cette ligne
            continue
