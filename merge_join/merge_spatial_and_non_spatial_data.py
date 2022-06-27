import pandas as pd
import geopandas as gpd 
from shapely.geometry import Point, Polygon, LineString
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

# Aufgabe: 
# fuehre die kartierten Informationen aus den Bezirken fuer Dresden-Plauen zusammen
# pro Bezirk gibt es je drei Shapefiles und je drei CSV mit Attributen


# dabei ALLES in EPSG 4326 machen




# A U S G A B E = newdata GeoDataFrame()

newdata = gpd.GeoDataFrame()

newdata['Zugang'] = None
newdata['Eigt'] = None
newdata['Ernte'] = None

newdata['Centroid_X'] = None
newdata['Centroid_Y'] = None

newdata['Length_m'] = None
newdata['Area_qm'] = None


# newdata['id'] = None # muss noch ein inkrement / serial werden... wird +1 hochgezaehlt
# newdata['id_esp'] = None # die zusammengesetzte ID aus BlattNr und Nr
# newdata['blattnr'] = None
# newdata['nr'] = None
# newdata['gr'] = None
# newdata['h'] = None
# newdata['n_kuerzel'] = None
# newdata['hoehe_m'] = None
# newdata['k_ansatz_m'] = None

# newdata['vital_0'] = None
# newdata['vital_1'] = None
# newdata['vital_2'] = None
# newdata['vital_3'] = None
# newdata['vital_rs'] = None

# newdata['standorttyp'] = None

# newdata['zugang_z'] = None
# newdata['zugang_nz_s_g'] = None
# newdata['zugang_bz'] = None

# newdata['eigt_oe'] = None
# newdata['eigt_p'] = None    

# newdata['ernte_ja'] = None
# newdata['ernte_nein'] = None

# newdata['ernte_hinweis'] = None



# create column for geometry
newdata['geometry'] = None



newdata.crs = "EPSG:4326"


# Daten importieren

# iterate over folder of each bezirk/part

input_folder = r'/code/esp_data_merge/Input_Ordner_Skript/'

listFiles = [] # generate list with full path of SHP and linked CSV
for foldername in os.listdir(input_folder):
    # for each folder
    for typ in ['p', 'l', 'f']:
        csv_file = shp_file = r''
        for filename in os.listdir(os.path.join(input_folder, foldername, typ)):
            #print(os.path.join(input_folder, foldername, typ))
            file_extension = os.path.splitext(filename)[1]
            #print(file_extension)        
            if file_extension == '.csv':
                csv_file = u'' + filename
            if file_extension == '.shp':
                shp_file = u'' + filename 
        listFiles.append([os.path.join(input_folder, foldername, typ), shp_file, csv_file])

