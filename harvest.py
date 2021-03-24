# -*- coding: utf-8 -*-
"""
Original created on Wed Mar 15 09:18:12 2017
Edited Dec 28 2018; January 8, 2019
@author: kerni016

Updated July 28, 2020
Updated by Yijing Zhou @YijingZhou33

Updated October 6, 2020
Updated by Ziying Cheng @Ziiiiing

Updated February 16, 2021
Updated by Yijing Zhou @YijingZhou33
-- populating spatial coverage based on bounding boxes

Updated February 24, 2021<br>
Updated by Yijing Zhou @YijingZhou33
-- Handling download link errors for newly added items

"""
# To run this script you need a csv with five columns (portalName, URL, provenance, publisher, and spatialCoverage) with details about ESRI open data portals to be checked for new records.
# Need to define directory path (containing arcPortals.csv, folder "jsons" and "reports"), and list of fields desired in the printed report
# The script currently prints two combined reports - one of new items and one with deleted items.
# The script also prints a status report giving the total number of resources in the portal, as well as the numbers of added and deleted items.

import json
import csv
import urllib
import urllib.request
import os
from html.parser import HTMLParser
import decimal
import re
import time
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import numpy as np
from itertools import chain
from itertools import repeat
from functools import reduce
import requests

######################################

# Manual items to change!

# names of the main directory containing folders named "jsons" and "reports"
# Windows:
directory = r'D:\Library RA\dcat-metadata'
# MAC or Linux:
# directory = r'/Users/zing/Desktop/RA/GitHub/dcat-metadata/'

# csv file contaning portal list
portalFile = 'arcPortals.csv'

# list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ['Title', 'Alternative Title', 'Description', 'Language', 'Creator', 'Publisher', 'Genre',
              'Subject', 'Keyword', 'Date Issued', 'Temporal Coverage', 'Date Range', 'Solr Year', 'Spatial Coverage',
              'Bounding Box', 'Type', 'Geometry Type', 'Format', 'Information', 'Download', 'MapServer',
              'FeatureServer', 'ImageServer', 'Slug', 'Identifier', 'Provenance', 'Code', 'Is Part Of', 'Status',
              'Accrual Method', 'Date Accessioned', 'Rights', 'Access Rights', 'Suppressed', 'Child']

# list of fields to use for the deletedItems report
delFieldsReport = ['identifier', 'landingPage', 'portalName']

# list of fields to use for the portal status report
statusFieldsReport = ['portalName', 'total', 'new_items', 'deleted_items']

# dictionary using partial portal code to find out where the data portal belongs
statedict = {'01': 'Indiana', '02': 'Illinois', '03': 'Iowa', '04': 'Maryland', '04c-01': 'District of Columbia', 
             '04f-01': '04f-01', '05': 'Minnesota', '06': 'Michigan', '07': 'Michigan', '08': 'Pennsylvania', 
             '09': 'Indiana', '10': 'Wisconsin', '11': 'Ohio', '12': 'Illinois', '13': 'Nebraska', '99': 'Esri'}
#######################################


# function to removes html tags from text
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
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

# function that prints metadata elements from the dictionary to a csv file (portal_status_report)
# with as specified fields list as the header row.


def printReport(report, dictionary, fields):
    with open(report, 'w', newline='', encoding='utf-8') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)

# Similar to the function above but generates two csv files (allNewItems & allDeletedItems)


def printItemReport(report, fields, dictionary):
    with open(report, 'w', newline='', encoding='utf-8') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for portal in dictionary:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)

# function that creates a dictionary with the position of a record in the data portal DCAT metadata json as the key
# and the identifier as the value.


def getIdentifiers(data):
    json_ids = {}
    for x in range(len(data["dataset"])):
        json_ids[x] = data["dataset"][x]["identifier"]
    return json_ids


