import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString

#Spatial Join
from geopandas.tools import sjoin

import shapely
import fiona
import pyproj       # for transforming shapely geometry

#import json

#from random import randint

#import time
#from time import gmtime, strftime

import numpy as np
#import matplotlib 
#import matplotlib.pyplot as plt
#import matplotlib.dates as mdates

#import os
#import sys
#import math
#import datetime


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++ data preparation before this python script ++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# convert Excel sheet (.xsl / .xslx) into .csv (with MS Excel)
# open .csv file with notepad++
# check data structure
# remove manually header and footer rows, which are not data rows!
# keep only first row for attribut names and all further data rows


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ data import +++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# care about semicolon seperator and quoting in the data
# for key attributes like the german 'AGS' read as data type 'object' to keep leading zero !
# care about encoding: 'utf-8' or 'latin3' for example

data_semantics.read_csv(r'folder/data_semantics.csv', encoding='latin3', engine ='python', sep=';', escapechar="\\", dtype={'AGS': 'object'})
data_semantics.info()
print(data_semantics.head())


# read geometry data (e.g. polygons)
# from ESRI Shapefile, GeoJSON or also PostgreSQL/ PostGIS-database
data_geometries = gpd.read_file(r'folder/data_polygons.shp', encoding='utf-8')
data_geometries.info()
print(data_geometries.head())

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ data preparation ++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# care about the proper spatial reference system / CRS

# reproject
data_geometries = data_geometries.to_crs("EPSG:4326")

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ merge attribut  +++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# create attribut for Merging / JOIN if not existing

data_semantics['nummer'] = None
data_semantics['name'] = None



data_semantics[['nummer', 'name']] = data_semantics['Stadtteile'].str.split(r' / ', n=1,  expand=True) #n=1 only one split

# delete space characters, to get equal values for merge attribut

data_semantics['nummer'] = data_semantics['nummer'].str.strip()
data_semantics['name'] = data_semantics['name'].str.strip()

print(data_semantics.head())

# ****************************************************************************************************************************************************
# if there is the need to process the german general municipality code 'AGS', then maybe like this:
# dealing with leading zeros... on different admin level of the administration in Germany


# data preparation for destatis data
mask_ags_2 = (data_destatis['AGS'].str.len() == 2)
ags_2 = data_destatis.loc[mask_ags_2]
print (ags_2)
# add 6 zeros as a suffix
ags_2['AGS'] = ags_2['AGS'].apply(lambda x: "{}{}".format(x, '000000'))
print (ags_2)

# take all municipalities (having AGS length of 8 chars) and take AGS length5 in order to add 3 zeros in the end (to gain AGS 8)
mask_ags_5 = (data_destatis['AGS'].str.len() == 5)
ags_5 = data_destatis.loc[mask_ags_5]
print (ags_5)

# add 3 zeros as a suffix
ags_5['AGS'] = ags_5['AGS'].apply(lambda x: "{}{}".format(x, '000'))
print (ags_5)

mask_ags_8 = (data_destatis['AGS'].str.len() == 8)
ags_8 = data_destatis.loc[mask_ags_8]
print (ags_8)
ags_8.info()

#append dataframe to other dataframe
ags_8 = ags_8.append(ags_5)
ags_8 = ags_8.append(ags_2)

print(ags_8)
ags_8.info()


# replace Point or Minus with zero
ags_8 = ags_8.replace({'Insg_Insg': {'.': 0, '-': 0}}, regex=True)
ags_8['Insg_Insg'] = ags_8['Insg_Insg'].astype(str).replace('-', '0', inplace=True)

ags_8.loc[ags_8.Insg_Insg == '.', 'Insg_Insg'] = 0
ags_8.loc[ags_8.Insg_Insg == '-', 'Insg_Insg'] = 0

ags_8.loc[ags_8.Insg_male == '.', 'Insg_male'] = 0
ags_8.loc[ags_8.Insg_male == '-', 'Insg_male'] = 0

ags_8.loc[ags_8.Insg_female == '.', 'Insg_female'] = 0
ags_8.loc[ags_8.Insg_female == '-', 'Insg_female'] = 0

ags_8.loc[ags_8.Ausl_insg == '.', 'Ausl_insg'] = 0
ags_8.loc[ags_8.Ausl_insg == '-', 'Ausl_insg'] = 0

ags_8.loc[ags_8.Ausl_male == '.', 'Ausl_male'] = 0
ags_8.loc[ags_8.Ausl_male == '-', 'Ausl_male'] = 0

ags_8.loc[ags_8.Ausl_female == '.', 'Ausl_female'] = 0
ags_8.loc[ags_8.Ausl_female == '-', 'Ausl_female'] = 0



#ags_8['Insg_male'] = ags_8['Insg_male'].astype(str).replace('.', '0', inplace=True)
#ags_8['Insg_male'] = ags_8['Insg_male'].astype(str).replace('-', '0', inplace=True)

# ****************************************************************************************************************************************************

# make shure, that all attributes with numbers have datatyp 'numerich'
# this is important for further classification / visualization in QGIS for example...

#data type back to numeric
data_semantics["2006"] = pd.to_numeric(data_semantics["2006"])
data_semantics["2007"] = pd.to_numeric(data_semantics["2007"])
data_semantics["2008"] = pd.to_numeric(data_semantics["2008"])
data_semantics["2009"] = pd.to_numeric(data_semantics["2009"])
data_semantics["2010"] = pd.to_numeric(data_semantics["2010"])
data_semantics["2011"] = pd.to_numeric(data_semantics["2011"])
data_semantics["2012"] = pd.to_numeric(data_semantics["2012"])
data_semantics["2013"] = pd.to_numeric(data_semantics["2013"])
data_semantics["2014"] = pd.to_numeric(data_semantics["2014"])
data_semantics["2015"] = pd.to_numeric(data_semantics["2015"])
data_semantics["2016"] = pd.to_numeric(data_semantics["2016"])
data_semantics["2017"] = pd.to_numeric(data_semantics["2017"])
data_semantics["2018"] = pd.to_numeric(data_semantics["2018"])
data_semantics["2019"] = pd.to_numeric(data_semantics["2019"])

data_semantics["nummer"] = pd.to_numeric(data_semantics["nummer"])

data_geometries["nummer"] = pd.to_numeric(data_geometries["nummer"])

print(data_semantics)

#++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ data merge +++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++

# JOIN on attribute 'nummer'
data_merge = data_geometries.merge(data_semantics, on='nummer')
data_merge.info()
print(data_merge.head())


#++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++ post processing++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++


# rename some columns (less 8 chars)
data_merge = data_merge.rename(columns={'Raumeinheit': 'RAUM_EINH'})


data_merge.info()
print(data_merge.head())

# reduce number of columns, only relevenat columns will be kept in output file

#data_output = data_merge[["AGS", "GEN", "BEZ", "BEM", "geometry", "Insg_Insg", "Insg_male", "Insg_female", "Ausl_insg", "Ausl_male", "Ausl_female"]]


# also bringt columns / attributes in the proper order...




data_output = data_merge

data_output.info()
print(data_output.head())




#++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++++++++++++++++ save merged data ++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++
data_output.to_file("/f/output/merged_data.geojson", driver='GeoJSON', encoding='utf-8')

data_output.to_file("/code/output/merged_data.shp")