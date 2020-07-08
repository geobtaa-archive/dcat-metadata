# DCAT Maintenance
This repository is for tracking the BTAA GDP harvesting activities from DCAT data portals. These portal platforms include ArcGIS Open Data Portals and Socrata. To keep BTAA Geoportal search tool from returning broken links and to capture newly added resources due to the instability of data source, it is necessary to re-check data portals frequently. 

The scripts can also be used for any site with DCAT enabled, including some DKAN and CKAN sites. However, an adjustment to the names of the harvested metadata fields may be required first.

## Python Scripts
- **JSONcomparison.py | JSONcomparison_MAC.py | SocrataJSONComparison.py** <br>
    
    This script will compare previously harvested JSON files with a hosted one. It will harvest a full copy of the current JSON files based on data portals stored in **arcPortals.csv** and produce three CSV reports for *NEW*, *DELETED* items and *PORTAL STATUS*.

- **DCAT_harvesting_full_Geo4Lib.ipynb** <br>
    
    This script should be opened with Anaconda3 Jupyter Notebook. It is a Jupyter Notebook version of **JSONcomparison.py** but with Markdown cells. 

## CSV Lists
These list the current and historical portal URL. The scripts above that harvest from hosted JSONS require accompanying lists of where to harvest from. These are referenced in the section of the script commented as *"Manual items to change!"*

- **arcPortals.csv**

    This file is supposed to have five columns *(portalName, URL, provenance, publisher, and spatialCoverage)* with details about ESRI open data portals to be checked for new records.

- **non-workingarcportals.csv**

    This file document the portals which are no longer harvested. 


## Folders

- **Jsons**

    This holds all harvested JSONs with the naming convention of **portalName_YYYYMMDD.json**. Once running the python scripts, newly generated JSON files need to be uploaded. The date in the latest JSON filename is used to define *PreviousActionDate*. These are referenced in the section of the script commented as *"Manual items to change!"*

- **Reports**
    
    This holds all CSV reports of new and deleted items and portal status reports :
    - **allNewItems_YYYYMMDD.csv**
    - **allDeletedItems_YYYYMMDD.csv**
    - **portal_status_report_YYYYMMDD.csv**
    
    Once running the python scripts, newly generated CSV files need to be uploaded. Like JSONs, the date in the latest CSV filename is used to define *PreviousActionDate*. These are referenced in the section of the script commented as *"Manual items to change!"*