# function that returns a dictionary of selected metadata elements into a dictionary of new items (newItemDict) for each new item in a data portal.
# This includes blank fields '' for columns that will be filled in manually later.
def metadataNewItems(newdata, newitem_ids):
    newItemDict = {}
    # y = position of the dataset in the DCAT metadata json, v = landing page URLs
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
        # Remove newline, whitespace, defalut description and replace singe quote, double quote
        if description == "{{default.description}}":
            description = description.replace("{{default.description}}", "")
        else:
            description = re.sub(r'[\n]+|[\r\n]+', ' ',
                                 description, flags=re.S)
            description = re.sub(r'\s{2,}', ' ', description)
            description = description.replace(u"\u2019", "'").replace(u"\u201c", "\"").replace(u"\u201d", "\"").replace(
                u"\u00a0", "").replace(u"\u00b7", "").replace(u"\u2022", "").replace(u"\u2013", "-").replace(u"\u200b", "")

        language = "English"

        creator = newdata["dataset"][y]["publisher"]
        for pub in creator.values():
            creator = pub.replace(u"\u2019", "'")

        format_types = []
        genre = ""
        formatElement = ""
        typeElement = ""
        downloadURL = ""
        geometryType = ""
        webService = ""

        distribution = newdata["dataset"][y]["distribution"]
        for dictionary in distribution:
            try:
                # If one of the distributions is a shapefile, change genre/format and get the downloadURL
                format_types.append(dictionary["title"])
                if dictionary["title"] == "Shapefile":
                    genre = "Geospatial data"
                    formatElement = "Shapefile"
                    if 'downloadURL' in dictionary.keys():
                        downloadURL = dictionary["downloadURL"].split('?')[0]
                    else:
                        downloadURL = dictionary["accessURL"].split('?')[0]

                    geometryType = "Vector"

                # If the Rest API is based on an ImageServer, change genre, type, and format to relate to imagery
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

            # If the distribution section of the metadata is not structured in a typical way
            except:
                genre = ""
                formatElement = ""
                typeElement = ""
                downloadURL = ""

                continue

        # If the item has both a Shapefile and Esri Rest API format, change type
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

        # deletes data portols except genere = 'Geospatial data' or 'Aerial imagery'
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

# Generate the current local time with the format like 'YYYYMMDD' and save to the variable named 'ActionDate'
ActionDate = time.strftime('%Y%m%d')

# List all files in the 'jsons' folder under the current directory and store file names in the 'filenames' list
filenames = os.listdir('jsons')

