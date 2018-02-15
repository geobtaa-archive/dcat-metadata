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

######################################

### Manual items to change!

ActionDate = '20180212'

## names of the main directory containing folders named "Jsons" and "Reports"
directory = r'/Users/majew030/GitHUB/dcat-metadata'

##list of metadata fields from the DCAT json schema for open data portals desired in the final report
fields = ["identifier", "title", "description", "issued", "modified", "landingPage", "webService", "spatial"]
##fields = ["identifier", "title", "description", "issued", "modified", "landingPage"]

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
    report = directory + "/reports/%s_%s.csv" % (portalName, ActionDate)
    with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            allvalues.append(keys)
            csvout.writerow(allvalues)
    print "report complete for %s!" % (portalName)


### Opens a list of portals and urls ending in data/json from PortalList.csv with column headers 'portalName' and 'URL'
with open(directory + '/MnPortals.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        portalName = row['portalName']
        url = row['URL']
        print portalName, url

        ## for each open data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates
        ## oldjson = directory + '\Jsons\%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '/jsons/%s_%s.json' % (portalName, ActionDate)


        ## Opens the url for the ESRI open data portal json and loads it into the script
        ## Could also check whether a new json already exists with  os.path.isfile(newjson)...
        response = urllib.urlopen(url)
        newdata = json.load(response)



        ### Saves a copy of the json to be used for the next round of comparison/reporting
        with open(newjson, 'w') as outfile:
            json.dump(newdata, outfile)


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

        ###temporary print reporting check
        print str(len(newItemDict)) + " items harvested from %s!" % (portalName)

        ### Checks if records have been added to each dictionary. If they have, prints results to a csv file with metadata elements as field names.  Prints a message about whether a report as been created.
        reportTypedict = {'new_items': newItemDict}
##
        for key, value in reportTypedict.iteritems():
            if len(value) > 0:
                print str(len(value)) + " %s harvested from %s!" % (key, portalName)
                printReport(key, value, fields)
            else:
                print "%s has no %s" % (portalName, key)
