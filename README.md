# DCAT Maintenance
This repository is for tracking the BTAA GDP harvesting activities from DCAT data portals. These portal platforms include ArcGIS Open Data Portals and Socrata. To keep BTAA Geoportal search tool from returning broken links and to capture newly added resources due to the instability of data source, it is necessary to re-check data portals frequently. 

The scripts can also be used for any site with DCAT enabled, including some DKAN and CKAN sites. However, an adjustment to the names of the harvested metadata fields may be required first.



## Python Scripts
- ### harvest.py
  
    This script will compare previously harvested JSON files with a hosted one. It will harvest a full copy of the current JSON files based on data portals stored in **arcPortals.csv** and produce three CSV reports for *NEW*, *DELETED* items and *PORTAL STATUS*. Also, it will populate Spatial Coverage based on bounding box and drop all the records with wrong bounding box or invalid download link. 

  > Remember to change the file path when using MAC or Linux operating system.
  
- ### harvest.ipynb
  
    This script should be opened with Anaconda3 Jupyter Notebook. It is a Jupyter Notebook version of **harvest.py** but with Markdown cells. 
    
- ### geojsonScripts

    This folder holds all the scripts generating GeoJSONs for further spatial join operation. 

    - **county_boundary.ipynb**
    - **city_boundary.ipynb**
    - **county_bbox.ipynb**
    - **city_bbox.ipynb**
    - **merge_geojsons.ipynb**


​	If the target state(s) hasn't included city or county bounding box files, you may need to 

1. download county and city boundary files (GeoJSON or Shapefile) online
2. run `city_boundary.ipynb` or `county_boundary.ipynb` to create boundary GeoJSONs first
   - if there exists regional data portals, you may need to run `merge_geojsons.ipynb` to merge them together
   - Note that manual changes are required for `city_boundary.ipynb` based on attributes. 
3. run `city_bbox.ipynb` or `county_bbox.ipynb` to create bounding box GeoJSONs



## CSV Lists
These list the current and historical portal URL. The scripts above that harvest from hosted JSONS require accompanying lists of where to harvest from. These are referenced in the section of the script commented as *"Manual items to change!"*

- ### arcPortals.csv

    This file is supposed to have five columns *(portalName, URL, provenance, publisher, and spatialCoverage)* with details about ESRI open data portals to be checked for new records.



## Folders

- ### jsons

    This holds all harvested JSONs with the naming convention of **portalName_YYYYMMDD.json**. Once running the python scripts, newly generated JSON files need to be uploaded. The date in the latest JSON filename is used to define *PreviousActionDate*. These are referenced in the section of the script commented as *"Manual items to change!"*

- ### geojsons

    This holds all the bounding box and boundary JSONs for states that have data portals. 

    -  **State**
      - **State_County_boundaries.json**
      - **State_City_boundaries.json**
      - **State_County_bbox.json**
      - **State_City_bbox.json**
    -  **portalCode -- regional portals** 
       - **portalCode_County_bbox.json**
       - **portalCode_City_bbox.json**

- ### reports
  
    This holds all CSV reports of new and deleted items and portal status reports :
    - **allNewItems_YYYYMMDD.csv**
    - **allDeletedItems_YYYYMMDD.csv**
    - **portal_status_report_YYYYMMDD.csv**
    
    Once running the python scripts, newly generated CSV files need to be uploaded. Like JSONs, the date in the latest CSV filename is used to define *PreviousActionDate*. These are referenced in the section of the script commented as *"Manual items to change!"*
    
- ### socrata

    This is for tracking metadata records harvesting from portals in the Socrata schema. And the folder structure is similar to the main directory. 

- ### olderScriptsAndWorkingCopies

    This holds every version of python scripts and other working copies. 
    
- ### geojsonScripts



## Something you may want to know

#### Why create county bounding box GeoJSONs?

A Bounding box is typically described as an array of two coordinate pairs: **SW** (the minimum longitude and latitude) and **NE** (the maximum longitude and latitude). Therefore, the rectangle area it represents always exceeds the real one and overlaps each other. It may cause problems especially for features sharing the same border like counties. 

If we spatial join the bounding box of records with accurate county boundaries, there's a great chance of returning place names which actually have no spatial relationship. In order to improve the accuracy, we need to use regular rectangle area for both join features and target features. 

#### How to determine spatial coverage?

<a href='https://geopandas.org/reference/geopandas.sjoin.html'>`geopandas.sjoin`</a> provides three match options: **intersects**, **contains** and **within**. The flow chart below demonstrates the decision-making process:

<img src="https://user-images.githubusercontent.com/66186715/107158001-e2e4ab80-694c-11eb-924f-d04937b8176d.png" width="700" />