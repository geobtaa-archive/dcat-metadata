# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 09:18:12 2017
Edited Dec 27 2018

@author: kerni016
"""
## To run this script you need a csv with six columns (portalName, URL, provenance, isPartOf, publisher, and spatialCoverage) with details about ESRI open data portals to be checked for new records.
## Need to define PreviousActionDate and ActionDate, directory path (containing PortalList.csv and folders "Jsons" and "Reports"), and list of fields desired in the printed report

## Remaining Quesitons / Possible Improvements:                                                                    
## what information should it print out to the report? Separate reports for each portal or should it lump them into one?
##deal with problems if there are more than 1000 json items in the dataset list data.json
## if new, check to see whether record similar to something that was there before?

import json
import csv
import urllib
import os.path
from HTMLParser import HTMLParser
from glob import glob

######################################

### Manual items to change!

### Set the date download of the older and newer jsons
ActionDate = 'YYYYMMDD'
PreviousActionDate = 'YYYYMMDD'

### names of the main directory containing folders named "Jsons" and "Reports"
directory = 'C:\BTAA\Maintenance'

##list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ["identifier", "code", "title", "alternativeTitle", "description", "genre", "subject", "format", "type", "geometryType", "dateIssued", "temporalCoverage", "Date", "spatialCoverage", "spatial", "provenance", "isPartOf", "publisher",  "creator", "landingPage", "downloadURL", "webService", "metadataURL", "serverType", "keywords"]

##list of fields to use for the deletedItems report
delFieldsReport = ['identifier', 'landingPage', 'portalName']
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


### strips off html tags and deals with unicode encoding.  Only works on strings, not items within lists or dictionaries.
def cleanData (value):
    fieldvalue = strip_tags(value)
    fieldvalue = fieldvalue.encode('ascii', 'replace')
    return fieldvalue

### function that checks if there are items added to a dictionary (ie. new, modified, or deleted items). If there are, prints results to a csv file with metadata elements as field names 
def printReport (report_type, dictionary, fields):
    report = directory + "\Reports\%s_%s_%sReport.csv" % (portalName, ActionDate, report_type) 
    with open(report, 'wb') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)    
    print "%s report complete for %s!" % (report_type, portalName)


### Opens a list of portals and urls ending in data/json from input CSV using column headers 'portalName' and 'URL'      
with open(directory + '\\newAll.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ### Read in values from the portals list to be used within the script or as part of the metadata report
        portalName = row['portalName']
        url = row['URL']
        provenance = row['provenance']
        isPartOf = row['isPartOf']
        publisher = row['publisher']
        spatialCoverage = row['spatialCoverage']
        print portalName, url

        ## for each open data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates
        oldjson = directory + '\Jsons\%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '\Jsons\%s_%s.json' % (portalName, ActionDate)
        
        
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
        deletedItemDict = {}
        
        for y in range(len(newdata["dataset"])):
            identifier = newdata["dataset"][y]["identifier"]
            ### Makes a dictionary of identifiers in the newer json to be used to look for deleted items below 
            new_ids[y] = identifier  
            if identifier not in original_ids.values():
                
                #### For each identifier that is present in the newer json but not the older json, appends to metadata elements gathered from the newer json or the input spreadsheet  
                metadata = []
                metadata.append(identifier.rsplit('/', 1)[-1])
                metadata.append(portalName)
                metadata.append(cleanData(newdata["dataset"][y]['title']))
                altTitle = ""
                metadata.append(altTitle)
                metadata.append(cleanData(newdata["dataset"][y]['description']))                                
                
                
                ### Sets default blank values for genre, format, type, and downloadURL
                format_types = []
                genre = ""
                formatElement = ""
                typeElement = ""
                downloadURL =  ""
                geometryType = ""
                                
                distribution = newdata["dataset"][y]["distribution"]
                for dictionary in distribution:
                    try:
                        ### If one of the distributions is a shapefile, changes genre/format and get the downloadURL
                        format_types.append(dictionary["title"])
                        if dictionary["title"] == "Shapefile":
                            genre = "Geospatial data"
                            formatElement = "Shapefile"
                            downloadURL = dictionary["downloadURL"]
                            geometryType = "Vector"
                            
                        ### If the Rest API is based on an ImageServer, changes genre, type, and format to relate to imagery
                        if dictionary["title"] == "Esri Rest API":
                            #imageCheck = dictionary['accessURL'].rsplit('/', 1)[-1]
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
                        
                        for dictionary in distribution:
                            ### If one of the distributions is a pdf, change genre and format  
                            if ".pdf" in dictionary['accessURL']:
                                genre = 'Nonspatial'
                                formatElement = 'PDF'
                                typeElement = ""
                                downloadURL =  ""
                                
                            ### If one of the distributions is a web map, change genre and format 
                            if "viewer.html?webmap" in dictionary['accessURL']:
                                genre = 'Nonspatial'
                                formatElement = 'Web map'
                                typeElement = ""
                                downloadURL =  ""
                                                         
                ###If the item has both a Shapefile and Esri Rest API format, change type                               
                if "Esri Rest API" in format_types:
                    if "Shapefile" in format_types:
                        typeElement = "Dataset|Service"
                
                ### If the distribution section is well structured but doesn't include either a shapefile or imagery, add a list of format types and set genre to 'nonspatial'  
                if formatElement == "":
                    genre = 'Nonspatial'
                    formatElement = '|'.join(format_types)
                    
                
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
                metadata.append(cleanData(newdata["dataset"][y]['spatial']))
                            
                metadata.append(provenance)
                metadata.append(isPartOf)
                metadata.append(publisher)
                creator = newdata["dataset"][y]["publisher"]
                creator = creator['name'].encode('ascii', 'replace')
                metadata.append(creator)
                
                metadata.append(cleanData(newdata["dataset"][y]['landingPage']))
                metadata.append(downloadURL)
                metadata.append(cleanData(newdata["dataset"][y]['webService'])) 
                metadataLink = ""
                metadata.append(metadataLink)
                webService = cleanData(newdata["dataset"][y]['webService'])
                
                serviceType = "" 
                serviceTypeList = ["FeatureServer", "MapServer", "ImageServer"]
                for server in serviceTypeList:
                    if server in webService:
                        serviceType = server                    
                metadata.append(serviceType)
                
                keywords = newdata["dataset"][y]["keyword"]
                unicode_keyword = []
                for item in keywords:
                    item = item.encode('ascii', 'replace')
                    unicode_keyword.append(item)
                    keyword_list = '|'.join(unicode_keyword)
                metadata.append(keyword_list)
                
                ### add Service Type tag
                newItemDict[identifier] = metadata
        
        
        ### Compares identifiers in the older json to the list of identifiers from the newer json. If the record no longer exists, adds selected fields (with html tags and utf-8 characters removed) into a dictionary of deleted items (deletedItemDict)
        for z in range(len(data["dataset"])):
            identifier = data["dataset"][z]["identifier"]
            if identifier not in new_ids.values():
                del_metadata = []
                del_metadata.append(identifier.rsplit('/', 1)[-1])
                del_metadata.append(identifier)
                del_metadata.append(portalName)
                deletedItemDict[identifier] = del_metadata
                               
      
        ### Checks if records have been added to each dictionary. If they have, prints results to a csv file with metadata elements as field names.  Prints a message about whether a report as been created.
        reportTypedict = {'new_items': newItemDict, 'deleted_items' : deletedItemDict}
        
        for key, value in reportTypedict.iteritems():
            if len(value) > 0:
                print str(len(value)) + " %s added to %s!" % (key, portalName)
                if key == 'deleted_items':
                    printReport(key,value,delFieldsReport)
                else:
                    printReport(key, value, fieldnames)
            else:
                print "%s has no %s" % (portalName, key)
                
#combines all deleted items CSV into one report
#csvFile = directory + "allDeletedItems_%s.csv" %  (ActionDate)
#with open(csvFile, 'a') as singleFile:
#    for csvFile in glob('*_deleted_itemsreport.csv'):
#        for line in open(csvFile, 'r'):
#            singleFile.write(line)
#
##combines all new items CSV into one report
#csvFile = directory + "allNewItems_%s.csv" %  (ActionDate)
#from glob import glob
#with open(csvFile, 'a') as singleFile:
#    for csvFile in glob('*_new_itemsreport.csv'):
#        for line in open(csvFile, 'r'):
#            singleFile.write(line)
#       
