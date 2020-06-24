#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -*- coding: utf-8 -*-
"""
Original created on Wed Mar 15 09:18:12 2017
Edited Dec 28 2018; January 8, 2019; Dec 26-31, 2019, Jan 22-29 2020
@author: kerni016
"""
## To run this script you need a csv with five columns (portalName, URL, provenance, publisher, and spatialCoverage) with details about ESRI open data portals to be checked for new records.
## Need to define PreviousActionDate and ActionDate, directory path (containing PortalList.csv and folder "DCATjsons"), and list of fields desired in the printed report
## The script currently prints two combined reports - one of new items and one with deleted items.  The script also prints a status report giving the total number of resources in the portal, as well as the numbers of added and deleted items.

import json
import csv

import urllib.request
import os
import os.path
from html.parser import HTMLParser
import decimal
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# In[2]:


### Manual items to change!

## Set the date download of the older and newer jsons
PreviousActionDate = '20200508'
ActionDate = '202000608'

##list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ["identifier", "code", "originalTitle", "title", "description", "subject", "keyword", "format", "type", "geometryType", "dateIssued", "temporalCoverage", "solrYear", "spatialCoverage", "spatial", "provenance", "publisher",  "creator", "landingPage", "downloadURL", "featureServer", "mapServer", "imageServer"]

##list of fields to use for the deletedItems report
delFieldsReport = ['identifier', 'landingPage', 'portalName']

##list of fields to use for the portal status report
statusFieldsReport = ['portalName', 'total', 'new_items', 'deleted_items']


# In[3]:


###Removes html tags from text and replaces non-ascii characters with "?"
###Code derived from Eloff on Stack Overflow : https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def cleanData (value):
    fieldvalue = strip_tags(value)
    fieldvalue = fieldvalue.encode('ascii', 'replace').decode('utf-8')
    return fieldvalue


# In[4]:


### function that prints metadata elements from a dictionary to a csv file with as specified fields list as the header row
def printReport (report, dictionary, fields):
    with open(report, 'w', newline='') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)

### function that creates a dictionary with the position of a record in the data portal DCAT metadata json as the key and the identifier as the value
def getIdentifiers (json):
    json_ids = {}
    for x in range(len(json["dataset"])):
        json_ids[x] = json["dataset"][x]["identifier"]
    return json_ids


# In[5]:


