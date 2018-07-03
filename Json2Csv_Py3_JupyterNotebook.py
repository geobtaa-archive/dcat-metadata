
# coding: utf-8

# #### From the Group Project:  
# _"Project goal: Repair, update, and clarify the existing Python script used by the Big Ten Geospatial Data Portal developers used to collect metadata from the Washington County website. The intent of this script is to pull the metadata from the site, strip it, and perform an organized import into a csv for cataloguing. It was also the intent for the script to edit & adapt functions as the site changes, as well as serve as a template and/or code source for future stripping scripts."_

# ## For the Individual Project:
# 
# ### This script has been adjusted to include user textstring input for parameters and store codeblocks in functions.  I spent a significant amount of time determining the best way to break code into functions for related output.
# 
# ### Over time as I try to utilize and extend/adapt the script it will likely grow more flexible.  The biggest difference between this script and the group script is that this produces working output.  We were close before but the dictionary values were not generating the way we wanted.
# 
# ### I've included a sample geoportal input CSV to use as a parameter and one of the old Python 2.7 scripts for code comparison.

# In[1]:


# Import modules necessary for geospatial resource harvest and analysis.
# JSON & URL modules provide methods for pulling harvest data from internet.
# CSV module needed for dataset export once iterated through.
# Other modules used for clean-up and conversion of data fields & attributes.

import datetime
import os.path
import csv
import json
import csv
import urllib.request
from urllib.request import urlopen
import regex
import codecs


# ### The Harvest Geoportal CSV file should follow this schema:
# **1st Row (column headings):**  
# * **_portalName,URL_**  
# 
# **Rows 2 to n (portal ID, portal JSON):**    
# * *e.g., 05b-12,http://data-wcmn.opendata.arcgis.com/data.json*  
# 

# In[2]:


# I added all functions used later to this cell.

def dirStruct(dirPath):
    # Function to generate folders in a directory for inputs/outputs.
    
    path = dirPath
    rFold = path + r'\reports'
    jFold = path + r'\jsons'
    os.mkdir(rFold)
    os.mkdir(jFold)
    print("")
    print("Working directory is ready.")
    print("Jsons & reports folders added.")
    return [rFold, jFold]


def csvPrep(csvFile, dirPath):
    # Function to collect JSON files from internet URLs and save locally.
    
    file = csvFile
    path = dirPath
    with open(file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            portalName = row["portalName"]
            url = row["URL"]
            harvestJson = dirStruct(path)[1] + "\%s_%s.json" % (portalName, today)
            response = urlopen(url)
            reader = codecs.getreader("utf-8")
            harvestRaw = json.load(reader(response))
            with open(harvestJson, "w") as outfile:
                json.dump(harvestRaw, outfile)
            print("Json Harvest file saved!")
    return [harvestRaw]


def setFieldNames(rawHarvest):
    # Function to pull relevant field names from JSON dictionary format.
    
    fieldHarvest = rawHarvest
    publisherList = []
    contactList = []
    distribList = []

    for resource in fieldHarvest:
        fieldList = list(resource)
        fieldList.remove("@type")    
        publisher = fieldHarvest[0]["publisher"]
        contactPoint = fieldHarvest[0]["contactPoint"]
        distribution = fieldHarvest[0]["distribution"]
    for name in publisher:
        publisherList.append("publisher" + name.capitalize())
    for contact in contactPoint:
        if contact != "@type":
            contactList.append(contact)
    cnt = 1
    for distrib in distribution:
        keys = distrib.keys()
        for key in keys:
            if key != "@type":
                distField = key+str(cnt)
                distribList.append(distField)
        cnt += 1

    for field in fieldList:
        if field == "keyword":
            kloc = fieldList.index(field)
            fieldList.remove(field)
            fieldList.insert(kloc, "keywords")
        elif field == "publisher":
            ploc = fieldList.index(field)
            fieldList.remove(field)
            publisherList.reverse()
            for pub in publisherList:
                fieldList.insert(ploc, pub)
        elif field == "contactPoint":
            cloc = fieldList.index(field)
            fieldList.remove(field)
            contactList.reverse()
            for con in contactList:
                fieldList.insert(cloc, con)
        elif field == "distribution":
            dloc = fieldList.index(field)
            fieldList.remove(field)
            distribList.reverse()
            for dist in distribList:
                fieldList.insert(dloc, dist)
        else:
            pass
    return fieldList

def getValues(rawHarvest):
    #Function to harvest values from JSON dictionary to
    #correspond to the field name elements collected.
    
    valuesHarvest = rawHarvest
    valueList = []

    e = 0
    for resource in valuesHarvest:
        valList = []
        allVals = valuesHarvest[e]
        valKeys = allVals.keys()
        publisher = valuesHarvest[e]["publisher"]
        contact = valuesHarvest[e]["contactPoint"]
        distribution = valuesHarvest[e]["distribution"]
        for key in valKeys:
            vals = allVals[key]
            if key == "publisher":
                pubKeys = publisher.keys()
                for pk in pubKeys:
                    pubVals = publisher[pk]
                    valList.append(pubVals)
            elif key == "contactPoint":
                conKeys = contact.keys()
                for ck in conKeys:
                    if ck != "@type":
                        conVals = contact[ck]
                        valList.append(conVals)
            elif key == "distribution":
                for distrib in distribution:
                    disKeys = distrib.keys()
                    for dk in disKeys:
                        if dk != "@type":
                            disVals = distrib[dk]
                            valList.append(disVals)          
            else:
                if key != "@type":
                    valList.append(vals)
        valueList.append(valList)
        e += 1
    return valueList


def csvOutfile(csvFile, dirPath):
    # Function to generate a CSV output file of harvest results.
    
    inCsv = csvFile
    path = dirPath
    # sys.stdout.encoding='utf-8'
    with open(inCsv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            portalName = row["portalName"]
    report2 = (in2 + r'\reports\%s_%s_HarvestReport.csv') % (portalName, today)
    with open(report2, 'w', encoding='cp1252', errors='replace') as outfile:
        csvout = csv.writer(outfile)
        for row in harvestList:
            csvout.writerow(row)
    print(today, "Report for", portalName, "complete!")


# In[ ]:


# harvestNew = r'C:\Work\Collections\ArcGIS_Portals\GEOhio\jsons\11a-01_20180523'


# In[3]:


# User input data elements to provide parameters for geoportal harvest.

in1 = input("Enter path and name of formatted geoportal harvest CSV \n(C:\\...\\filename.csv): ")
in2 = input("Enter path to new empty working folder \n(C:\...\Xfolder): ")

today = datetime.date.today().isoformat().replace("-","")

# Function calls with user input parameters
harvest = csvPrep(in1, in2)[0]["dataset"]
# harvestNew = in2 + r'11a-01_20180523.json'
# harvest = harvestNew[0]["dataset"]
harvestList = getValues(harvest)
harvestList.insert(0, setFieldNames(harvest))
csvOutfile(in1, in2)

# C:\Work\Collections\ArcGIS_Portals\GEOhio\GEOhio_portal.csv
# C:\Users\smit1975\School\GEOG_5541_Geocomputing\PROJECT\TestRun\All_ArcPortals.csv

