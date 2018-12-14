#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Import modules necessary for geospatial resource harvest and analysis.
# JSON & URL modules for methods of scraping harvest data from internet.
# CSV module needed for dataset export once iterated through.
# Other modules for clean-up and conversion of data fields & attributes.

import os
import os.path
import urllib.request
from urllib.request import urlopen
import datetime
import decimal
import json
import operator
import regex
import codecs
import progressbar as pb
import csv


# In[ ]:


def schemaAllFields():
    # Function to define and name metadata standard
    ## Project Open Data Schema v1.1 ALL metadata fields.
    # Template found at https://project-open-data.cio.gov/v1.1/schema/
    
    ## root == Root JSON Dict, dat == dataset Dict, pub == publisher Dict,
    ##  con == contactPoint Dict, dis == distribution Dict
    
    allRootList = ["@context", "@id", "@type",
                   "conformsTo", "describedBy", "dataset"]
    allDatList = ["@type", "identifier", "title", "description", "keyword",
                  "issued", "modified", "publisher", "contactPoint",
                  "accessLevel", "distribution", "landingPage", "webService",
                  "license", "spatial", "theme", "temporal", "describedBy",
                  "isPartOf", "references", "rights", "accrualPeriodicity",
                  "conformsTo", "describedByType", "language", "bureauCode",
                  "programCode", "dataQuality", "primaryITInvestmentUII",
                  "systemOfRecords"]
    allConList = ["@type", "fn", "hasEmail"]
    allPubList = ["@type", "name", "subOrganizationOf"]
    allDisList = ["@type", "title", "format", "mediaType", 
                  "accessURL", "downloadURL", "description", 
                  "conformsTo", "describedBy", "describedByType"]

# Dictionary variable defined for key-value matching.
    schemaDict = {"root": allRoot, "dat": allDat, 
                  "con": allCon, "pub": allPub, "dis": allDis}
    
    return schemaDict


# In[ ]:


# Conversion of resultant dictionary to list if better for user script editing.
def getSchema():
    schemaDict = schemaAllFields()
    schemaKeys = schemaDict.keys()
    schemaList = []
    for key in schemaKeys:
        vals = schemaDict[key]
        pairing = [key, vals]
        schemaList.append(pairing)
        
    return [schemaDict, schemaList]


# In[ ]:


def pathDefs(portalCsvPath, portalCsvFile, workingDir):
    # Function to generate/establish working output file directory.
    
    cPath = os.path.normpath(portalCsvPath)
    cFile = os.path.join(cPath, portalCsvFile + ".csv")
    wDir = os.path.normpath(workingDir)
    jPath = os.path.join(wDir, "jsons")
    rPath = os.path.join(wDir, "reports")    
    if not os.path.exists(jPath):
        os.mkdir(jPath)
    if not os.path.exists(rPath):
        os.mkdir(rPath)    
    print("Working data & directory structure defined.\n")
    return [cFile, wDir, jPath, rPath]


# In[ ]:


def harvestJsons():    
    with open(cFile) as c:
        reader = csv.DictReader(c)
        for row in reader:
            pName = row["portalName"]
            url = row["URL"]
            nJson = "%s_%s_Harvest.json" % (pName, today)
            harvestJson = os.path.join(jPath, nJson)
            response = urlopen(url)
            reader = codecs.getreader("utf-8")
            pScrape = json.load(reader(response))
            widgets = [pb.Percentage(), pb.Bar()]
            bar = pb.ProgressBar(widgets=widgets, max_value=1000).start()
            for i in range(100):
                with open(harvestJson, "w") as outJson:
                    json.dump(pScrape, outJson)
                bar.update(10 * i + 1)
            bar.finish()
            print("    *", nJson)
        print("\n", "-" * 80, "\n")


# In[ ]:


def idSlice(identifierURL):
    identifier = []
    u = identifierURL
    arc = u.find("/datasets/")
    soc = u.find("/d/")
    i = arc + 10
    i2 = soc
    if i > 0:
        identifier.append(u[i:])
    elif i2 > 0:
        identifier.append(u[-9:])
    else:
        identifier.append("check identifier URL")
    uuid = str(identifier[0])
    return uuid

def issuedSlice(issuedDate):
    isoIssued = []
    inStr = issuedDate    
    yr, mo, dy = int(inStr[:4]), int(inStr[5:7]), int(inStr[8:10])
    dateFormat = datetime.date(yr, mo, dy).isoformat()
    isoIssued.append(dateFormat)
    issued = str(isoIssued[0])
    return issued

