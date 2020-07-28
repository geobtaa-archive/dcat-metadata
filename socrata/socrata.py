# -*- coding: utf-8 -*-
"""
Original created on Wed Mar 15 09:18:12 2017
Edited Dec 28 2018; January 8, 2019
@author: kerni016

Updated July 28, 2020
Updated by Yijing Zhou @YijingZhou33
"""
## To run this script you need a csv with five columns (portalName, URL, provenance, publisher, and spatialCoverage) with details about ESRI open data portals to be checked for new records.
## Need to define PreviousActionDate and ActionDate, directory path (containing PortalList.csv, folder "jsons" and "reports"), and list of fields desired in the printed report
## The script currently prints two combined reports - one of new items and one with deleted items.  
## The script also prints a status report giving the total number of resources in the portal, as well as the numbers of added and deleted items. 
                                                                    
import json
import csv
import urllib
import urllib.request
import os
import os.path
from html.parser import HTMLParser
import decimal
import ssl
import re
import csv

######################################

### Manual items to change!

## set the date download of the older and newer jsons
ActionDate = '20200722'
PreviousActionDate = '20200414'

## names of the main directory containing folders named "jsons" and "reports"
## Windows:
directory = r'D:\Library RA\GitHub\dcat-metadata-master'
## MAC or Linux:
## directory = r'D:/Library RA/GitHub/dcat-metadata-master'

## csv file contaning portal list
portalFile = 'SocrataPortals.csv'

## list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ['Title', 'Alternative Title', 'Description', 'Language', 'Creator', 'Publisher', 'Genre',
              'Subject', 'Date Issued', 'Temporal Coverage', 'Date Range', 'Solr Year', 'Spatial Coverage',
              'Type', 'Geometry Type', 'Format', 'Information', 'Download', 
              'Identifier', 'Provenance', 'Code', 'Is Part Of', 'Status',
              'Accrual Method', 'Date Accessioned', 'Rights', 'Suppressed', 'Child']

## list of fields to use for the deletedItems report
delFieldsReport = ['identifier', 'landingPage', 'portalName']

## list of fields to use for the portal status report
statusFieldsReport = ['portalName', 'total', 'new_items', 'deleted_items']
#######################################


### function to removes html tags from text
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

def cleanData(value):
    fieldvalue = strip_tags(value)
    return fieldvalue

### function that prints metadata elements from the dictionary to a csv file (portal_status_report) 
### with as specified fields list as the header row. 
def printReport(report, dictionary, fields):
    with open(report, 'w', newline='', encoding='utf-8') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)  

### Similar to the function above but generates two csv files (allNewItems & allDeletedItems)            
def printItemReport(report, fields, dictionary):
    with open(report, 'w', newline='', encoding='utf-8') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for portal in dictionary:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)   

### function that creates a dictionary with the position of a record in the data portal DCAT metadata json as the key 
### and the identifier as the value. 
def getIdentifiers(data):
    json_ids = {}
    for x in range(len(data["dataset"])):
        json_ids[x] = data["dataset"][x]["identifier"]
    return json_ids


### function that returns a dictionary of selected metadata elements into a dictionary of new items (newItemDict) for each new item in a data portal. 
### This includes blank fields '' for columns that will be filled in manually later. 
def metadataNewItems(newdata, newitem_ids):
    newItemDict = {}
    ### y = position of the dataset in the DCAT metadata json, v = landing page URLs 
    for y, v in newitem_ids.items():
        identifier = v 
        metadata = []
                
        title = ""
        alternativeTitle = ""
        try:
            alternativeTitle = cleanData(newdata["dataset"][y]['title'])
        except:
            alternativeTitle = newdata["dataset"][y]['title']

        description = cleanData(newdata["dataset"][y]['description'])
        ### Remove newline, whitespace, defalut description and replace singe quote, double quote 
        if description == "{{default.description}}":
            description = description.replace("{{default.description}}", "")
        else:
            description = re.sub(r'[\n]+|[\r\n]+',' ', description, flags=re.S)
            description = re.sub(r'\s{2,}' , ' ', description)
            description = description.replace(u"\u2019", "'").replace(u"\u201c", "\"").replace(u"\u201d", "\"").replace(u"\u00a0", "").replace(u"\u00b7", "").replace(u"\u2022", "").replace(u"\u2013","-").replace(u"\u200b", "")
              
        language = "English"        
        
        creator = newdata["dataset"][y]["publisher"]["name"]

        genre = "Geospatial data"
        formatElement = "Shapefile"
        typeElement = "Dataset|Service"
        downloadURL = ""
        geometryType = "Vector"
                       
        subject = ""
                
        dateIssued = cleanData(newdata["dataset"][y]['issued'])
        temporalCoverage = ""
        dateRange = ""
        solrYear = ""
        
        information = cleanData(newdata["dataset"][y]['landingPage'])
                                
        identifier = identifier.rsplit('/', 1)[-1]   
        isPartOf = portalName
        
        status = "Active"
        accuralMethod = "ArcGIS Hub"
        dateAccessioned = ""
                  
        rights = "Public"               
        suppressed = "FALSE"
        child = "FALSE"
               
        metadataList = [title, alternativeTitle, description, language, creator, publisher,
                    genre, subject, dateIssued, temporalCoverage,
                    dateRange, solrYear, spatialCoverage, typeElement, geometryType,
                    formatElement, information, downloadURL,
                    identifier, provenance, portalName, isPartOf, status,
                    accuralMethod, dateAccessioned, rights, suppressed, child]
  
        for i in range(len(metadataList)):
            metadata.append(metadataList[i])      
        
        newItemDict[identifier] = metadata   
         
    return newItemDict