for i in range(0, len(listFiles)):
    # import each data set 
    print(' + + + + + + + + + + + + + + + + + +')
    print(str(i) + ' : ' + str(listFiles[i][0]) + '  ' + str(listFiles[i][1]) + '  ' + str(listFiles[i][2]))       

    daten_shp = gpd.read_file(r'' + os.path.join(listFiles[i][0], listFiles[i][1]), encoding='utf-8')
    daten_csv = gpd.read_file(r'' + os.path.join(listFiles[i][0], listFiles[i][2]), encoding='latin-1')
    #hier ist latin-1 als Encoder wichtig! zuerst hatte ich utf-8 aber es gab nur Fehler

    # new columns for new id
    daten_shp['id_esp'] = None
    daten_csv['id_esp'] = None

    # remove rows with empty value of 'Nr.' and 'Blatt_Nr'
    # selection: all rows, with Nr. not equal to ''

    col1 = daten_csv['Blatt_Nr'] != ''
    col2 = daten_csv['Nr.'] != ''
    daten_csv_1 = daten_csv[col1 & col2] # selection only with rows having some values for Blatt Nr and Nr.


    # if I added before the linked id column 'id_neu'.. now I will remove it
    if 'id_neu' in daten_shp.columns:
        daten_shp = daten_shp.drop(columns=['id_neu'])

    if 'id_neu' in daten_csv_1.columns:
        daten_csv_1 = daten_csv_1.drop(columns=['id_neu'])    

    # all files must have CRS WGS 84
    daten_shp = daten_shp.to_crs("EPSG:4326")





    # go over SHP data, create new ID from Blattnr and Nr
    for j, row in daten_shp.iterrows():
    # update id_esp  column with combined id from BlattNr and Nr
        daten_shp.at[j, 'id_esp'] = str(daten_shp.loc[j,'Blatt_Nr']) + '_' + str(daten_shp.loc[j,'Nr']) 


    # go over CSV data, create new ID from Blattnr and Nr
    for j, row in daten_csv_1.iterrows():
    # update id_esp  column with combined id from BlattNr and Nr
        daten_csv_1.at[j, 'id_esp'] = str(daten_csv_1.loc[j,'Blatt_Nr']) + '_' + str(daten_csv_1.loc[j,'Nr.']) 

    # JOIN / VERKETTEN by Attribute 'id_esp'
    daten_merge = daten_shp.merge(daten_csv_1, on='id_esp')

    # clean this data after Merge
    daten_merge = daten_merge.drop(columns=['Nr.'])
    daten_merge = daten_merge.drop(columns=['Blatt_Nr_y'])
    daten_merge = daten_merge.drop(columns=['geometry_y'])
    # rename columns after Merge
    daten_merge = daten_merge.rename(columns={'geometry_x': 'geometry'}).set_geometry('geometry') # set_geometry for geometry column!
    daten_merge = daten_merge.rename(columns={'Blatt_Nr_x': 'Blatt_Nr'})

    # new output GeoDataFrame only with the structure of the gdf, without the data... only the columns
    if i == 0:
        newdata = daten_merge
    if i > 0:
        newdata = newdata.append(daten_merge, ignore_index=True)

    





    # merge / concat / append the gdf into one GDF for output

    print(newdata.info())
    print(newdata.head())


    #print(daten_merge.info())
    #print(daten_csv_1.info())

    #print(daten_merge.head())
    #print(daten_csv_1.head())


# D A T E N A U F B E R E I T U N G
# +++++++++++++++++++++++++++++++++++

# einige Attribute zusammenfassen

attribute_name = 'Eigt_' + chr(246)  # for char 'oe'

for j, row in newdata.iterrows():
    # Zugang
    if newdata.loc[j, 'Zugang_z']=='x':
        newdata.at[j, 'Zugang'] = 'z'
    if newdata.loc[j, 'Zugang_nz_S_G']=='x':
        newdata.at[j, 'Zugang'] = 'nz_S_G'
    if newdata.loc[j, 'Zugang_bz']=='x':
        newdata.at[j, 'Zugang'] = 'bz'  

    # Eigentum
    
    if newdata.loc[j, attribute_name]=='x':
        newdata.at[j, 'Eigt'] = 'oe'
    if newdata.loc[j, 'Eigt_p']=='x':
        newdata.at[j, 'Eigt'] = 'p'

    # Ernte

    if newdata.loc[j, 'Ernte_ja']=='x':
        newdata.at[j, 'Ernte'] = 'ja'
    if newdata.loc[j, 'Ernte_nein']=='x':
        newdata.at[j, 'Ernte'] = 'nein'


# fill two columns with x and y of centroid --> is better for CSV to also have some data of geometry

for j, row in newdata.iterrows():
    # update geometry column with centroid of geometry
    newdata.at[j, 'Centroid_X'] = row.geometry.centroid.x
    newdata.at[j, 'Centroid_Y'] = row.geometry.centroid.y

    # centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
    # newdata.at[i, 'geometry'] = centroid
    # del centroid


# NEW: fill two columns. One for Length_m and one for Area_qm