###function that returns a dictionary of selected metadata elements for each new item in a data portal. This includes blank fields '' for columns that will be filled in manually later. Input requires the current DCAT json of the a data portal and a dictionary with key (position in the DCAT json), value (landing page URL) of the items.
def metadataNewItems(newdata, newitem_ids):
    newItemDict = {}
    ### key = position of the dataset in the DCAT metadata json, value = landing page URLs
    for key, value in newitem_ids.items():
        ###each time through the loop, creates an empty list to hold metadata about each item
        metadata = []

        identifier = value
        metadata.append(identifier.rsplit('/', 1)[-1])
        metadata.append(portalName)
        try:
            metadata.append(cleanData(newdata["dataset"][key]['title']))
        except:
            metadata.append(newdata["dataset"][key]['title'])

        originalTitle = ""
        metadata.append(originalTitle)
        metadata.append(cleanData(newdata["dataset"][key]['description']))

        ### Set default blank values for format, type, and downloadURL
        format_types = []
        formatElement = ""
        typeElement = ""
        downloadURL =  ""
        geometryType = ""
        webService = ""

        distribution = newdata["dataset"][key]["distribution"]
        for dictionary in distribution:
            try:
                ### If one of the distributions is a shapefile, change format and get the downloadURL
                format_types.append(dictionary["title"])
                if dictionary["title"] == "Shapefile":
                    formatElement = "Shapefile"
                    if 'downloadURL' in dictionary.keys():
                        downloadURL = dictionary["downloadURL"]
                    else:
                        downloadURL = dictionary["accessURL"]

                    geometryType = "Vector"

                ### If the Rest API is based on an ImageServer, change type, and format to relate to imagery
                if dictionary["title"] == "Esri Rest API":
                    if 'accessURL' in dictionary.keys():
                        webService = dictionary['accessURL']

                        if webService.rsplit('/', 1)[-1] == 'ImageServer':
                            formatElement = 'Imagery'
                            typeElement = 'Image|Service'
                            #### Change this to Raster or Image?
                            geometryType = ""

                        ### If one of the distributions is a pdf, change format
                        elif ".pdf" in webService:
                            formatElement = 'PDF'
                            typeElement = ""
                            downloadURL =  ""

                        ### If one of the distributions is a web application, change format
                        elif "/apps/" in webService:
                            formatElement = 'Web application'
                            typeElement = ""
                            downloadURL =  ""
                    else:
                        formatElement = "error"
                        typeElement = ""
                        downloadURL =  ""

                if dictionary["title"] == "CSV":
                    formatElement = "CSV"
                    typeElement = ""
                    downloadURL =  ""

            ### If the distribution section of the metadata is not structured in a typical way
            except:
                ### Set default error values for format, type, and downloadURL
                formatElement = "error"
                typeElement = "error"
                downloadURL =  "error"

                continue


        ###If the item has both a Shapefile and Esri Rest API format, change type
        if "Esri Rest API" in format_types:
            if "Shapefile" in format_types:
                typeElement = "Dataset|Service"
        ### If the distribution section is well structured but doesn't include either a shapefile or imagery, add a list of format types present
        if formatElement == "":
            formatElement = '|'.join(format_types)

        ### Standardizes bounding box coordinates
        try:
            bbox = []
            spatial = cleanData(newdata["dataset"][key]['spatial'])
            typeDmal = decimal.Decimal
            fix4 = typeDmal("0.0001")
            for coord in spatial.split(","):
                coordFix = typeDmal(coord).quantize(fix4)
                bbox.append(str(coordFix))
        except:
            spatial = ""

        subject = ""
        metadata.append(subject)

        keywords = newdata["dataset"][key]["keyword"]
        keyword_list = '|'.join(keywords)
        metadata.append(keyword_list)

        metadata.append(formatElement)
        metadata.append(typeElement)
        metadata.append(geometryType)

        metadata.append(cleanData(newdata["dataset"][key]['issued']))
        temporalCoverage = ""
        metadata.append (temporalCoverage)
        dateElement = ""
        metadata.append(dateElement)
        metadata.append(spatialCoverage)
        metadata.append(spatial)

        metadata.append(provenance)
        metadata.append(publisher)

        creator = newdata["dataset"][key]["publisher"]
        for pub in creator.values():
            creator = pub.encode('ascii', 'replace').decode('utf-8')
        metadata.append(creator)

#         metadata.append(cleanData(newdata["dataset"][key]['landingPage']))
        metadata.append(downloadURL)

        featureServer = ""
        mapServer = ""
        imageServer = ""

        try:
            if "FeatureServer" in webService:
                featureServer = webService
            if "MapServer" in webService:
                mapServer = webService
            if "ImageServer" in webService:
                imageServer = webService
        except:
                print(identifier)

        metadata.append(featureServer)
        metadata.append(mapServer)
        metadata.append(imageServer)

        newItemDict[identifier] = metadata

    return newItemDict


# In[6]:


### Sets up lists to hold metadata information from each portal to be printed to a report
All_New_Items = []
All_Deleted_Items = []
Status_Report = {}

