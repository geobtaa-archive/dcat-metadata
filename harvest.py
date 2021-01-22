# -*- coding: utf-8 -*-
"""
Original created on Wed Mar 15 09:18:12 2017
Edited Dec 28 2018; January 8, 2019
@author: kerni016

Updated July 28, 2020
Updated by Yijing Zhou @YijingZhou33

Updated October 6, 2020
Updated by Ziying Cheng @Ziiiiing
"""
## To run this script you need a csv with five columns (portalName, URL, provenance, publisher, and spatialCoverage) with details about ESRI open data portals to be checked for new records.
## Need to define directory path (containing arcPortals.csv, folder "jsons" and "reports"), and list of fields desired in the printed report
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
import time

######################################

### Manual items to change!

## names of the main directory containing folders named "jsons" and "reports"
## Windows:
## directory = r'E:\RA\dcat-metadata_test_fix2'
## MAC or Linux:
directory = r'/Users/zing/Desktop/RA/GitHub/dcat-metadata/'

## csv file contaning portal list
portalFile = 'arcPortals_test.csv'

## list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ['Title', 'Alternative Title', 'Description', 'Language', 'Creator', 'Publisher', 'Genre',
              'Subject', 'Keyword', 'Date Issued', 'Temporal Coverage', 'Date Range', 'Solr Year', 'Spatial Coverage',
              'Bounding Box', 'Type', 'Geometry Type', 'Format', 'Information', 'Download', 'MapServer', 
              'FeatureServer', 'ImageServer', 'Slug', 'Identifier', 'Provenance', 'Code', 'Is Part Of', 'Status',
              'Accrual Method', 'Date Accessioned', 'Rights', 'Access Rights', 'Suppressed', 'Child']

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
        
        creator = newdata["dataset"][y]["publisher"]
        for pub in creator.values():
            creator = pub.replace(u"\u2019", "'")
                
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
                    if 'downloadURL' in dictionary.keys():
                        downloadURL = dictionary["downloadURL"].split('?')[0]
                    else:
                        downloadURL = dictionary["accessURL"].split('?')[0]
                    
                    geometryType = "Vector"
                    
                ### If the Rest API is based on an ImageServer, change genre, type, and format to relate to imagery
                if dictionary["title"] == "Esri Rest API":
                    if 'accessURL' in dictionary.keys():
                        webService = dictionary['accessURL']
                        
                        if webService.rsplit('/', 1)[-1] == 'ImageServer':
                            genre = "Aerial imagery"
                            formatElement = 'Imagery'
                            typeElement = 'Image|Service'
                            geometryType = "Image"                       
                    else:
                        genre = ""
                        formatElement = ""
                        typeElement = ""
                        downloadURL = "" 
                    
            ### If the distribution section of the metadata is not structured in a typical way
            except:
                genre = ""
                formatElement = ""
                typeElement = ""
                downloadURL =  ""
                
                continue
                                                 
        ### If the item has both a Shapefile and Esri Rest API format, change type                               
        if "Esri Rest API" in format_types:
            if "Shapefile" in format_types:
                typeElement = "Dataset|Service"
        
        try:
            bboxList = []
            bbox = ''
            spatial = cleanData(newdata["dataset"][y]['spatial'])
            typeDmal = decimal.Decimal
            fix4 = typeDmal("0.0001")
            for coord in spatial.split(","):
                coordFix = typeDmal(coord).quantize(fix4)
                bboxList.append(str(coordFix))
            bbox = ','.join(bboxList)
        except:
            spatial = ""     
        
        subject = ""
        keyword = newdata["dataset"][y]["keyword"]
        keyword_list = []
        keyword_list = '|'.join(keyword).replace(' ', '')
        
        dateIssued = cleanData(newdata["dataset"][y]['issued'])
        temporalCoverage = ""
        dateRange = ""
        solrYear = ""
        
        information = cleanData(newdata["dataset"][y]['landingPage'])
        
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


        slug = identifier.rsplit('/', 1)[-1]
        identifier_new = "https://hub.arcgis.com/datasets/" + slug   
        isPartOf = portalName
        
        status = "Active"
        accuralMethod = "ArcGIS Hub"
        dateAccessioned = ""
                  
        rights = "Public"               
        accessRights = ""
        suppressed = "FALSE"
        child = "FALSE"
               
        metadataList = [title, alternativeTitle, description, language, creator, publisher,
                    genre, subject, keyword_list, dateIssued, temporalCoverage,
                    dateRange, solrYear, spatialCoverage, bbox, typeElement, geometryType,
                    formatElement, information, downloadURL, mapServer, featureServer,
                    imageServer, slug, identifier_new, provenance, portalName, isPartOf, status,
                    accuralMethod, dateAccessioned, rights, accessRights, suppressed, child]
        
        ### deletes data portols except genere = 'Geospatial data' or 'Aerial imagery'  
        for i in range(len(metadataList)):
            if metadataList[6] != "":
                metadata.append(metadataList[i])

        newItemDict[slug] = metadata
        
        for k in list(newItemDict.keys()):
            if not newItemDict[k]:
                del newItemDict[k]
         
    return newItemDict


All_New_Items = []
All_Deleted_Items = []
Status_Report = {}

## Generate the current local time with the format like 'YYYYMMDD' and save to the variable named 'ActionDate'
ActionDate = time.strftime('%Y%m%d')

## List all files in the 'jsons' folder under the current directory and store file names in the 'filenames' list 
filenames = os.listdir('jsons')

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

        ## For each open data portal in the csv list...
        ## create an empty list to extract all previous action dates only from file names
        dates = []

        ## loop over all file names in 'filenames' list and find the json files for the selected portal
        ## extract the previous action dates only from these files and store in the 'dates' list
        for filename in filenames:
            if filename.startswith(portalName):
                ## format of filename is 'portalName_YYYYMMDD.json'
                ## 'YYYYMMDD' is located from index -13(included) to index -5(excluded)
                dates.append(filename[-13:-5]) 

        # remove action date from previous dates if any 
        if ActionDate in dates:
            dates.remove(ActionDate)

        ## find the latest action date from the 'dates' list
        PreviousActionDate = max(dates)

        ## renames file paths based on portalName and manually provided dates
        oldjson = directory + '/jsons/%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '/jsons/%s_%s.json' % (portalName, ActionDate)
        

        ## if newjson already exists, do not need to request again
        if os.path.exists(newjson):
            with open(newjson, 'r') as fr:
                newdata = json.load(fr)
        else:
            try:
                context = ssl._create_unverified_context()
                response = urllib.request.urlopen(url, context=context)
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
newItemsReport = directory + "/reports/allNewItems_%s.csv" % (ActionDate)
printItemReport(newItemsReport, fieldnames, All_New_Items)

delItemsReport = directory + "/reports/allDeletedItems_%s.csv" % (ActionDate)
printItemReport(delItemsReport, delFieldsReport, All_Deleted_Items)       
                
reportStatus = directory + "/reports/portal_status_report_%s.csv" % (ActionDate) 
printReport(reportStatus, Status_Report, statusFieldsReport)