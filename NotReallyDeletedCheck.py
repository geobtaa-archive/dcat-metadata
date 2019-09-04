# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 09:42:09 2019

@author: kerni016
"""
import csv
from urllib2 import urlopen

Deleted4Realz = {}
fields = ['URL', 'HTMLlength', 'ItemState']

with open('allDeletedItems_20190607.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        PageInfo = []
        response = urlopen(row[0])
        #print "This gets the code: ", response.code
        #print "The Headers are: ", response.info()
        html = response.read()
        PageInfo.append(row[0])
        PageInfo.append(len(html))
        if len(html) < 6000:
            PageInfo.append('Removed')
        else:
            PageInfo.append('Functioning')
        Deleted4Realz[row[0]] = PageInfo


report = ('GBLDeleted_TestReport_20190607.csv')
with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in Deleted4Realz:
            allvalues = Deleted4Realz[keys]
            csvout.writerow(allvalues)
