#!/usr/bin/python3
# Format of each line is:
# item_name\ttransaction_count
#
# We want to sum the transactions for each item

import sys

transactionCount = 0
oldKey = None

# Loop around the data
# It will be in the format key\tval
# Where key is the item name, val is the count (1 for each sale)

for line in sys.stdin:
    data_mapped = line.strip().split("\t")
    
    if len(data_mapped) != 2:
        # Something has gone wrong, skip this line
        continue
    
    thisKey, thisSale = data_mapped
    thisSale = int(thisSale)  # The sale count is always 1, but we convert it to an integer for summing
    
    if oldKey and oldKey != thisKey:
        # If the item changes, print the count of transactions for the old item
        print(oldKey, "\t", transactionCount)
        oldKey = thisKey
        transactionCount = 0
    
    oldKey = thisKey
    transactionCount += thisSale

# Don't forget to output the last item
if oldKey != None:
    print(oldKey, "\t", transactionCount)