for j, row in newdata.iterrows():
    # update length meters column... only for LineString / "Hecke"
    # transform geometry to epsg 25833 to measure in Meters
    if newdata.loc[j, 'H']=='x':
        geom_4326 = row.geometry
        transformer = pyproj.Transformer.from_crs(pyproj.CRS('EPSG:4326'), pyproj.CRS('EPSG:25833'), always_xy=True).transform
        geom_25833 = shapely.ops.transform(transformer, geom_4326)
        

        # length in meter
        newdata.at[j, 'Length_m'] = geom_25833.length




    # update area squaremeters column... only for Polygon / "Gruppe"
    if newdata.loc[j, 'Gr']=='x':
        geom_4326 = row.geometry
        transformer = pyproj.Transformer.from_crs(pyproj.CRS('EPSG:4326'), pyproj.CRS('EPSG:25833'), always_xy=True).transform
        geom_25833 = shapely.ops.transform(transformer, geom_4326)
        

        # length in meter
        newdata.at[j, 'Area_qm'] = geom_25833.area



# drop some columns
newdata = newdata.drop(columns=['Zugang_z'])
newdata = newdata.drop(columns=['Zugang_nz_S_G'])
newdata = newdata.drop(columns=['Zugang_bz'])

newdata = newdata.drop(columns=[attribute_name])
newdata = newdata.drop(columns=['Eigt_p'])

newdata = newdata.drop(columns=['Ernte_ja'])
newdata = newdata.drop(columns=['Ernte_nein'])

# change order of columns
newdata = gpd.GeoDataFrame(newdata[["geometry", "id", "id_esp", "Blatt_Nr", "Nr", "Gr", "H", "Namensk"+chr(252)+"rzel", "H"+chr(246)+"he_m", "K_Ansatz_m", "Vitalit"+chr(228)+"t_0", "Vitalit"+chr(228)+"t_1", "Vitalit"+chr(228)+"t_2", "Vitalit"+chr(228)+"t_3", "Vitalit"+chr(228)+"t_rs", "Standorttyp", "Zugang", "Eigt", "Ernte", "Ernte_Hinweis", "Centroid_X", "Centroid_Y", "Length_m", "Area_qm"]])



#Exportiere die Daten als Shapefile EPSG 4326


# fill in serial number for ID
for j, row in newdata.iterrows():
# update id_esp  column with combined id from BlattNr and Nr
    newdata.at[j, 'id'] = j

#newdata['id'].astype('int') # to integer
newdata['id'] = pd.to_numeric(newdata['id'])

newdata.to_csv("/code/esp_data_merge/" + str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + "_result.csv", encoding='utf-8')
newdata.to_file("/code/esp_data_merge/" + str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + "_result.geojson", driver='GeoJSON', encoding='utf-8')



# # select distinct 'id' - quasi ein group by 'id'
# #listID = daten_rnv['id'].unique().tolist()


# # ++++++++++++++++++++++++++++++++++++++++++++
# # project to WGS84 / EPSG 4326
# # daten_dd_city_4326 = daten_dd_city.to_crs("EPSG:4326")


# # ++++++++++++++++++++++++++++++++++++++++++++
# # create CENTROID: polygon and line to point

# # for i, row in daten_dd_osm_fountain.iterrows():
# #     # update geometry column with centroid point of former geometry
# #     centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
# #     daten_dd_osm_fountain.at[i, 'geometry'] = centroid
# #     del centroid

# # for i, row in daten_hd_osm_fountain.iterrows():
# #     # update geometry column with centroid point of former geometry
# #     centroid = Point(row.geometry.centroid.x, row.geometry.centroid.y)
# #     daten_hd_osm_fountain.at[i, 'geometry'] = centroid
# #     del centroid

# # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# # V E R S U C H S R E I H E N 
# # synthetisch mit Zufallszahlen, welche entscheiden, welche Sitzbaenke entfernet werden sollen


# # Array fuer Aufbau des Versuchs

