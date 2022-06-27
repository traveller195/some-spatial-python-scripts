import pandas as pd
import geopandas as gpd 
from shapely.geometry import Point, Polygon, LineString
import fiona

import json


# Aufgabe: die extrahierten Daten von OSM zu Sehenswuerdigkeiten mergen
# alles fuer HD und DD in einem finalen Datensatz bereitstellen

# input Dateien im GeoJSON Format durch-browsen und per if Entscheidung abhandeln
# bei Linien und Flaechen ein Centroid bilden

# in Dresden die staedtischen Daten zu Sehenswuerdigkeiten puffern und pruefen, ob OSM Punkt darin liegt oder nicht

# was brauche ich an Geo-Befehlen? project/ projections, centroid, buffer, intersect/ point in polygon

# dabei ALLES in EPSG 3035 machen, wegen puffer in Metern!!!






newdata = gpd.GeoDataFrame()

# create column for geometry
newdata['geometry'] = None

newdata['id'] = None # muss noch ein inkrement / serial werden

newdata['id_source'] = None # entspricht 'id' und 'number'
newdata['type'] = None

newdata['name'] = None
newdata['source'] = None
newdata['dataset'] = None
newdata['city'] = None # kann hier auch noch mit Dresden/Heidelberg gefuellt werden

newdata.crs = "EPSG:4326"


# Daten importieren

# 2020 June 04: for Dresden use open data Dresden + OSM fountain
# 2020 June 04: for Heidelberg use OSM incl. fountain




daten_dd_osm_beachvolleyball = gpd.read_file(r'volleyball_merge/Rohdaten/osm_dd_sport_beachvolleyball.geojson')

daten_hd_osm_beachvolleyball = gpd.read_file(r'volleyball_merge/Rohdaten/osm_hd_sport_beachvolleyball.geojson')


daten_dd_osm_volleyball = gpd.read_file(r'volleyball_merge/Rohdaten/osm_dd_sport_volleyball.geojson')

daten_hd_osm_volleyball = gpd.read_file(r'volleyball_merge/Rohdaten/osm_hd_sport_volleyball.geojson')





print(daten_dd_osm_beachvolleyball.info())


print(daten_dd_osm_beachvolleyball.head())

# select distinct 'id' - quasi ein group by 'id'
#listID = daten_rnv['id'].unique().tolist()


# ++++++++++++++++++++++++++++++++++++++++++++
# project to WGS84 / EPSG 4326



# ++++++++++++++++++++++++++++++++++++++++++++
# create CENTROID: polygon and line to point

for i, row in daten_dd_osm_beachvolleyball.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_dd_osm_beachvolleyball.at[i, 'geometry'] = centroid
    del centroid

for i, row in daten_hd_osm_beachvolleyball.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_hd_osm_beachvolleyball.at[i, 'geometry'] = centroid
    del centroid



for i, row in daten_dd_osm_volleyball.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_dd_osm_volleyball.at[i, 'geometry'] = centroid
    del centroid

for i, row in daten_hd_osm_volleyball.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_hd_osm_volleyball.at[i, 'geometry'] = centroid
    del centroid








# ++++++++++++ BEACH VOLLEYBALL ++++++++++++++++++
# add OSM dresden (dd) fountain
for i in range(0, len(daten_dd_osm_beachvolleyball)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_osm_beachvolleyball.loc[i,'id'], 'type':'Beachvolleyball', 'name':daten_dd_osm_beachvolleyball.loc[i,'name'], 'source':'OSM', 'dataset':'sport=beachvolleyball', 'city':'Dresden', 'geometry':daten_dd_osm_beachvolleyball.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# add OSM heidelberg (hd) fountain
for i in range(0, len(daten_hd_osm_beachvolleyball)):

    new_row = {'id': len(newdata), 'id_source': daten_hd_osm_beachvolleyball.loc[i,'id'], 'type':'Beachvolleyball', 'name':daten_hd_osm_beachvolleyball.loc[i,'name'], 'source':'OSM', 'dataset':'sport=beachvolleyball', 'city':'Heidelberg', 'geometry':daten_hd_osm_beachvolleyball.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)






# ++++++++++++ VOLLEYBALL ++++++++++++++++++
# add OSM dresden (dd) memorial
for i in range(0, len(daten_dd_osm_volleyball)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_osm_volleyball.loc[i,'id'], 'type':'Volleyball', 'name':daten_dd_osm_volleyball.loc[i,'name'], 'source':'OSM', 'dataset':'sport=volleyball', 'city':'Dresden', 'geometry':daten_dd_osm_volleyball.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# add OSM heidelberg (hd) memorial
for i in range(0, len(daten_hd_osm_volleyball)):

    # ausgeklammert, da nicht vorhanden: daten_hd_osm_volleyball.loc[i,'name']

    new_row = {'id': len(newdata), 'id_source': daten_hd_osm_volleyball.loc[i,'id'], 'type':'Volleyball', 'name':'', 'source':'OSM', 'dataset':'sport=volleyball', 'city':'Heidelberg', 'geometry':daten_hd_osm_volleyball.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)





print(newdata.head())








#Exportiere die Daten als Shapefile EPSG 4326

#newdata['id'].astype('int') # to integer
newdata['id'] = pd.to_numeric(newdata['id'])

newdata.to_file("volleyball_merge/FINAL_voll_v2.shp")
newdata.to_file("volleyball_merge/FINAL_voll_v2.geojson", driver='GeoJSON', encoding='utf-8')