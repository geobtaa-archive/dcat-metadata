# -*- coding: utf-8 -*-
"""
Original created on Wed Mar 15 09:18:12 2017
Edited Dec 28 2018; January 8, 2019

@author: kerni016
"""
## To run this script you need a csv with six columns (portalName, URL, provenance, isPartOf, publisher, and spatialCoverage) with details about ESRI open data portals to be checked for new records.
## Need to define PreviousActionDate and ActionDate, directory path (containing newAll.csv and folders "Jsons" and "Reports"), and list of fields desired in the printed report
## The script currently prints two combined reports - one of new items and one with deleted items.  Commented code allows the option to also print reports for each data portal.

## Remaining Quesitons / Possible Improvements:
## what information should it print out to the report?
##deal with problems if there are more than 1000 json items in the dataset list data.json
## if new, check to see whether record similar to something that was there before?

import json
import csv
import urllib
import os
import os.path
from HTMLParser import HTMLParser
import decimal
import ssl

######################################

### Manual items to change!

## Set the date download of the older and newer jsons
ActionDate = '20200207'
PreviousActionDate = '20200103'

## names of the main directory containing folders named "Jsons" and "Reports"
directory = r'C:\\Users\\Emily\\Documents\\Grad School\\Map Library RA\\dcat-metadata\\'

##list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ["identifier", "code", "title", "alternativeTitle", "description", "genre", "subject", "format", "type", "geometryType", "dateIssued", "temporalCoverage", "Date", "spatialCoverage", "spatial", "provenance", "publisher",  "creator", "landingPage", "downloadURL", "webService", "metadataURL", "serverType", "keywords"]

##list of fields to use for the deletedItems report
delFieldsReport = ['identifier', 'landingPage', 'portalName']

##list of fields to use for the portal status report
statusFieldsReport = ['portalName', 'total', 'new_items', 'deleted_items']
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


### function that strips off html tags and deals with unicode encoding.  Only works on strings, not items within lists or dictionaries.
def cleanData (value):
    fieldvalue = strip_tags(value)
    fieldvalue = fieldvalue.encode('ascii', 'replace')
    return fieldvalue

### function that checks if there are items added to a dictionary (ie. new or deleted items). If there are, prints metadata elements from the dictionary to a csv file with as specified fields list as the header row
def printReport (report, dictionary, fields):
    with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)

### function that creates a dictionary with the position of a record in the data portal DCAT metadata json as the key and the identifier as the value
def getIdentifiers (data):
    json_ids = {}
    for x in range(len(data["dataset"])):
        json_ids[x] = data["dataset"][x]["identifier"]
    return json_ids


###function that returns a dictionary of selected metadata elements(with html tags and utf-8 characters removed) into a dictionary of new items (newItemDict) for each new item in a data portal. This includes blank fields '' for columns that will be filled in manually later. Includes an option to print a csv report of new items for each data portal
def metadataNewItems(newdata, newitem_ids):
    newItemDict = {}
    for y, v in newitem_ids.iteritems():
        identifier = v
        metadata = []
        metadata.append(identifier.rsplit('/', 1)[-1])
        metadata.append(portalName)
        try:
             metadata.append(cleanData(newdata["dataset"][y]['title']))
        except:
             metadata.append(newdata["dataset"][y]['title'])

        altTitle = ""
        metadata.append(altTitle)
        metadata.append(cleanData(newdata["dataset"][y]['description']))


        ### Set default blank values for genre, format, type, and downloadURL
        format_types = []
        genre = ""
        formatElement = ""
        typeElement = ""
        downloadURL =  ""
        geometryType = ""
        webService = ""

        distribution = newdata["dataset"][y]["distribution"]
        for dictionary in distribution:
            try:
                ### If one of the distributions is a shapefile, change genre/format and get the downloadURL
                format_types.append(dictionary["title"])
                if dictionary["title"] == "Shapefile":
                    genre = "Geospatial data"
                    formatElement = "Shapefile"
                    if downloadURL in dictionary:
                         downloadURL = dictionary["downloadURL"]
                    else:
                         downloadURL = dictionary["accessURL"]

                    geometryType = "Vector"

                ### If the Rest API is based on an ImageServer, change genre, type, and format to relate to imagery
                if dictionary["title"] == "Esri Rest API":
                    #imageCheck = dictionary['accessURL'].rsplit('/', 1)[-1]
                    webService = dictionary['accessURL']

                    if dictionary['accessURL'].rsplit('/', 1)[-1] == 'ImageServer':
                        genre = "Aerial imagery"
                        formatElement = 'Imagery'
                        typeElement = 'Image|Service'
                        #### Change this to Raster or Image?
                        geometryType = ""

            ### If the distribution section of the metadata is not structured in a typical way
            except:
                ### Set default error values for genre, format, type, and downloadURL
                genre = "error"
                formatElement = "error"
                typeElement = "error"
                downloadURL =  "error"

                try:
                    for dictionary in distribution:
                        ### If one of the distributions is a pdf, change genre and format
                        if ".pdf" in dictionary['accessURL']:
                            genre = 'Flagged'
                            formatElement = 'PDF'
                            typeElement = ""
                            downloadURL =  ""

                        ### If one of the distributions is a web map, change genre and format
                        if "viewer.html?webmap" in dictionary['accessURL']:
                            genre = 'Flagged'
                            formatElement = 'Web map'
                            typeElement = ""
                            downloadURL =  ""
                except:
                    continue

        ###If the item has both a Shapefile and Esri Rest API format, change type
        if "Esri Rest API" in format_types:
            if "Shapefile" in format_types:
                typeElement = "Dataset|Service"
        ### If the distribution section is well structured but doesn't include either a shapefile or imagery, add a list of format types and set genre to 'flagged
        if formatElement == "":
            genre = 'Flagged'
            formatElement = '|'.join(format_types)

        ### Checks for patterns in spatial coordinates that frequently indicate an error and, if found, changes the genre to "Suspicious coordinates"

        try:
            bbox = []
            spatial = cleanData(newdata["dataset"][y]['spatial'])
            typeDmal = decimal.Decimal
            fix4 = typeDmal("0.0001")
            for coord in spatial.split(","):
                coordFix = typeDmal(coord).quantize(fix4)
                bbox.append(str(coordFix))
            count = 0
            for coord in bbox:
                if coord == '0.0000':
                    count += 1
            if count >= 2:
                genre = 'Suspicious coordinates'
        except:
            spatial = ""

        metadata.append(genre)
        subject = ""
        metadata.append(subject)
        metadata.append(formatElement)
        metadata.append(typeElement)
        metadata.append(geometryType)

        metadata.append(cleanData(newdata["dataset"][y]['issued']))
        temporalCoverage = ""
        metadata.append (temporalCoverage)
        dateElement = ""
        metadata.append(dateElement)
        metadata.append(spatialCoverage)
        metadata.append(spatial)

        metadata.append(provenance)