# # (prozent_stadt dd, prozent_osm, Anzahl_Versuchsreihen, buffer_minimum_meter, buffer_maximum_buffer)

# arr_aufbau_versuch = [[100, 100, 1, 1, 25],
#                         [100, 80, 10, 1, 25],
#                         [80, 100, 10, 1, 25],
#                         [80, 80, 10, 1, 25]]

# # also ein Duchgang mit beiden Datensaetzen vollstaendig
# # und dann jeweils 10 Durchgaenge mit synthetisch verschlechterten Datensaetzen (20% entfernt = 80)

# # dabei wird beim Entfernen pro Durchgang durch Zufallsgenerator andere Baenke ausgesucht
# # pro Durchgang wird jeweils Datensatz A und danach Datensatz B gepuffert

# #das Array Zeile fuer Zeile durchgehen und abbarbeiten
# zaehlvariable = 0
# nummer_versuch = -1

# for i in range(0, len(arr_aufbau_versuch)):
#     # zeilenweise das Array vom Versuchsaufbau abbarbeiten

#     # die Anzahl der jeweiligen Versuchsreihen durchlaufen
#     for j in range(0, arr_aufbau_versuch[i][2]):
#         # anzahl Versuchsreihen 
#         nummer_versuch = nummer_versuch + 1



#         # datensaetze fuer aktuellen Versuch , als deep copy mit .copy()
#         data_city_dd = daten_city_dd.copy()
#         data_osm = daten_osm.copy()
        
#         # Zufallszahlen um Elemente zu loeschen, falls weniger als 100% verwendet werden sollen
#         # Stadt Dresden
#         if arr_aufbau_versuch[i][0] < 100:
#             # Anzahl an zu loeschenden Elementen errechnen
#             anz = len(daten_city_dd) * arr_aufbau_versuch[i][0] / 100
#             anz_el = int(round(anz, 0))
#             anz_el_delete_city_dd = len(daten_city_dd) - anz_el

#             print('------------------------')            
#             print('Anzahl loeschender Elemente - City DD : ' + str(anz_el_delete_city_dd))

#             zufallszahlen = []
#             for z in range(0, anz_el_delete_city_dd):
#                 zuf = randint(0, len(daten_city_dd) - 1)
#                 while zuf in zufallszahlen:
#                     zuf = randint(0, len(daten_city_dd) - 1)
#                     #solange die Zufallszahl neu wuerfeln, falls sie schon existiert (keine Duplikate)
#                 zufallszahlen.append(zuf)
#             #Array sortieren
#             zufallszahlen.sort()
#             print('Zufallszahlen: ' + str(zufallszahlen))

#             # remove rows/ elements by using random integers as index
#             data_city_dd.drop(zufallszahlen,  inplace=True)
            
#             print('Anzahl Elemente in GeoDataFrame: ' + str(len(data_city_dd)))

#             print('------------------------')


#         # OSM
#         if arr_aufbau_versuch[i][1] < 100:
#             # Anzahl an zu loeschenden Elementen errechnen
#             anz = len(daten_osm) * arr_aufbau_versuch[i][1] / 100
#             anz_el = int(round(anz, 0))
#             anz_el_delete_osm = len(daten_osm) - anz_el
            
#             print('Anzahl loeschender Elemente - OSM : ' + str(anz_el_delete_osm))

#             zufallszahlen = []
#             for z in range(0, anz_el_delete_osm):
#                 zuf = randint(0, len(daten_osm) - 1)
#                 while zuf in zufallszahlen:
#                     zuf = randint(0, len(daten_osm) - 1)
#                     #solange die Zufallszahl neu wuerfeln, falls sie schon existiert (keine Duplikate)
#                 zufallszahlen.append(zuf)
#             #Array sortieren
#             zufallszahlen.sort()
#             print('Zufallszahlen: ' + str(zufallszahlen))

#             # remove rows/ elements by using random integers as index
#             data_osm.drop(zufallszahlen,  inplace=True)
            