# Open a list of portals and urls ending in /data.json from input CSV
# using column headers 'portalName', 'URL', 'provenance', 'SpatialCoverage'
with open(portalFile, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Read in values from the portals list to be used within the script or as part of the metadata report
        portalName = row['portalName']
        url = row['URL']
        provenance = row['provenance']
        publisher = row['publisher']
        spatialCoverage = ''
        print(portalName, url)

        # For each open data portal in the csv list...
        # create an empty list to extract all previous action dates only from file names
        dates = []

        # loop over all file names in 'filenames' list and find the json files for the selected portal
        # extract the previous action dates only from these files and store in the 'dates' list
        for filename in filenames:
            if filename.startswith(portalName):
                # format of filename is 'portalName_YYYYMMDD.json'
                # 'YYYYMMDD' is located from index -13(included) to index -5(excluded)
                dates.append(filename[-13:-5])

        # remove action date from previous dates if any
        if ActionDate in dates:
            dates.remove(ActionDate)

        # find the latest action date from the 'dates' list
        PreviousActionDate = max(dates)

        # renames file paths based on portalName and manually provided dates
        oldjson = directory + \
            '/jsons/%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '/jsons/%s_%s.json' % (portalName, ActionDate)

        # if newjson already exists, do not need to request again
        if os.path.exists(newjson):
            with open(newjson, 'r') as fr:
                newdata = json.load(fr)
        else:
            response = urllib.request.urlopen(url)
            if response.headers['content-type'] != 'application/json; charset=utf-8':
                print("\n--------------------- Data portal URL does not exist --------------------\n",
                      portalName, url,  "\n--------------------------------------------------------------------------\n")
                continue
            else:
                newdata = json.load(response)

            # Saves a copy of the json to be used for the next round of comparison/reporting
            with open(newjson, 'w', encoding='utf-8') as outfile:
                json.dump(newdata, outfile)

        # collects information about number of resources (total, new, and old) in each portal
        status_metadata = []
        status_metadata.append(portalName)

        # Opens older copy of data/json downloaded from the specified Esri Open Data Portal.
        # If this file does not exist, treats every item in the portal as new.
        if os.path.exists(oldjson):
            with open(oldjson) as data_file:
                older_data = json.load(data_file)

            # Makes a list of dataset identifiers in the older json
            older_ids = getIdentifiers(older_data)

            # compares identifiers in the older json harvest of the data portal with identifiers in the new json,
            # creating dictionaries with
            # 1) a complete list of new json identifiers
            # 2) a list of just the items that appear in the new json but not the older one
            newjson_ids = {}
            newitem_ids = {}

            for y in range(len(newdata["dataset"])):
                identifier = newdata["dataset"][y]["identifier"]
                newjson_ids[y] = identifier
                if identifier not in older_ids.values():
                    newitem_ids[y] = identifier

            # Creates a dictionary of metadata elements for each new data portal item.
            # Includes an option to print a csv report of new items for each data portal.
            # Puts dictionary of identifiers (key), metadata elements (values) for each data portal into a list
            # (to be used printing the combined report)
            # i.e. [portal1{identifier:[metadataElement1, metadataElement2, ... ],
            # portal2{identifier:[metadataElement1, metadataElement2, ... ], ...}]
            All_New_Items.append(metadataNewItems(newdata, newitem_ids))

            # Compares identifiers in the older json to the list of identifiers from the newer json.
            # If the record no longer exists, adds selected fields into a dictionary of deleted items (deletedItemDict)
            deletedItemDict = {}

            # check deleted item's landing page, if it is broken, delete it
            for z in range(len(older_data["dataset"])):
                identifier = older_data["dataset"][z]["identifier"]
                if identifier not in newjson_ids.values():
                    distribution = older_data["dataset"][z]["distribution"]
                    for dictionary in distribution:
                        if dictionary["title"] == "Shapefile":
                            slug = identifier.rsplit('/', 1)[-1]
                        elif dictionary["title"] == "Esri Rest API":
                            if 'accessURL' in dictionary.keys():
                                webService = dictionary['accessURL']
                                if webService.rsplit('/', 1)[-1] == 'ImageServer':
                                    slug = identifier.rsplit('/', 1)[-1]
                        else:
                            slug = ''

                    # only include records whose download link is either Shapefile or ImageServer
                    if len(slug):
                        del_metadata = []
                        del_metalist = [slug, identifier, portalName]
                        for value in del_metalist:
                            del_metadata.append(value)
                        deletedItemDict[identifier] = del_metadata

            All_Deleted_Items.append(deletedItemDict)

            # collects information for the status report
            status_metalist = [len(newjson_ids), len(
                newitem_ids), len(deletedItemDict)]
            for value in status_metalist:
                status_metadata.append(value)

        # if there is no older json for comparions....
        else:
            print("There is no comparison json for %s" % (portalName))
            # Makes a list of dataset identifiers in the new json
            newjson_ids = getIdentifiers(newdata)

            All_New_Items.append(metadataNewItems(newdata, newjson_ids))

            # collects information for the status report
            status_metalist = [len(newjson_ids), len(newjson_ids), '0']
            for value in status_metalist:
                status_metadata.append(value)

        Status_Report[portalName] = status_metadata

# prints two csv spreadsheets with all items that are new or deleted since the last time the data portals were harvested
newItemsReport = directory + "/reports/allNewItems_%s.csv" % (ActionDate)
printItemReport(newItemsReport, fieldnames, All_New_Items)

delItemsReport = directory + "/reports/allDeletedItems_%s.csv" % (ActionDate)
printItemReport(delItemsReport, delFieldsReport, All_Deleted_Items)

reportStatus = directory + \
    "/reports/portal_status_report_%s.csv" % (ActionDate)
printReport(reportStatus, Status_Report, statusFieldsReport)


# ---------- Populating Spatial Coverage -----------

""" set file path """
df_csv = pd.read_csv(newItemsReport, encoding='unicode_escape')


""" check if link is valid """
print("\n--------------------- Check if link is valid --------------------\n")

def check_url(df, timeout):
    totalcount = len(df.index)
    countnotshp = countprivate = countok = count404 = count500 = countothercode = countconnection = counttimeout = 0
    start_time = time.time()
    filesize = download = imageserver = None
    filesizelist, downloadlist, imageserverlist, oklist, checkagainlist = (
        [] for i in range(5))
    for _, row in df.iterrows():
        slug = row['Slug']
        # access the download link
        if row['Format'] == 'Imagery':
            url = row['ImageServer']
        else:
            url = row['Download']
        try:
            # set timeout to avoid waiting for the server to response forever
            response = requests.get(
                url, timeout=timeout, proxies=urllib.request.getproxies())
            response.raise_for_status()
            # vector data: check if it is a shapefile
            # only keep the data source url
            if 'content-type' in response.headers and response.headers['content-type'] == 'application/json; charset=utf-8':
                countnotshp += 1
                oklist.append(slug)
                print(f'{slug}: Not a shapefile')
            # imagery Data: check if we could access ImageServer
            # only keep the data source url
            elif 'Cache-Control' in response.headers and response.headers['Cache-Control'] == 'private':
                countprivate += 1
                oklist.append(slug)
                print(f'{slug}: Could not access ImageServer')
            else:
                # if records with both vaild data source page and download link
                # query the file size and keep both links
                if 'content-length' in response.headers:
                    filesize = str(
                        round(int(response.headers['content-length']) / 1000000, 4)) + ' MB'
                if row['Download'] is not None:
                    download = row['Download']
                if row['ImageServer'] is not None:
                    imageserver = row['ImageServer']
                countok += 1
                oklist.append(slug)
                print(f'{slug}: Success')
        # check HTTP error: 404 (not found) or 500 (server error)
        except requests.exceptions.HTTPError as errh:
            # 404 error: drop this record
            if errh.response.status_code == 404:
                count404 += 1
            # 500 error: only keeps data source url
            elif errh.response.status_code == 500:
                count500 += 1
                oklist.append(slug)
            # other HTTP errors: only keeps data source url
            else:
                countothercode += 1
            print(f'{slug}: {errh}')
        # check Connection error: need to be double-checked by increasing the timeout or even manually open it
        except requests.exceptions.ConnectionError as errc:
            download = row['Download']
            imageserver = row['ImageServer']
            countconnection += 1
            checkagainlist.append(slug)
            print(f'{slug}: {errc}')
        # check Timeout error: need to be double-checked by increasing the timeout or even manually open it
        except requests.exceptions.Timeout as errt:
            download = row['Download']
            imageserver = row['ImageServer']
            counttimeout += 1
            checkagainlist.append(slug)
            print(f'{slug}: {errt}')

        filesizelist.append(filesize)
        downloadlist.append(download)
        imageserverlist.append(imageserver)

    df['FileSize'] = filesizelist
    df['Download'] = downloadlist
    df['ImageServer'] = imageserverlist

    errordict = {'OK': countok, 'Not a shapefile': countnotshp, 'Timeout Error': counttimeout,
                 'Could not access ImageServer': countprivate, '404 Not Found': count404,
                 '500 Internal Server Error': count500, 'Other HTTP Errors': countothercode,
                 'Connection Errors': countconnection}
    msglist = [
        f'{k}: {v}, {round(v/totalcount * 100.0, 2)}%' for k, v in errordict.items()]
    print('\n---------- %s seconds ----------' % round((time.time() - start_time), 0),
          '\n\n---------- Error Summary ----------',
          '\nAll records: %s' % totalcount)
    for msg in msglist:
        print(msg)

    # records with runtime error need to be double-checked
    return [df[df['Slug'].isin(oklist)], df[df['Slug'].isin(checkagainlist)]]


df_total = check_url(df_csv, 3)
df_ok = df_total[0].reset_index(drop=True)
df_checkagain = df_total[1].reset_index(drop=True)

# set the timeout as 10 seconds
# if there still exists any records, manually check the download link to see if it works
if len(df_checkagain.index):
    df_checkagain = check_url(df_checkagain, 10)
    df_checkok = df_checkagain[0].reset_index(drop=True)
    df_manualcheck = df_checkagain[1].reset_index(drop=True)
    df_manualcheck['Title'] = 'Manually check this link!'
    df_csv = pd.concat([df_ok, df_checkok, df_manualcheck]
                       ).reset_index(drop=True)

""" split csv file if necessary """
# if records come from Esri, the spatial coverage is considered as United States
df_esri = df_csv[df_csv['Publisher'] == 'Esri'].reset_index(drop=True)
df_csv = df_csv[df_csv['Publisher'] != 'Esri'].reset_index(drop=True)


""" split state from column 'Publisher' """
# -----------------------------------------
# The portal code is the main indicator:
# - 01 - Indiana
# - 02 - Illinois
# - 03 - Iowa
# - 04 - Maryland
# - 04c-01 - District of Columbia
# - 04f-01 - Delaware, Philadelphia, Maryland, New Jersey
# - 05 - Minnesota
# - 06 - Michigan
# - 07 - Michigan
# - 08 - Pennsylvania
# - 09 - Indiana
# - 10 - Wisconsin
# - 11 - Ohio
# - 12 - Illinois
# - 13 - Nebraska
# - 99 - Esri
# -----------------------------------------
print("\n--------------------- Populating spatial coverage based on bounding box: --------------------\n")

df_csv['State'] = [statedict[row['Code']] if row['Code'] in statedict.keys(
) else statedict[row['Code'][0:2]] for _, row in df_csv.iterrows()]


""" create bounding boxes for csv file """


def format_coordinates(df, identifier):
    # create regular bouding box coordinate pairs and round them to 2 decimal places
    # manually generates the buffering zone
    df = pd.concat([df, df['Bounding Box'].str.split(',', expand=True).astype(float).round(2)], axis=1).rename(
        columns={0: 'minX', 1: 'minY', 2: 'maxX', 3: 'maxY'})

    # check if there exists wrong coordinates and drop them
    coordslist = ['minX', 'minY', 'maxX', 'maxY']
    idlist = []
    for _, row in df.iterrows():
        for coord in coordslist:
            # e.g. [-180.0000,-90.0000,180.0000,90.0000]
            if abs(row[coord]) == 0 or abs(row[coord]) == 180:
                idlist.append(row[identifier])
        if (row.maxX - row.minX) > 10 or (row.maxY - row.minY) > 10:
            idlist.append(row[identifier])

    # create bounding box
    df['Coordinates'] = df.apply(lambda row: box(
        row.minX, row.minY, row.maxX, row.maxY), axis=1)
    df['Roundcoords'] = df.apply(lambda row: ', '.join(
        [str(i) for i in [row.minX, row.minY, row.maxX, row.maxY]]), axis=1)

    # clean up unnecessary columns
    df = df.drop(columns=coordslist).reset_index(drop=True)

    df_clean = df[~df[identifier].isin(idlist)]
    # remove records with wrong coordinates into a new dataframe
    df_wrongcoords = df[df[identifier].isin(idlist)].drop(
        columns=['State', 'Coordinates'])

    return [df_clean, df_wrongcoords]


df_csvlist = format_coordinates(df_csv, 'Slug')
df_clean = df_csvlist[0]
# df_wrongcoords = df_csvlist[1]


""" convert csv and GeoJSON file into dataframe """
gdf_rawdata = gpd.GeoDataFrame(df_clean, geometry=df_clean['Coordinates'])
gdf_rawdata.crs = 'EPSG:4326'


""" split dataframe and convert them into dictionary  """
# -----------------------------------------
# e.g.
# splitdict = {'Minnesota': {'Roundcoords 1': df_1, 'Roundcoords 2': df_2},
#              'Michigan':  {'Roundcoords 3': df_3, ...},
#               ...}
# -----------------------------------------
splitdict = {}
for state in list(gdf_rawdata['State'].unique()):
    gdf_slice = gdf_rawdata[gdf_rawdata['State'] == state]
    if state:
        coordsdict = {}
        for coord in list(gdf_slice['Roundcoords'].unique()):
            coordsdict[coord] = gdf_slice[gdf_slice['Roundcoords']
                                          == coord].drop(columns=['State', 'Roundcoords'])
        splitdict[state] = coordsdict
    else:
        sluglist = gdf_slice['Code'].unique()
        print("Can't find the bounding box file: ", sluglist)


""" perform spatial join on each record """
# -----------------------------------------
# geopandas.sjoin provides the following the criteria used to match rows:
# - intersects
# - within
# - contains
# -----------------------------------------


def split_placename(df, level):
    formatlist = []
    for _, row in df.iterrows():
        # e.g. 'Baltimore County, Baltimore City'
        # --> ['Baltimore County&Maryland', 'Baltimore City&Maryland']
        if row[level] != 'nan':
            placelist = row[level].split(', ')
            formatname = ', '.join([(i + '&' + row['State'])
                                    for i in placelist])
        # e.g. 'nan'
        # --> ['nan']
        else:
            formatname = 'nan'
        formatlist.append(formatname)
    return formatlist


# spatial join: both city and county bounding box files
def city_and_county_sjoin(gdf_rawdata, op, state):
    bboxpath = os.path.join('geojsons', state, f'{state}_City_bbox.json')
    gdf_basemap = gpd.read_file(bboxpath)
    # spatial join
    df_merged = gpd.sjoin(gdf_rawdata, gdf_basemap, op=op, how='left')[
        ['City', 'County', 'State']].astype(str)
    # merge column 'City', 'County' into one column 'op'
    df_merged['City'] = split_placename(df_merged, 'City')
    df_merged['County'] = split_placename(df_merged, 'County')
    df_merged[op] = df_merged[['City', 'County']].agg(
        ', '.join, axis=1).replace('nan, nan', 'nan')
    # convert placename into list
    oplist = df_merged[op].astype(str).values.tolist()
    return oplist


# spatial join: either city or county bounding box file
def city_or_county_sjoin(gdf_rawdata, op, state, level):
    bboxpath = os.path.join('geojsons', state, f'{state}_{level}_bbox.json')
    gdf_basemap = gpd.read_file(bboxpath)
    # spatial join
    df_merged = gpd.sjoin(gdf_rawdata, gdf_basemap, op=op, how='left')[
        [level, 'State']].astype(str)
    # merge column level and 'State' into one column 'op'
    df_merged[op] = df_merged.apply(lambda row: (
        row[level] + '&' + row['State']) if str(row[level]) != 'nan' else 'nan', axis=1)
    # convert placename into list
    oplist = df_merged[op].astype(str).values.tolist()
    return oplist


""" remove duplicates and 'nan' from place name """


def remove_nan(row):
    # e.g. ['nan', 'Minneapolis, Minnesota', 'Hennepin County, Minnesota', 'Hennepin County, Minnesota']
    # remove 'nan' and duplicates from list: ['Minneapolis, Minnesota, 'Hennepin County, Minnesota']
    nonan = list(filter(lambda x: x != 'nan', row))
    nodups = list(set(', '.join(nonan).split(', ')))
    result = [i.replace('&', ', ') for i in nodups]
    return result


""" fetch the proper join bouding box files """
operations = ['intersects', 'within', 'contains']


def spatial_join(gdf_rawdata, state, length):
    oplist = []
    for op in operations:
        bboxpath = os.path.join('geojsons', state, f'{state}_City_bbox.json')

        # Disteict of Columbia doesn't have county boudning box file
        if state == 'District of Columbia':
            columbia = city_or_county_sjoin(gdf_rawdata, op, state, 'City')
            pnamelist = remove_nan(columbia)

        # check if there exists bounding box files
        elif os.path.isfile(bboxpath):
            city_county_state_list = city_and_county_sjoin(
                gdf_rawdata, op, state)
            county_state_list = city_or_county_sjoin(
                gdf_rawdata, op, state, 'County')
            pnamelist = city_county_state_list + county_state_list
            pnamelist = remove_nan(pnamelist)

        # missing bounding box file
        else:
            print('Missing city bounding box file: ', state)
            continue

        oplist.append(pnamelist)
    # duplicate placename list for all rows with the same bounding box
    allopslist = list(repeat(oplist, length))
    # ultimately it returns a dataframe with placename related to matching operation
    ## e.g. dataframe = {'intersects', 'within', 'contains'}
    df_match = pd.DataFrame.from_records(allopslist, columns=operations)
    return df_match


""" merge place names generated by three matching operations to raw data """
mergeddf = []
# loop through splitdict based on key 'State'
for state, gdfdict in splitdict.items():
    # loop through records based on key 'Bounding Box'
    for coord, gdf_split in gdfdict.items():
        length = int(len(gdf_split))
        df_comparison = spatial_join(gdf_split.iloc[[0]], state, length)
        # append dataframe {'intersects', 'within', 'contains'} to raw data
        gdf_sjoin = pd.concat([gdf_split.reset_index(
            drop=True), df_comparison.reset_index(drop=True)], axis=1)
        mergeddf.append(gdf_sjoin)

# merge all dataframes with different bounding boxes into one
gdf_merged = reduce(lambda left, right: left.append(right),
                    mergeddf).reset_index(drop=True)

# replace [''] with None
for op in operations:
    gdf_merged[op] = gdf_merged[op].apply(
        lambda row: None if row == [''] else row)


""" format spatial coverage based on GBL Metadata Template """
# e.g. ['Camden County, New Jersey', 'Delaware County, Pennsylvania', 'Philadelphia County, Pennsylvania']


def format_placename(colname):
    inv_map = {}
    plist = []

    ## {'Camden County': 'New Jersey', 'Delaware County': 'Pennsylvania', 'Philadelphia County': 'Pennsylvania'}
    namedict = dict(item.split(', ') for item in colname)

    ## {'New Jersey': ['Camden County'], 'Pennsylvania': ['Delaware County', 'Philadelphia County']}
    for k, v in namedict.items():
        inv_map[v] = inv_map.get(v, []) + [k]

    ## ['Camden County, New Jersey|New Jersey', 'Delaware County, Pennsylvania|Philadelphia County, Pennsylvania|Pennsylvania']
    for k, v in inv_map.items():
        pname = [elem + ', ' + k for elem in v]
        pname.append(k)
        plist.append('|'.join(pname))

    # Camden County, New Jersey|New Jersey|Delaware County, Pennsylvania|Philadelphia County, Pennsylvania|Pennsylvania
    return '|'.join(plist)


""" select spatial coverage based on operaions """


def populate_placename(df, identifier):
    placenamelist = []
    for _, row in df.iterrows():
        if row['contains'] is None:
            if row['intersects'] is None:
                placename = ''
            elif row['within'] is None:
                placename = format_placename(row['intersects'])
            else:
                placename = format_placename(row['within'])
        else:
            placename = format_placename(row['contains'])
        placenamelist.append(placename)
    df['Spatial Coverage'] = placenamelist
    return df.drop(columns=['intersects', 'within', 'contains', 'Coordinates', 'geometry'])


df_bbox = populate_placename(gdf_merged, 'Slug')


""" write to csv file """
# check if there exists data portal from Esri
if len(df_esri):
    df_esri['Spatial Coverage'] = 'United States'

dflist = [df_esri, df_bbox]
df_final = pd.concat(filter(len, dflist), ignore_index=True)

df_final.to_csv(newItemsReport, index=False)
print("\n--------------------- Congrats! ╰(￣▽￣)╯ --------------------\n")