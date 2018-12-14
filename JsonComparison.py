# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 09:18:12 2017

@author: kerni016
@author: majew030
"""
## To run this script you need a csv (ArcPortals.csv) with two columns (portalName and URL) with the names of ESRI open data portals to be checked for new and modified records.
## Need to define PreviousActionDate and ActionDate, directory path (containing ArcPortals.csv and folders "Jsons" and "Reports"), and list of fields desired in the printed report



import json
import csv
import urllib
import os.path
from HTMLParser import HTMLParser
from glob import glob

######################################

### Manual items to change!

## Set the date download of the older and newer jsons
ActionDate = '20181207'
PreviousActionDate = '20181102'


## names of the main directory containing folders named "Jsons" and "Reports"
directory = r'/Users/majew030/GitHUB/dcat-metadata/'

##list of metadata fields from the DCAT json schema for open data portals desired in the final report
fields = ["identifier", "title", "description", "issued", "modified", "landingPage", "webService", "spatial"]

##list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ["identifier", "title", "description", "issued", "modified", "landingPage", "webService", "spatial","portalName", "provenance", "isPartOf", "publisher", "spatialCoverage"]

##list of metadata fields to use for finding deleted items
delFields = ["identifier"]

##list of fields to use for the deletedItems report
delFieldsReport = ['identifier','portalName']
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
    report = directory + "%s_%s_%sreport.csv" % (portalName, ActionDate, report_type)
    with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)


### Opens a list of portals and urls ending in data/json from PortalList.csv with column headers 'portalName' and 'URL'
with open(directory + 'newAll.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        portalName = row['portalName']
        url = row['URL']
        provenance = row['provenance']
        isPartOf = row['isPartOf']
        publisher = row['publisher']
        spatialCoverage = row['spatialCoverage']
        print portalName, url

        ## for each open data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates
        oldjson = directory + 'jsons/%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + 'jsons/%s_%s.json' % (portalName, ActionDate)


        ## Opens the url for the ESRI open data portal json and loads it into the script
        ## Could also check whether a new json already exists with  os.path.isfile(newjson)...
        response = urllib.urlopen(url)
        newdata = json.load(response)

        ### Saves a copy of the json to be used for the next round of comparison/reporting
        with open(newjson, 'w') as outfile:
            json.dump(newdata, outfile)

        #Opens older copy of data/json downloaded from the specified Esri Open Data Portal.  If this file does not exist, prints an error message and skips to the next portal on the list
        if os.path.exists(oldjson):
            with open(oldjson) as data_file:
                data = json.load(data_file)

        else:
            print "There is no comparison json for %s" % (portalName)
            continue

        ### Makes a list of dataset identifiers in the older json
        original_ids = {}
        for x in range(len(data["dataset"])):
            original_ids[x] = data["dataset"][x]["identifier"]

        ### Compares identifiers in the newer json to the list of identifiers from the older json.  If new record, adds selected fields (with html tags and utf-8 characters removed) into a dictionary of new items (newItemDict)
        new_ids = {}
        newItemDict = {}
        modifiedItemDict = {}
        deletedItemDict = {}


        for y in range(len(newdata["dataset"])):
            identifier = newdata["dataset"][y]["identifier"]
            ### Makes a dictionary of identifiers in the newer json to be used to look for deleted items below
            new_ids[y] = identifier
            if identifier not in original_ids.values():
                publisher = newdata["dataset"][y]["publisher"]
                keyword = newdata["dataset"][y]["keyword"]
              ###  keyword = keyword.encode('ascii', 'replace')
                name = publisher["name"]
                metadata = []
                metadata.append(name)
                metadata.append(keyword)
                for field in fields:
                    fieldvalue = strip_tags(newdata["dataset"][y][field])
                    fieldvalue = fieldvalue.encode('ascii', 'replace')
                    metadata.append(fieldvalue)
                metadata.append(portalName)
                metadata.append(provenance)
                metadata.append(isPartOf)
                metadata.append(publisher)
                metadata.append(spatialCoverage)
                newItemDict[identifier] = metadata

        ### Compares identifiers in the older json to the list of identifiers from the newer json. If the record no longer exists, adds selected fields (with html tags and utf-8 characters removed) into a dictionary of deleted items (deletedItemDict)
        for z in range(len(data["dataset"])):
            identifier = data["dataset"][z]["identifier"]
            if identifier not in new_ids.values():
                del_metadata = []
                for field in fields:
                    fieldvalue = strip_tags(data["dataset"][z][field])
                    fieldvalue = fieldvalue.encode('ascii', 'replace')
                    del_metadata.append(fieldvalue)
                deletedItemDict[identifier] = del_metadata


        ### Checks if records have been added to each dictionary. If they have, prints results to a csv file with metadata elements as field names.  Prints a message about whether a report as been created.
        reportTypedict = {'new_items': newItemDict, 'deleted_items' : deletedItemDict}

        for key, value in reportTypedict.iteritems():
            if len(value) > 0:
                print str(len(value)) + " %s added to %s!" % (key, portalName)
                if key == 'deleted_items':
                    printReport(key,value,delFieldsReport)
                else:
                    printReport(key, value, fields)
            else:
                print "%s has no %s" % (portalName, key)

#combines all deleted items CSV into one report
csvFile = directory + "allDeletedItems_%s.csv" %  (ActionDate)
with open(csvFile, 'a') as singleFile:
    for csvFile in glob('*_deleted_itemsreport.csv'):
        for line in open(csvFile, 'r'):
            singleFile.write(line)

#combines all new items CSV into one report
csvFile = directory + "allNewItems_%s.csv" %  (ActionDate)
from glob import glob
with open(csvFile, 'a') as singleFile:
    for csvFile in glob('*_new_itemsreport.csv'):
        for line in open(csvFile, 'r'):
            singleFile.write(line)