#             print('Anzahl Elemente in GeoDataFrame: ' + str(len(data_osm)))

#             print('------------------------')

#         # nun gibt es fuer jeden Versuch die synthetisch hergestellten Datensaetze 

#         # Differenz = Maximum Buffer minus Minimum Buffer
#         differenz_buffer_intervall = arr_aufbau_versuch[i][4] - arr_aufbau_versuch[i][3]

#         for k in range(0, differenz_buffer_intervall + 1):
#             # fuer jeden Buffer-Schritt in Schleife durchgehen
#             # also von Minimum bis Maximum in 1Meter Schritten
#             akt_buffer = int(arr_aufbau_versuch[i][3]) + int(k)

#             for m in range(0, 2):
#                 # fuer die beiden Faelle, dass beide Datensaetze mal gepuffert wurden
#                 arr_ID_results = []
#                 dataset_buffered = ''
                
#                 if m == 0:
#                     #wenn 0 = Stadt DD Daten
#                     dataset_buffered = 'city DD'

#                     city_DD_buffer = data_city_dd.copy()
#                     city_DD_buffer['dissolve'] = None
#                     #create BUFFER
#                     for x, row in city_DD_buffer.iterrows():
#                         # update geometry column with buffer
#                         city_DD_buffer.at[x, 'geometry'] = row.geometry.buffer(akt_buffer)
#                         #fill value to new attribute, to easier dissolve it finally
#                         city_DD_buffer.at[x, 'dissolve'] = 0

#                     # haenge alle IDs vom gepufferten Datensatz an, da diese Elemente 
#                     # alle erhalten bleiben!
#                     for x, row in data_city_dd.iterrows():
#                         arr_ID_results.append(str(data_city_dd.loc[x,'autoid']))


#                     # dissolve should have equal values--> everything should be dissolved
#                     buffer_dissolved = city_DD_buffer.dissolve(by='dissolve')
#                     #there is still one multipolygon, which we need for intersection/ within
#                     buffer_polygon = buffer_dissolved.loc[0, 'geometry']

#                     #print(buffer_polygon)

#                     #print(arr_ID_results)
#                     #print(buffer_dissolved.head())

#                     for x, row in data_osm.iterrows():   
#                         #iterate over not-buffered dataset and check 'within' point in polygon
#                         point_current = data_osm.loc[x, 'geometry'] 
#                         #print(point_current)  
#                         if (point_current.within(buffer_polygon)):
#                             pass
#                             # do nothing with this ID of point
#                         else:
#                             #if Point is out of buffer_polygon
#                             arr_ID_results.append(str(data_osm.loc[x, 'id']))   
#                         del point_current

#                     print('Anzahl an Punkten im Ergebnis: ' + str(len(arr_ID_results)))           
                
#                 if m == 1:
#                     #wenn 1 = OSM Daten
#                     dataset_buffered = 'osm'


#                     osm_buffer = data_osm.copy()
#                     osm_buffer['dissolve'] = None

#                     #create BUFFER
#                     for x, row in osm_buffer.iterrows():
#                         # update geometry column with buffer
#                         osm_buffer.at[x, 'geometry'] = row.geometry.buffer(akt_buffer)
#                         #fill value to new attribute, to easier dissolve it finally
#                         osm_buffer.at[x, 'dissolve'] = 0

#                     # haenge alle IDs vom gepufferten Datensatz an, da diese Elemente 
#                     # alle erhalten bleiben!
#                     for x, row in data_osm.iterrows():
#                         arr_ID_results.append(str(data_osm.loc[x,'id']))


#                     # dissolve should have equal values--> everything should be dissolved
#                     buffer_dissolved = osm_buffer.dissolve(by='dissolve')
#                     #there is still one multipolygon, which we need for intersection/ within
#                     buffer_polygon = buffer_dissolved.loc[0, 'geometry']

