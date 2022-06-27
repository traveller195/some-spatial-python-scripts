#here are just all the often used libraries and packages, I usually import as default
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

import copy

# nominatim geocoder
# partly source code from see # https://www.w3resource.com/python-exercises/geopy/python-geopy-nominatim_api-exercise-4.php

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="geoapiExercises")

# input parameter
city = 'city_name'


# import data

# encoding 'latin-1' instead of utf-8. it was not working first.
daten_csv = gpd.read_file(r'path/to/adress_list.csv', encoding='latin-1')

print(daten_csv.head())
daten_csv.info()


# new fields for lat and lon
daten_csv['lat'] = None
daten_csv['lon'] = None

daten_csv['status'] = None

# geocode lat and lon for each adress

for j, row in daten_csv.iterrows():
    str_adress = ''
    str_adress = daten_csv.loc[j, 'StrName'] + ' ' +  daten_csv.loc[j, 'HsNr'] + ' ' + city
    location = geolocator.geocode(str_adress)

    print(location)
    if location == None:
        daten_csv.at[j, 'status'] = 'no_coordinates'

    if location != None:
        daten_csv.at[j, 'status'] = 'succesful'
        # write coordinates into cols
        daten_csv.at[j, 'lat'] = location.latitude
        daten_csv.at[j, 'lon'] = location.longitude    


    del str_adress, location

print(daten_csv.head())

# selection of only succesful geocoded adresses


geocoded = gpd.GeoDataFrame(daten_csv[daten_csv['status']== 'succesful'], geometry=gpd.points_from_xy(daten_csv[daten_csv['status']== 'succesful'].lon, daten_csv[daten_csv['status']== 'succesful'].lat))

geocoded.to_file("/code/output/" + str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + "_geocoded_data.geojson", driver='GeoJSON', encoding='utf-8')


#geolocator = Nominatim(user_agent="geoapiExercises")
#ladd1 = "Weberplatz 1 Dresden"
#print("Location address:",ladd1)
#location = geolocator.geocode(ladd1)
#print("Latitude and Longitude of the said address:")
#print((location.latitude, location.longitude))
#ladd2 = "380 New York St, Redlands, CA 92373"
#print("\nLocation address:",ladd2)
#location = geolocator.geocode(ladd2)
#print("Latitude and Longitude of the said address:")
#print((location.latitude, location.longitude))
#ladd3 = "1600 Pennsylvania Avenue NW"
#print("\nLocation address:",ladd3)
#location = geolocator.geocode(ladd3)
#print("Latitude and Longitude of the said address:")
#print((location.latitude, location.longitude))