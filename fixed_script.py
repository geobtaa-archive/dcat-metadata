# -*- coding: utf-8 -*-
"""
Modified on July 14, 2017

@author: kerni016
@author2: majew030
"""

import json
import csv
import urllib
import os.path
from HTMLParser import HTMLParser
from collections import namedtuple


######################################

### Manual items to change!

ActionDate = '20171012'

## names of the main directory containing folders named "Jsons" and "Reports"
directory = r' '

##list of metadata fields from the DCAT json schema for open data portals desired in the final report

fields = ["identifier", "title", "description", "issued", "modified"]


#######################################


### function to strip html tags from strings
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

### function that checks if there are items added to a dictionary (ie. new, modified, or deleted items). If there are, prints results to a csv file with metadata elements as field names
def printReport (report_type, dictionary, fields):
    report = directory + "/reports/IowaGeodata2.csv"
    with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            allvalues.append(keys)
            csvout.writerow(allvalues)
    print "report complete"


with open('IowaGeodata.json') as data_file:
	newdata = json.load(data_file)

	new_ids = {}
	newItemDict = {}

	for y in range(len(newdata["dataset"])):
		identifier = newdata["dataset"][y]["identifier"]
		new_ids[y] = identifier
		metadata = []
		for field in fields:
			fieldvalue = strip_tags(newdata["dataset"][y][field])
			fieldvalue = fieldvalue.encode('ascii', 'replace')
			metadata.append(fieldvalue)
		newItemDict[identifier] = metadata


	### Checks if records have been added to each dictionary. If they have, prints results to a csv file with metadata elements as field names.  Prints a message about whether a report as been created.
	reportTypedict = {'new_items': newItemDict}
##
	for key, value in reportTypedict.iteritems():
		if len(value) > 0:
			print str(len(value)) + "  items harvested "
			printReport(key, value, fields)
		else:
			print "none"
