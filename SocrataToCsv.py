# -*- coding: utf-8 -*-
"""
Created on Mon Apr 03 14:38:31 2017

@author: kerni016
"""

#'/SocrataPortalList.csv'  Socrata

#do we have identifiers from open data portals anywhere in our geoportal metadata? could I limit the modified items search to things that we already have in the portal?
#socrata update:  if distribution   within distribution dictionary key value downloadURL string method=export&format=Shapefile or method=export&format=KMZ or method=export&format=KML or others??

#could make a list of spatial types of method=export, if any of these strings match the method??

import json
import csv
import urllib
import os.path
from HTMLParser import HTMLParser


######################################

### Manual items to change!

## Set the date download of the older and newer jsons
actionDate = 'yyyymmdd'

## names of the main directory containing folders named "jsons" and "reports"
directory = r' '

##list of metadata fields desired for the final report
fields = ["identifier", "title", "description", "issued", "landingPage"]

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
    report = directory + "/Reports/%s_%s.csv" % (portalName, actionDate)
    with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            allvalues.append(keys)
            csvout.writerow(allvalues)
    print "report complete for %s!" % (portalName)


### Opens a list of portals and urls ending in data/json. Needs to be a csv with column headers 'portalName' and 'URL'
with open(directory + '/temp.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        portalName = row['portalName']
        url = row['URL']
        print portalName, url


        ## for each socrata data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates

        newjson = directory + '/Socrata/%s_%s.json' % (portalName, actionDate)


        ## Opens the url for an open data portal json and loads it into the script
        ## Could also check whether a new json already exists with  os.path.isfile(newjson)?
        response = urllib.urlopen(url)
        newdata = json.load(response)

        ### Saves a copy of the json to be used for the next round of comparison/reporting
        with open(newjson, 'w') as outfile:
            json.dump(newdata, outfile)

        ### Makes a dictionary of identifiers in the older json that have a "Shapefile" export option
        ###original_ids = {}
        ###for x in range(len(data["dataset"])):
        ### for method in range(len(data["dataset"][x]['distribution'])):
        ###        if "method=export&format=Shapefile" in data["dataset"][x]['distribution'][method]['downloadURL']:
           ###         original_ids[x] = data["dataset"][x]["identifier"]

        ### Compares spatial item identifiers in the newer json to the list of identifiers from the older json.  If new record, adds selected fields (with html tags and utf-8 characters removed) into a dictionary of new items (newItemDict)
        new_ids = {}
        newItemDict = {}
        for y in range(len(newdata["dataset"])):
            for method in range(len(newdata["dataset"][y]['distribution'])):
                if "method=export&format=Shapefile" in newdata["dataset"][y]['distribution'][method]['downloadURL']:
                    identifier = newdata["dataset"][y]["identifier"]
                    ### Makes a dictionary of identifiers in the newer json that have a "Shapefile" export option to be used to look for deleted items below
                    new_ids[y] = identifier
##                    if identifier not in original_ids.values():
                    metadata = []
                    for field in fields:
                        fieldvalue = strip_tags(newdata["dataset"][y][field])
                        fieldvalue = fieldvalue.encode('ascii', 'replace')
                        metadata.append(fieldvalue)
                    newItemDict[identifier] = metadata
##                ### If the spatial item identifier was in the new record, checks to see whether the modified date has changed. If yes, adds selected fields (with html tags and utf-8 characters removed) into a dictionary of modified items (modifiedItemDict)
##                    elif data["dataset"][original_ids.keys()[original_ids.values().index(identifier)]]["modified"] != newdata["dataset"][y]["modified"]:
##                            mod_metadata = []
##                            for field in fields:
##                                fieldvalue = strip_tags(newdata["dataset"][y][field])
##                                fieldvalue = fieldvalue.encode('ascii', 'replace')
##                                mod_metadata.append(fieldvalue)
                            ##could maybe add download for shapefile? if "method=export&format=Shapefile" in data["dataset"][x]['distribution'][method]['downloadURL']: mod_metadata.append(data["dataset"][x]['distribution'][method]['downloadURL'] will make creating csvs more challenging - two separate lists of fields one for iterating and one for creating reports)
##                            modifiedItemDict[identifier] = mod_metadata


##        ### Compares spatial item identifiers in the older json to the list of identifiers from the newer json. If the record no longer exists, adds selected fields (with html tags and utf-8 characters removed) into a dictionary of deleted items (deletedItemDict)
##        for z in range(len(data["dataset"])):
##            for method in range(len(data["dataset"][z]['distribution'])):
##                if "method=export&format=Shapefile" in data["dataset"][z]['distribution'][method]['downloadURL']:
##                    identifier = data["dataset"][z]["identifier"]
##                    if identifier not in new_ids.values():
##                        del_metadata = []
##                        for field in fields:
##                            fieldvalue = strip_tags(data["dataset"][z][field])
##                            fieldvalue = fieldvalue.encode('ascii', 'replace')
##                            del_metadata.append(fieldvalue)
##                        deletedItemDict[identifier] = del_metadata

                ###temporary print reporting check
        #        print str(len(newItemDict)) + " new items added to %s!" % (portalName)
        #        print str(len(modifiedItemDict)) + " modified items in %s!" % (portalName)
        #        print str(len(deletedItemDict)) + " items deleted from %s!" % (portalName)

        ### Checks if records have been added to each dictionary. If they have, prints results to a csv file with metadata elements as field names
        reportTypedict = {'new_items': newItemDict}

        for key, value in reportTypedict.iteritems():
            if len(value) > 0:
                print str(len(value)) + " %s added to %s!" % (key, portalName)
                printReport(key, value, fields)
            else:
                print "%s has no %s" % (portalName, key)
