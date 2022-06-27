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

daten_dd_city = gpd.read_file(r'swdk/Rohdaten/opendata_dresden/sehenswuerdigkeiten.shp')


daten_dd_osm_fountain = gpd.read_file(r'swdk/Rohdaten/OSM/osm_dd_amenity_fountain.geojson')

daten_hd_osm_fountain = gpd.read_file(r'swdk/Rohdaten/OSM/osm_hd_amenity_fountain.geojson')


daten_dd_osm_memorial = gpd.read_file(r'swdk/Rohdaten/OSM/osm_dd_historic_memorial.geojson')

daten_hd_osm_memorial = gpd.read_file(r'swdk/Rohdaten/OSM/osm_hd_historic_memorial.geojson')


daten_dd_osm_artwork = gpd.read_file(r'swdk/Rohdaten/OSM/osm_dd_tourism_artwork.geojson')

daten_hd_osm_artwork = gpd.read_file(r'swdk/Rohdaten/OSM/osm_hd_tourism_artwork.geojson')


daten_dd_osm_attraction = gpd.read_file(r'swdk/Rohdaten/OSM/osm_dd_tourism_attraction.geojson')

daten_hd_osm_attraction = gpd.read_file(r'swdk/Rohdaten/OSM/osm_hd_tourism_attraction.geojson')


print(daten_dd_city.info())
print(daten_dd_osm_fountain.info())


print(daten_dd_city.head())
print(daten_dd_osm_fountain.head())

# select distinct 'id' - quasi ein group by 'id'
#listID = daten_rnv['id'].unique().tolist()


# ++++++++++++++++++++++++++++++++++++++++++++
# project to WGS84 / EPSG 4326
daten_dd_city_4326 = daten_dd_city.to_crs("EPSG:4326")


# ++++++++++++++++++++++++++++++++++++++++++++
# create CENTROID: polygon and line to point

for i, row in daten_dd_osm_fountain.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_dd_osm_fountain.at[i, 'geometry'] = centroid
    del centroid

for i, row in daten_hd_osm_fountain.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_hd_osm_fountain.at[i, 'geometry'] = centroid
    del centroid



for i, row in daten_dd_osm_memorial.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_dd_osm_memorial.at[i, 'geometry'] = centroid
    del centroid

for i, row in daten_hd_osm_memorial.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_hd_osm_memorial.at[i, 'geometry'] = centroid
    del centroid



for i, row in daten_dd_osm_artwork.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_dd_osm_artwork.at[i, 'geometry'] = centroid
    del centroid

for i, row in daten_hd_osm_artwork.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_hd_osm_artwork.at[i, 'geometry'] = centroid
    del centroid



for i, row in daten_dd_osm_attraction.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_dd_osm_attraction.at[i, 'geometry'] = centroid
    del centroid

for i, row in daten_hd_osm_attraction.iterrows():
    # update geometry column with centroid point of former geometry
    centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    daten_hd_osm_attraction.at[i, 'geometry'] = centroid
    del centroid




# add city data of Dresen to newdata
for i in range(0, len(daten_dd_city_4326)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_city_4326.loc[i,'id'], 'type':daten_dd_city_4326.loc[i,'einricht_2'], 'name':daten_dd_city_4326.loc[i,'einrichtun'], 'source':'opendata dresden', 'dataset':'Sehensw'+chr(252)+'rdigkeiten', 'city':'Dresden', 'geometry':daten_dd_city_4326.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)

print(newdata.head())

# ++++++++++++ FOUNTAIN ++++++++++++++++++
# add OSM dresden (dd) fountain
for i in range(0, len(daten_dd_osm_fountain)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_osm_fountain.loc[i,'id'], 'type':'Springbrunnen', 'name':daten_dd_osm_fountain.loc[i,'name'], 'source':'OSM', 'dataset':'amenity=fountain', 'city':'Dresden', 'geometry':daten_dd_osm_fountain.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# add OSM heidelberg (hd) fountain
for i in range(0, len(daten_hd_osm_fountain)):

    new_row = {'id': len(newdata), 'id_source': daten_hd_osm_fountain.loc[i,'id'], 'type':'Springbrunnen', 'name':daten_hd_osm_fountain.loc[i,'name'], 'source':'OSM', 'dataset':'amenity=fountain', 'city':'Heidelberg', 'geometry':daten_hd_osm_fountain.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)






# ++++++++++++ MEMORIAL ++++++++++++++++++
# add OSM dresden (dd) memorial
for i in range(0, len(daten_dd_osm_memorial)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_osm_memorial.loc[i,'id'], 'type':'Gedenkst'+chr(228)+'tte', 'name':daten_dd_osm_memorial.loc[i,'name'], 'source':'OSM', 'dataset':'historic=memorial', 'city':'Dresden', 'geometry':daten_dd_osm_memorial.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# add OSM heidelberg (hd) memorial
for i in range(0, len(daten_hd_osm_memorial)):

    new_row = {'id': len(newdata), 'id_source': daten_hd_osm_memorial.loc[i,'id'], 'type':'Gedenkst'+chr(228)+'tte', 'name':daten_hd_osm_memorial.loc[i,'name'], 'source':'OSM', 'dataset':'historic=memorial', 'city':'Heidelberg', 'geometry':daten_hd_osm_memorial.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# ++++++++++++ ARTWORK ++++++++++++++++++
# add OSM dresden (dd) artwork
for i in range(0, len(daten_dd_osm_artwork)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_osm_artwork.loc[i,'id'], 'type':'Kunstwerk', 'name':daten_dd_osm_artwork.loc[i,'name'], 'source':'OSM', 'dataset':'tourism=artwork', 'city':'Dresden', 'geometry':daten_dd_osm_artwork.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# add OSM heidelberg (hd) artwork
for i in range(0, len(daten_hd_osm_artwork)):

    new_row = {'id': len(newdata), 'id_source': daten_hd_osm_artwork.loc[i,'id'], 'type':'Kunstwerk', 'name':daten_hd_osm_artwork.loc[i,'name'], 'source':'OSM', 'dataset':'tourism=artwork', 'city':'Heidelberg', 'geometry':daten_hd_osm_artwork.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)





# ++++++++++++ ATTRACTION ++++++++++++++++++
# add OSM dresden (dd) attraction
for i in range(0, len(daten_dd_osm_attraction)):

    new_row = {'id': len(newdata), 'id_source': daten_dd_osm_attraction.loc[i,'id'], 'type':'Kunstwerk', 'name':daten_dd_osm_attraction.loc[i,'name'], 'source':'OSM', 'dataset':'tourism=attraction', 'city':'Dresden', 'geometry':daten_dd_osm_attraction.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)




# add OSM heidelberg (hd) attraction
for i in range(0, len(daten_hd_osm_attraction)):

    new_row = {'id': len(newdata), 'id_source': daten_hd_osm_attraction.loc[i,'id'], 'type':'Kunstwerk', 'name':daten_hd_osm_attraction.loc[i,'name'], 'source':'OSM', 'dataset':'tourism=attraction', 'city':'Heidelberg', 'geometry':daten_hd_osm_attraction.loc[i,'geometry']}
    newdata = newdata.append(new_row, ignore_index=True)

print(newdata.head())








#Exportiere die Daten als Shapefile EPSG 4326

#newdata['id'].astype('int') # to integer
newdata['id'] = pd.to_numeric(newdata['id'])

newdata.to_file("swdk/FINAL_swdk_v1.shp")
newdata.to_file("swdk/FINAL_swdk_1.geojson", driver='GeoJSON', encoding='utf-8')