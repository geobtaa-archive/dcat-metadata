# DCAT Maintenance
This repository is for tracking the BTAA GDP harvesting activities from DCAT data portals. These portal platforms include ArcGIS Open Data Portals and Socrata. To keep BTAA Geoportal search tool from returning broken links and to capture newly added resources due to the instability of data source, it is necessary to re-check data portals frequently. 

The scripts can also be used for any site with DCAT enabled, including some DKAN and CKAN sites. However, an adjustment to the names of the harvested metadata fields may be required first.



## Environment Setup

We We will be using **Anaconda 3** to edit and run scripts. Information on Anaconda installation can be found [here](https://docs.anaconda.com/anaconda/install/).  All packages available for 64-bit Windows with Python 3.7 in the Anaconda can be found [here](https://docs.anaconda.com/anaconda/packages/py3.7_win-64/). Please note that all scripts are running on Python 3 (**3.7.6**).

Here are all dependencies needed to be installed properly: 

- [geopandas](https://geopandas.org/getting_started/install.html) [Version: 0.7.0]

- [shapely](https://pypi.org/project/Shapely/) [Version: 1.7.0]

- [requests](https://requests.readthedocs.io/en/master/user/install/#install) [Version: 2.22.0]

- [numpy](https://numpy.org/install/) [Version: 1.18.1]



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



## Handling URL Errors

### Error Summary

| Error                        | Access Landing Page? | Access Download Link or ImageServer? | Solution                       |
| ---------------------------- | :------------------: | :----------------------------------: | ------------------------------ |
| 404 - Not Found              |          X           |                  X                   | Drop this record               |
| 500 - Internal Server Error  |          √           |                  X                   | Only keep the landing page URL |
| Wrong File Type              |          √           |                  √                   | Only keep the landing page URL |
| Could not access ImageServer |          √           |                  X                   | Only keep the landing page URL |
| Read Timeout                 |      It depends      |              It depends              | Manually check it              |



### More Explanations Based on Each Error

1. **404 - Not Found**

   - **Reason**

     We can’t access either the landing page or download link. 

   - **Solution** 

     Technically speaking, it’s a broken link, so just drop it. 

2. **500 - Internal Server Error**

   - **Reason** 

     We can access the landing page, but there’s something wrong with the download link on the server side.

   - **Solution** 

     Provide the data source without the download link. Let users decide if they want to download other types of data.

3. **Wrong File Type** -- [Vector Data] *Not a shapefile*

   - **Reason** 

     When querying the metadata, the script will treat any link ended with `.zip` as a shapefile. But, some of them are not shapefiles. 

   - **Solution** 

     Provide the data source without the download link. Let users decide if they want to download other types of data.

4. **Could not access ImageServer**  -- [Imagery Data] 

   - **Reason** 

     Currently, all TIFF data would throw this error. Here’s Esri’s [explanation](https://support.esri.com/en/technical-article/000012620). 

   - **Solution** 

     Provide the data source without the download link. Let users decide if they want to download other types of data.

5. **Read Timeout**

   - **Reason** 

     This is the most ambiguous one. In order to improve the efficiency of web scraping, **`timeout`** is necessary to prevent the script waiting forever. If it does not get       a response within a particular time period, just move to the next one. Failure to do so can cause the program to hang indefinitely. 

     The servers can become slow and unresponsive for many reasons. One reason might be the **gigantic file size**. According to the Python library [**Requests**](https://requests.readthedocs.io/en/master/user/advanced/), when making a request, the body of the response (the entire file) is downloaded immediately. But                  **`timeout`** is not a time limit on the *entire response download*; rather, an exception is raised if the server has not issued a response for **`timeout`** seconds (        more precisely, this is the time before the server sends the first byte). 

   - **Solution**

     Try setting **`timeout`** as **3 seconds** first, and push all the records with timeout error into a new list. Then increase **`timeout`** up to **10 seconds** and loop      through the list, most of the links will get a response. If still get some unresponsive ones, manually check it in case accidently delete any valid records. Those            records will be flagged in the “**Title**” column using something like “*Manually check it!*”.



## Obtain File Size

The default content length is in **Byte**, currently it has been converted into **MB** and rounded to 4 decimal places.



## Something you may want to know

#### Why create county bounding box GeoJSONs?

A Bounding box is typically described as an array of two coordinate pairs: **SW** (the minimum longitude and latitude) and **NE** (the maximum longitude and latitude). Therefore, the rectangle area it represents always exceeds the real one and overlaps each other. It may cause problems especially for features sharing the same border like counties. 

If we spatial join the bounding box of records with accurate county boundaries, there's a great chance of returning place names which actually have no spatial relationship. In order to improve the accuracy, we need to use regular rectangle area for both join features and target features. 

#### How to determine spatial coverage?

<a href='https://geopandas.org/reference/geopandas.sjoin.html'>`geopandas.sjoin`</a> provides three match options: **intersects**, **contains** and **within**. The flow chart below demonstrates the decision-making process:

<img src="https://user-images.githubusercontent.com/66186715/107158001-e2e4ab80-694c-11eb-924f-d04937b8176d.png" width="700" />