#                     #print(buffer_polygon)

#                     #print(arr_ID_results)
#                     #print(buffer_dissolved.head())

#                     for x, row in data_city_dd.iterrows():   
#                         #iterate over not-buffered dataset and check 'within' point in polygon
#                         point_current = data_city_dd.loc[x, 'geometry'] 
#                         #print(point_current)  
#                         if (point_current.within(buffer_polygon)):
#                             pass
#                             # do nothing with this ID of point
#                         else:
#                             #if Point is out of buffer_polygon
#                             arr_ID_results.append(str(data_city_dd.loc[x, 'autoid']))   
#                         del point_current

#                     print('Anzahl an Punkten im Ergebnis: ' + str(len(arr_ID_results)))           







#                 # AUSWERTUNG und Datensatz in Ergebnis schreiben
#                 anzahl_tp = anzahl_tn = anzahl_fp = anzahl_fn = 0

#                 #print(arr_ID_results)
#                 #print(daten_csv_matching_table.head())



#                 # die matching table durchgehen, mit den arr_UID_results abgleichen
#                 # und die Anzahl an true positive, true negativ, false positive, false negative hochzaehlen

#                 for x, row in daten_csv_matching_table.iterrows():
#                     #iterate over matching table
#                     if daten_csv_matching_table.loc[x, 'stat_city_dd'] == 'true':
#                         check_1 = str(daten_csv_matching_table.loc[x, 'id_osm']) in arr_ID_results
#                         check_2 = str(daten_csv_matching_table.loc[x, 'id_city_dd']) in arr_ID_results

#                         #print(str(check_1) + '  ' + str(check_2))

#                         if (check_1 == True and check_2 == False) or (check_1 == False and check_2 == True):
#                             # so soll es sein. genau ein Punkt hat richtiger ueberlebt
#                             anzahl_tp += 1
#                             anzahl_tn += 1


#                         if (check_1 == True and check_2 == True):
#                             # ein Punkt ist zu viel
#                             anzahl_tp += 1
#                             anzahl_fp += 1


#                         if (check_1 == False and check_2 == False):
#                             # der Punkt taucht gar nicht mehr auf, egal ob OSM oder city dd
#                             anzahl_tn += 1
#                             anzahl_fn += 1


#                     if daten_csv_matching_table.loc[x, 'stat_city_dd'] == 'false':
#                         check_1 = str(daten_csv_matching_table.loc[x, 'id_osm']) in arr_ID_results

#                         #print(str(check))

#                         if check_1 == True:
#                             # so soll es sein. genau ein Punkt hat richtiger ueberlebt
#                             anzahl_tp += 1
#                             anzahl_tn += 1

#                         if check_1 == False:
#                             # der Punkt taucht gar nicht mehr auf, egal ob OSM oder city dd
#                             anzahl_tn += 1
#                             anzahl_fn += 1   
#                 # Schreibe Resultat in newdata
#                 new_row = {'id': len(newdata), 'id_series': nummer_versuch, 'proz_city_dd':arr_aufbau_versuch[i][0], 'proz_osm':arr_aufbau_versuch[i][1], 'dataset_buffered':dataset_buffered, 'buffer_value':akt_buffer, 'number_points':len(arr_ID_results), 'true_positive':anzahl_tp, 'true_negative':anzahl_tn, 'false_positive':anzahl_fp, 'false_negative':anzahl_fn}
#                 newdata = newdata.append(new_row, ignore_index=True)

# # print(newdata.head())

# # Datenauswertung / Diagramme

# # geeignet Aggregieren




# #Exportiere die Daten als Shapefile EPSG 4326

# #newdata['id'].astype('int') # to integer
# newdata['id'] = pd.to_numeric(newdata['id'])

# newdata.to_csv("analyse_suchradius/output/" + str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + "_result.csv")
# #newdata.to_file("swdk/FINAL_swdk_1.geojson", driver='GeoJSON', encoding='utf-8')