#         metadata.append(isPartOf)
        metadata.append(publisher)
        creator = newdata["dataset"][y]["publisher"]
        for pub in creator.values():
             creator = pub.encode('ascii', 'replace')

#         creator = creator['source'].encode('ascii', 'replace')
        metadata.append(creator)

        metadata.append(cleanData(newdata["dataset"][y]['landingPage']))
        metadata.append(downloadURL)
        metadata.append(webService)
#         metadata.append(cleanData(newdata["dataset"][y]['webService']))
        metadataLink = ""
        metadata.append(metadataLink)

#         webService = cleanData(newdata["dataset"][y]['webService'])

        serviceType = ""
        serviceTypeList = ["FeatureServer", "MapServer", "ImageServer"]
        for server in serviceTypeList:
            try:
                if server in webService:
                    serviceType = server
            except:
                print(identifier)

        metadata.append(serviceType)

        keywords = newdata["dataset"][y]["keyword"]
        unicode_keyword = []
        for item in keywords:
            item = item.encode('ascii', 'replace')
            unicode_keyword.append(item)
            keyword_list = '|'.join(unicode_keyword)
        metadata.append(keyword_list)

        newItemDict[identifier] = metadata
    ###Uncomment to print reports for individual portals
#    if len(newItemDict) > 0:
#        reportNew = directory + "\Reports\%s_%s_new_itemsReport.csv" % (portalName, ActionDate)
#        printReport(reportNew, newItemDict, fieldnames)
#        print "new item report complete for %s!" % (portalName)
    return newItemDict


### Sets up lists to hold metadata information from each portal to be printed to a report
All_New_Items = []
All_Deleted_Items = []
Status_Report = {}

### Opens a list of portals and urls ending in /data.json from input CSV using column headers 'portalName' and 'URL'
with open(directory + 'arcPortals.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ### Read in values from the portals list to be used within the script or as part of the metadata report
        portalName = row['portalName']
        url = row['URL']
        provenance = row['provenance']
#         isPartOf = row['isPartOf']
        publisher = row['publisher']
        spatialCoverage = row['spatialCoverage']
        print portalName, url

        ## for each open data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates
        oldjson = directory + '/Jsons/%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '/Jsons/%s_%s.json' % (portalName, ActionDate)


        ## Opens the url for the ESRI open data portal json and loads it into the script
        ## Could also check whether a new json already exists with  os.path.isfile(newjson)...
        try:
            response = urllib.urlopen(url)
            newdata = json.load(response)
        except ssl.CertificateError as e:
            print e
            pass

        ### Saves a copy of the json to be used for the next round of comparison/reporting
        with open(newjson, 'w') as outfile:
            json.dump(newdata, outfile)

            ### Prints a warning if there are more than 1000 resources in the data portal
            if len(newdata["dataset"]) == 999:
                print "Warning! More than 1000 data resources in %s!" % (portalName)

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
            ###Uncomment to print reports for individual portals
#            if len(deletedItemDict) > 0:
#                reportDelete = directory + "\Reports\%s_%s_deleted_itemsReport.csv" % (portalName, ActionDate)
#                printReport(reportDelete, deletedItemDict, delFieldsReport)
#                print "deleted items report complete for %s!" % (portalName)

            ### collects information for the status report about the number of deleted items
            status_metadata.append(len(deletedItemDict))
            Status_Report [portalName] = status_metadata

        ### if there is no older json for comparions....
        else:
            print "There is no comparison json for %s" % (portalName)
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

### prints two csv spreadsheets with all items that are new or deleted since the last time the data portals were harvested
report = directory + "allNewItems_%s.csv" %  (ActionDate)
with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fieldnames)
        for portal in All_New_Items:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)

report = directory + "allDeletedItems_%s.csv" %  (ActionDate)
with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(delFieldsReport)
        for portal in All_Deleted_Items:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)

reportStatus = directory + "Reports/portal_status_report_%s.csv" % (ActionDate)
printReport (reportStatus, Status_Report, statusFieldsReport)