### Opens a list of portals and urls ending in /data.json from input CSV using column headers 'portalName', 'URL', "provenance", "publisher", and "spatialCoverage"
with open('arcportals.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ### Read in values from the portals list to be used within the script or as part of the metadata report
        portalName = row['portalName']
        url = row['URL']
        provenance = row['provenance']
        publisher = row['publisher']
        spatialCoverage = row['spatialCoverage']
        print (portalName, url)

        ## for each open data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates
        oldjson = 'Jsons/%s_%s.json' % (portalName, PreviousActionDate)
        newjson = 'Jsons/%s_%s.json' % (portalName, ActionDate)

#         try:
        response = urllib.request.urlopen(url, context=ctx)
        newdata = json.load(response)

#         except:
#             print ("Data portal URL does not exist: " + url)
#             break


        ### Saves a copy of the json to be used for the next round of comparison/reporting
        with open(newjson, 'w') as outfile:
            json.dump(newdata, outfile)

            ### collects information about number of resources (total, new, and old) in each portal
            status_metadata = []
            status_metadata.append(portalName)

        #Opens older copy of data/json downloaded from the specified Esri Open Data Portal.  If this file does not exist, treats every item in the portal as new
        if os.path.exists(oldjson):
            with open(oldjson) as data_file:
                older_data = json.load(data_file)

            ### Makes a list of dataset identifiers in the older json
            older_ids = getIdentifiers (older_data)

            ###compares identifiers in the older json harvest of the data portal with identifiers in the new json, creating dictionaries with 1) a complete list of new json identifiers and 2) a list of just the items that appear in the new json but not the older one
            newjson_ids = {}
            newitem_ids = {}

            for y in range(len(newdata["dataset"])):
                identifier = newdata["dataset"][y]["identifier"]
                newjson_ids[y] = identifier
                if identifier not in older_ids.values():
                    newitem_ids[y] = identifier


            ### creates a dictionary of metadata elements for each new data portal item. Includes an option to print a csv report of new items for each data portal
            ### Puts dictionary of identifiers (key), metadata elements (values) for each data portal into a list (to be used printing the combined report) [portal1{identifier:[metadataElement1, metadataElement2, ... ], portal2{identifier:[metadataElement1, metadataElement2, ... ], ...}
            All_New_Items.append(metadataNewItems(newdata, newitem_ids))

            ### collects information for the status report about the number of records currently in the portal and new items
            status_metadata.append(len(newjson_ids))
            status_metadata.append(len(newitem_ids))

            ### Compares identifiers in the older json to the list of identifiers from the newer json. If the record no longer exists, adds selected fields into a dictionary of deleted items (deletedItemDict)
            deletedItemDict = {}
            for z in range(len(older_data["dataset"])):
                identifier = older_data["dataset"][z]["identifier"]
                if identifier not in newjson_ids.values():
                    del_metadata = []
                    del_metadata.append(identifier.rsplit('/', 1)[-1])
                    del_metadata.append(identifier)
                    del_metadata.append(portalName)
                    deletedItemDict[identifier] = del_metadata

            ### Puts dictionary of identifiers (key), metadata elements (values) for each data portal into a list (to be used printing the combined report) [portal1{identifier:[metadataElement1, metadataElement2, ... ], portal2{identifier:[metadataElement1, metadataElement2, ... ], ...}
            All_Deleted_Items.append(deletedItemDict)

            ### collects information for the status report about the number of deleted items
            status_metadata.append(len(deletedItemDict))
            Status_Report [portalName] = status_metadata

        ### if there is no older json for comparions....
        else:
            print ("There is no comparison json for %s" % (portalName))
            ### Makes a list of dataset identifiers in the new json
            newjson_ids = getIdentifiers (newdata)

            ### creates a dictionary of metadata elements for each new item in a data portal (i.e. all items from the new json). Includes an option to print a csv report of new items for each data portal
            ### Puts dictionary of identifiers (key), metadata elements (values) for each data portal into a list (to be used printing the combined report)   [portal1{identifier:[metadataElement1, metadataElement2, ... ], portal2{identifier:[metadataElement1, metadataElement2, ... ], ...}
            All_New_Items.append(metadataNewItems(newdata, newjson_ids))

            ### collects information for the status report about the number of records currently in the portal, new items, and deleted items
            status_metadata.append(len(newjson_ids))
            status_metadata.append(len(newjson_ids))
            status_metadata.append('0')
            Status_Report [portalName] = status_metadata


# In[7]:


### prints two csv spreadsheets with all items that are new or deleted since the last time the data portals were harvested
report = "NewDCATitems_full_%s.csv" %  (ActionDate)
with open(report, 'w', newline='', encoding="utf-8") as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fieldnames)
        for portal in All_New_Items:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)

report = "DeletedDCATitems_full_%s.csv" %  (ActionDate)
with open(report, 'w', newline='', encoding="utf-8") as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(delFieldsReport)
        for portal in All_Deleted_Items:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)

### prints a status report about how many items have been added or deleted from each portal.
reportStatus = "portal_status_report_%s.csv" % (ActionDate)
printReport (reportStatus, Status_Report, statusFieldsReport)