def boundingBox(spatialString):
    bbox = []
    formatBbox = []
    inStr = spatialString
    typeDmal = decimal.Decimal
    fix4 = typeDmal("0.0001")    
    for coord in inStr.split(","):
        coordFix = typeDmal(coord).quantize(fix4)
        bbox.append(str(coordFix))            
    return bbox

def getData(inJson):
    hasVals = []
    for key in inJson["dataset"]:
        identifier = key["identifier"]
        ident = ["identifier", identifier]
        hasVals.append(idSlice(ident[1]))
        
        dsetTitle = key["title"]
        listTitle = ["title", dsetTitle]
        hasVals.append(listTitle[1])
        
        dsetDescript = key["description"]
        listDescript = ["description", dsetDescript]
        hasVals.append(listDescript[1])
        
        dsetKeywords = key["keyword"]
        listKeywords = ["keyword", dsetKeywords]
        hasVals.append(listKeywords[1])
        
        dsetIssued = key["issued"]
        listIssued = ["issued", dsetIssued]
        hasVals.append(issuedSlice(listIssued[1]))
        
        dsetSpatial = key["spatial"]
        listSpatial = ["spatial", dsetSpatial]        
        hasVals.append(",".join(boundingBox(listSpatial[1])))
        
        dsetPublisher = key["publisher"]["name"]
        listPublisher = ["name", dsetPublisher]
        hasVals.append(listPublisher[1])
        
        dsetLandingPage = key["landingPage"]
        listLandingPage = ["landingPage", dsetLandingPage]
        hasVals.append(listLandingPage[1])
        
        dsetWebService = key["webService"]
        listWebService = ["webService", dsetWebService]
        hasVals.append(listWebService[1])
        
        dsetDistrib = key["distribution"]        
        distribValList = ["Shapefile", "GeoJSON", "OGC WFS", "OGC WMS"]
        for z in range(len(dsetDistrib)):           
            for index, (keys, values) in enumerate(dsetDistrib[z].items()):
                if keys == "title":
                    if values in distribValList:                    
                        hasVals.append(values)
                listVals = [values]
                for val in listVals:
                    if ".geojson" in val:
                        hasVals.append(val)
                    elif ".zip" in val:
                        hasVals.append(val)
                    elif "=WFS" in val:
                        hasVals.append(val)
                    elif "=WMS" in val:
                        hasVals.append(val)
                    else:
                        continue

    return hasVals

def harvestReports():
    with open(cFile) as c:
        reader = csv.DictReader(c)
        for row in reader:
            pName = row["portalName"]
            nReport = "%s_%s_HarvestReport.csv" % (pName, today)
            harvestReport = os.path.join(rPath, nReport)
            with open(csvOut, "w") as f:
                writer = csv.writer(f, dialect="unix")    
                for row in rows:
                    writer.writerow(row)
    
#             with open(harvestReport, 'w') as outfile:
#                 csvout = csv.writer(outfile)
#                 for row in harvestList:
#                     csvout.writerow(row)


# In[ ]:


# User input, Function Call Cell 1

## ISO format current date
today = datetime.date.today().isoformat().replace("-","")

# User input data elements to provide parameters for geoportal harvest.
userIn1 = input("*Enter path of folder containing formatted geoportal harvest CSV \n(C:folderPath, Windows or UNIX-style):\n")
print("")
userIn2 = input("*Enter name of formatted geoportal harvest CSV \n(C:formattedFile, No extension on filename):\n")
print("")
userIn3 = input("*Enter path of data output folder \n(C:folderPath, Windows or UNIX-style):\n")
print("\n", "-" * 80, "\n")

# Input/output file names & paths
pathLookup = pathDefs(userIn1, userIn2, userIn3)
cFile = pathLookup[0]
wDir = pathLookup[1]
jPath = pathLookup[2]
rPath = pathLookup[3]

print("Input CSV file, formatted geoportal harvest list:\n   ", cFile)
print("Script output file directory:\n   ", wDir)
print("Output folder, geoportal response JSONs:\n   ", jPath)
print("Output folder, JSON to CSV conversion Reports:\n   ", rPath)
print("\n", "-" * 80, "\n")
print("Saving JSONs:\n   ")

# Run portal harvest script
harvestJsons()

# responseJsons = harvestJsons()
jList = []
for newJson in os.listdir(jPath):
    jList.append(newJson)

# INSERT JSONCOMPARISON SCRIPT HERE

