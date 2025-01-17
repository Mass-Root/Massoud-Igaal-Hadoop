#!/usr/bin/python3
# Format of each line is:
# date\ttime\tstore name\titem description\tcost\tmethod of payment
#
# We want elements 3 (item description) and emit a count of 1 for each transaction

import sys

for line in sys.stdin:
    data = line.strip().split("\t")
    if len(data) == 6:
        date, time, store, item, cost, payment = data
        # Emit the item as the key and '1' as the value
        print("{0}\t{1}".format(item, 1))
