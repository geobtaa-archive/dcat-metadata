# DCAT Maintenance
This repository is for tracking the BTAA GDP  harvesting activities from DCAT data portals. These portal platforms include ArcGIS Open Data Portals and Socrata.
The scripts can also be used for any site with DCAT enabled, including some DKAN and CKAN sites.  However, an adjustment to the names of the harvested metadata fields may be required first.

## Python Scripts
* ConvertJson2CsvFromLocalFile.py
This script will transform a local DCAT JSON file into a CSV.

* Json2Csv_Py3.ipynb should be opened with Anaconda3 Jupyter Notebook.  Script is in-progress user input version of the Python 2.x Json2Csv.py script.  Further Markdown within Jupyter Notebook cells.

* Socrata2Csv.py
These scripts will harvest full hosted DCAT JSON files and convert them to CSV

* JSON_comparison.py
* SocrataJSON_comparison.py
This script will compare previously harvested JSON files with a hosted one. It will harvest a full copy of the current JSON and produce CSV reports for NEW and DELETED items.

* testJSON
This script is for testing harvesting problems if the JSON is not being recognized

## CSV Lists
These list the collection code and the portal URL. The scripts that harvest from hosted JSONS require accompanying lists of where to harvest from. These are referenced in the section of the script commented as "Manual items to change!"


* ArcPortals.csv
* Mn Portals.csv
* SocrataPortals.csv
* temp.csv - useful for adding one or two portal addresses to harvest at a time.


## Folders

### Jsons
This holds all harvested Jsons with the naming convention of collectioncode_YYYYMMDD.json

### Reports
This holds all CSV reports of new and deleted items.



### reports.log
This is a running log of harvesting activities. Must be manually saved from operating system default log location.
