import pandas as pd
import geopandas as gpd 
from shapely.geometry import Point, Polygon, LineString
import fiona

import json


# Aufgabe: die Haltestellen von VVO (kilian koeltzsch) und vom RNV fuer Heidelberg mergen
# die Heidelberger Daten muessen noch nach ihrer id gruppiert werden, und centroid der Geometrien

# Attribut name sollte genutzt werden
# Attrobit 'source' sollte als String vergeben werden
# neue ID als inkrement in GPD , die alten Ids als 'id_old'



newdata = gpd.GeoDataFrame()

# create column for geometry
newdata['geometry'] = None

newdata['id'] = None # muss noch ein inkrement / serial werden


newdata['id_from_source'] = None # entspricht 'id' und 'number'

newdata['name'] = None
newdata['source'] = None
newdata['sub_id'] = None
newdata['nameWithCity'] = None
newdata['city'] = None # kann hier auch noch mit Dresden/Heidelberg gefuellt werden
newdata['tariffZone1'] = None
newdata['tariffZone2'] = None
newdata['tariffZone3'] = None




newdata.crs = "EPSG:4326"


# Daten importieren

#daten_rnv = gpd.GeoDataFrame()
#daten_vvo = gpd.GeoDataFrame()

daten_rnv = gpd.read_file(r'haltestellen_merge/haltestellen_153_edit.shp')
daten_vvo = gpd.read_file(r'haltestellen_merge/stations.json')

print(daten_rnv.info())
print(daten_vvo.info())


print(daten_rnv.head())
print(daten_vvo.head())

# select distinct 'id' - quasi ein group by 'id'
listID = daten_rnv['id'].unique().tolist()

# centroid der mehreren Punkte durch Mittelwert Berechnung kreieren
for i in range(0, len(listID)):
    listSelect = daten_rnv.query('id == "' + listID[i] + '"')

    sum_lat = 0.0
    sum_lon = 0.0
    for j in range(0, len(listSelect)):
        point = listSelect.iloc[j,3] # select 3rd columns = geometry
        
        sum_lat += point.y
        sum_lon += point.x

    lat = sum_lat / len(listSelect)
    lon = sum_lon / len(listSelect)

    newPoint = Point(lon, lat)

    new_row = {'id': len(newdata), 'id_from_source': listSelect.iloc[0,0], 'name':listSelect.iloc[0,1], 'source':'RNV', 'sub_id':listSelect.iloc[0,2], 'city':'Heidelberg', 'geometry':newPoint}
    newdata = newdata.append(new_row, ignore_index=True)


print(newdata.head())

for i in range(0, len(daten_vvo)):

    # insert data of VVO
    new_row = {'id': len(newdata), 'id_from_source': daten_vvo.iloc[i,0], 'name':daten_vvo.iloc[i,2], 'source':'VVO_Kilian_Koeltzsch', 'nameWithCity':daten_vvo.iloc[i,1], 'city':daten_vvo.iloc[i,3], 'geometry':daten_vvo.iloc[i,7], 'tariffZone1':daten_vvo.iloc[i,4], 'tariffZone2':daten_vvo.iloc[i,5], 'tariffZone3':daten_vvo.iloc[i,6]}
    newdata = newdata.append(new_row, ignore_index=True)


#Exportiere die Daten als Shapefile EPSG 4326

#newdata['id'].astype('int') # to integer
newdata['id'] = pd.to_numeric(newdata['id'])

newdata.to_file("haltestellen_merge/FINAL_haltestellen_v1.shp")