All_New_Items = []
All_Deleted_Items = []
Status_Report = {}


### Opens a list of portals and urls ending in /data.json from input CSV 
### using column headers 'portalName', 'URL', 'provenance', 'SpatialCoverage'
with open(portalFile, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ### Read in values from the portals list to be used within the script or as part of the metadata report
        portalName = row['portalName']
        url = row['URL']
        provenance = row['provenance']
        publisher = row['publisher']
        spatialCoverage = row['spatialCoverage']
        print(portalName, url)

        ## for each open data portal in the csv list...
        ## renames file paths based on portalName and manually provided dates
        oldjson = directory + '\\jsons\\%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '\\jsons\\%s_%s.json' % (portalName, ActionDate)
        
        try:
            response =urllib.request.urlopen(url)
            newdata = json.load(response)
        except ssl.CertificateError as e:
            print("Data portal URL does not exist: " + url)
            break
        
        ### Saves a copy of the json to be used for the next round of comparison/reporting
        with open(newjson, 'w', encoding='utf-8') as outfile:  
            json.dump(newdata, outfile)
            
            ### collects information about number of resources (total, new, and old) in each portal
            status_metadata = []
            status_metadata.append(portalName)
                          
        ### Opens older copy of data/json downloaded from the specified Esri Open Data Portal.  
        ### If this file does not exist, treats every item in the portal as new.
        if os.path.exists(oldjson):
            with open(oldjson) as data_file:    
                older_data = json.load(data_file)
             
            ### Makes a list of dataset identifiers in the older json
            older_ids = getIdentifiers(older_data)
            
            ### compares identifiers in the older json harvest of the data portal with identifiers in the new json, 
            ### creating dictionaries with 
            ###     1) a complete list of new json identifiers
            ###     2) a list of just the items that appear in the new json but not the older one
            newjson_ids = {}
            newitem_ids = {}
            
            for y in range(len(newdata["dataset"])):
                identifier = newdata["dataset"][y]["identifier"]
                newjson_ids[y] = identifier  
                if identifier not in older_ids.values():
                    newitem_ids[y] = identifier
            
            
            ### Creates a dictionary of metadata elements for each new data portal item. 
            ### Includes an option to print a csv report of new items for each data portal.          
            ### Puts dictionary of identifiers (key), metadata elements (values) for each data portal into a list 
            ### (to be used printing the combined report) 
            ### i.e. [portal1{identifier:[metadataElement1, metadataElement2, ... ], 
            ###       portal2{identifier:[metadataElement1, metadataElement2, ... ], ...}]
            All_New_Items.append(metadataNewItems(newdata, newitem_ids))
            
            ### Compares identifiers in the older json to the list of identifiers from the newer json. 
            ### If the record no longer exists, adds selected fields into a dictionary of deleted items (deletedItemDict)
            deletedItemDict = {}
            for z in range(len(older_data["dataset"])):
                identifier = older_data["dataset"][z]["identifier"]
                if identifier not in newjson_ids.values():
                    del_metadata = []
                    del_metalist = [identifier.rsplit('/', 1)[-1], identifier, portalName]
                    for value in del_metalist:
                        del_metadata.append(value)

                    deletedItemDict[identifier] = del_metadata
            
            All_Deleted_Items.append(deletedItemDict)
            
            ### collects information for the status report 
            status_metalist = [len(newjson_ids), len(newitem_ids), len(deletedItemDict)]
            for value in status_metalist:
                status_metadata.append(value)

        ### if there is no older json for comparions....
        else:
            print("There is no comparison json for %s" % (portalName))
            ### Makes a list of dataset identifiers in the new json
            newjson_ids = getIdentifiers(newdata)
            
            All_New_Items.append(metadataNewItems(newdata, newjson_ids))

            ### collects information for the status report 
            status_metalist = [len(newjson_ids), len(newjson_ids), '0']
            for value in status_metalist:
                status_metadata.append(value)
                
        Status_Report [portalName] = status_metadata
            
### prints two csv spreadsheets with all items that are new or deleted since the last time the data portals were harvested                                
newItemsReport = directory + "\\reports\\allNewItems_%s.csv" % (ActionDate)
printItemReport(newItemsReport, fieldnames, All_New_Items)

delItemsReport = directory + "\\reports\\allDeletedItems_%s.csv" % (ActionDate)
printItemReport(delItemsReport, delFieldsReport, All_Deleted_Items)       
                
reportStatus = directory + "\\reports\\portal_status_report_%s.csv" % (ActionDate) 
printReport(reportStatus, Status_Report, statusFieldsReport)