# datAll = lScrape[0]["dataset"]
# testFile = os.path.join(jPath, "04c-02_20181205_Harvest.json")


# In[ ]:


spatialList = []

# Iterate through JSONs
for j in jList:
    j = harvestJson
    with open(harvestJson, "r") as targetJson:
        readJson = json.load(targetJson)

# Run JSON dataset key/value capture iteration.
getData(readJson)

### ZIP UP result lists for CSV outfile prep.
# rows = zip(idList, tiList, descList, kewList, issList, spList, pubList, 
#            infoList, servList, licList, thmList)

# csvOut = r"C:\Users\Andy\Desktop\Work\Development\Script\A_proj_Json2Csv\Testing\TestCSVs\testing.csv"
# csvDistOut = r"C:\Users\Andy\Desktop\Work\Development\Script\A_proj_Json2Csv\Testing\TestCSVs\testingDist.csv"

# with open(csvOut, "w") as f:
#     writer = csv.writer(f, dialect="unix")    
#     for row in rows:
#         writer.writerow(row)

# def harvestReports():
#     with open(cFile) as c:
#         reader = csv.DictReader(c)
#         for row in reader:
#             pName = row["portalName"]
#             nReport = "%s_%s_HarvestReport.csv" % (pName, today)
#             harvestReport = os.path.join(rPath, nReport)
#             with open(harvestReport, 'w') as outfile:
#                 csvout = csv.writer(outfile)
#                 for row in harvestList:
#                     csvout.writerow(row)

# def csvOutfile(csvFile, dirPath):
#     # Function to generate a CSV output file of harvest results.
    
#     inCsv = csvFile
#     path = dirPath
#     # sys.stdout.encoding='utf-8'
#     with open(inCsv) as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             portalName = row["portalName"]
#     report2 = (in2 + r'\reports\%s_%s_HarvestReport.csv') % (portalName, today)
#     with open(report2, 'w', encoding='cp1252', errors='replace') as outfile:
#         csvout = csv.writer(outfile)
#         for row in harvestList:
#             csvout.writerow(row)
#     print(today, "Report for", portalName, "complete!")


# In[ ]:


# fieldDict = schemaAllFields()
# fieldKeys = fieldDict.keys()
# datFieldList = fieldDict.get('dat')
# newDict = {}
# c = 0
# for d in datFieldList:
#     newDict[d] = c
#     c += 1
# dSetDict_keys = set(dSet.keys())
# newDict_keys = set(newDict.keys())
# shared_keys = set(newDict.keys()) & set(dSet.keys())

# with open(testFile, "r") as read_file:
#     readJson = json.load(read_file)
#     rootKeys = readJson.keys()
#     dSet = readJson["dataset"][0]
#     dSetList = list(dSet.keys())

# def ordered_set(in_list):
#     out_list = []
#     added = set()
#     for val in in_list:
#         if not val in added:
#             out_list.append(val)
#             added.add(val)
#     return out_list

# fieldList = []
# rKeys = rFieldDict.keys()
# for key in rKeys:   
#     vals = rFieldDict[key]
#     for v in vals:
#         fieldList.append(v)

# def parseJsons():
#     for open(os.list)
#     for open(newJson in os.listdir(jPath, "r")) as inJson:
#         readJson = json.load(inJson)
#         root = readJson[0]
#         dSet = root["dataset"]
#         resourceCount = len(dSet)        
#     allKeysList = []
#     allValsList = []    
#     allKeys = allFieldsDict.keys()
#     for aKey in allKeys:
#         allKeysList.append(aKey)
#         allVals = allFieldsDict[aKey]
#         for aVal in allVals:
#             allValsList.append(aVal)

# def schemaParse():
#     # Assemble schema field names in preferred spreadsheet order.
    
#     allFieldsDict = schemaAllFields()
#     allKeysList = []
#     allValsList = []
    
#     allKeys = allFieldsDict.keys()
#     for aKey in allKeys:
#         allKeysList.append(aKey)
#         allVals = allFieldsDict[aKey]
#         for aVal in allVals:
#             allValsList.append(aVal)
            
#     return allKeysList, allValsList

# def dictOrg(dictionary):
#     dictTuple = []
#     d = dictionary
#     for index, (key, value) in enumerate(d.items()):
#         dTuple = (index, key, value)
#         dictTuple.append(dTuple)        
#     return dictTuple

# a = (1,2,3)
# (one,two,three) = a
# print(one)


# In[ ]:




