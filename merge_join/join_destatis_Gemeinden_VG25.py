import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString

#Spatial Join
from geopandas.tools import sjoin

import shapely
import fiona
import pyproj       # for transforming shapely geometry

import json

from random import randint

import time
from time import gmtime, strftime

import numpy as np
import matplotlib 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import os
import sys
import math
import datetime


# ++++++++++++++++++++++ data import +++++++++++++++++++++
# to read destatis data, care about semicolon seperator and quoting in the data
# AGS read as data type 'object' to keep leading zero !

data_destatis = pd.read_csv(r'import/13111-01-03-5Gem2020_bereinigt.csv', encoding='latin3', engine ='python', sep=';', escapechar="\\", dtype={'AGS': 'object'})
data_destatis.info()
print(data_destatis.head())


# read municipality data of 2019 for Germany
data_municipality = gpd.read_file(r'import/VG_25_Gemeinden_2020/VG25_GEM.shp', encoding='utf-8')
data_municipality.info()
print(data_municipality.head())


# ++++++++++++++++++++++ data preparation +++++++++++++++++

# rename col 'Kennziffer' into 'AGS', for merging/ join data sets
# data_inkar = data_inkar.rename(columns={'Kennziffer': 'AGS'})

# data_inkar.info()

#reproject to WGS 84/ EPSG: 4326
# data_municipality = data_municipality.to_crs("EPSG:4326")




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


# delete leading space in 'Gemeinde'

ags_8['Gemeinde'] = ags_8['Gemeinde'].str.strip()
print(ags_8)

# replace Point or Minus with zero
#ags_8 = ags_8.replace({'Insg_Insg': {'.': 0, '-': 0}}, regex=True)
#ags_8['Insg_Insg'] = ags_8['Insg_Insg'].astype(str).replace('-', '0', inplace=True)

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

#data type back to numeric
ags_8["Insg_Insg"] = pd.to_numeric(ags_8["Insg_Insg"])
ags_8["Insg_male"] = pd.to_numeric(ags_8["Insg_male"])
ags_8["Insg_female"] = pd.to_numeric(ags_8["Insg_female"])
ags_8["Ausl_insg"] = pd.to_numeric(ags_8["Ausl_insg"])
ags_8["Ausl_male"] = pd.to_numeric(ags_8["Ausl_male"])
ags_8["Ausl_female"] = pd.to_numeric(ags_8["Ausl_female"])



print(ags_8)

# ++++++++++++++++++++++ data merge +++++++++++++++++
# JOIN on attribute 'AGS'
data_merge = data_municipality.merge(ags_8, on='AGS')
data_merge.info()
print(data_merge.head())

# +++++++++++++++++++++ some final adaptions of data structure ++++++++++++++++++++++

# rename some columns (less 8 chars)
#data_merge = data_merge.rename(columns={'Raumeinheit': 'RAUM_EINH'})


data_merge.info()
print(data_merge.head())

# reduce number of columns, only relevenat columns will be kept in output file

data_output = data_merge[["AGS", "GEN", "BEZ", "BEM", "geometry", "Insg_Insg", "Insg_male", "Insg_female", "Ausl_insg", "Ausl_male", "Ausl_female"]]

data_output.info()
print(data_output.head())


# ++++++++++++++++++++++++ save output ++++++++++++++++++++++++++
data_output.to_file("/code/output/VG25_GEMEINDEN_2020_destatis_SV_beschaeftigte_2020.geojson", driver='GeoJSON', encoding='utf-8')

data_output.to_file("/code/output/VG25_GEMEINDEN_2020_destatis_SV_beschaeftigte_2020.shp")