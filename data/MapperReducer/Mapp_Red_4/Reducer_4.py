#!/usr/bin/python3

import sys

current_payment = None
total_cost = 0
transaction_count = 0

# Parcourir les paires clé-valeur en entrée
for line in sys.stdin:
    data = line.strip().split("\t")
    if len(data) != 3:
        continue
    
    payment, cost, count = data
    cost = float(cost)
    count = int(count)
    
    if payment == current_payment:
        total_cost += cost
        transaction_count += count
    else:
        if current_payment:
            # Calculer la moyenne des ventes pour le mode de paiement précédent
            average_sale = total_cost / transaction_count if transaction_count > 0 else 0
            print("{0}\t{1}".format(current_payment, average_sale))
        
        # Réinitialiser les variables pour le nouveau mode de paiement
        current_payment = payment
        total_cost = cost
        transaction_count = count

# Ne pas oublier de traiter le dernier mode de paiement
if current_payment:
    average_sale = total_cost / transaction_count if transaction_count > 0 else 0
    print("{0}\t{1}".format(current_payment, average_sale))
