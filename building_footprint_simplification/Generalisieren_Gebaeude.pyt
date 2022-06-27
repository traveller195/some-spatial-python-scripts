# Abgabe am 16.09.2020
# der Python - Code erfordert Python 2.7
# --------------------------------------------------------------

'''
Name:        Gebaeudegrundrisse generalisieren
Purpose:     APL Kartographie und Geoprocessing
Author:      Theodor Rieche (theodor.rieche@gmx.de)
Created:     16.09.2020
Copyright:   (c) Theodor Rieche, 2020
Licence:     CC-BY-SA
'''

import arcpy
from arcpy import env, gp, sa

import os
import sys
import math
import json
import csv
import copy

#import numpy as np

###import external python file in same folder:
##import polygon_triangulate as ptri

#fuer die Time der exportierten Files:
import time

from time import gmtime, strftime

#JSON Online Viewer
#http://jsonviewer.stack.hu/

###fuer graham-algorithm reduce ist notwendig
##from functools import reduce

arcpy.env.overwriteOutput = True



class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Generalisierung"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Gebaeudegrundrisse generalisieren Theodor Rieche"
        self.description = "abhaengig von einem gewaehlten Bezugsmaﬂstab fuehrt das Tool eine Generalisierung von 2D-Gebauedegrundrissen durch"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Eingabe Polygon FeatureClass",
            name="in_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")
        param0.filter.list=["Polygon"]

        param1 = arcpy.Parameter(
            displayName="Ausgabe FeatureClass",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        param2 = arcpy.Parameter(
            displayName="Bezugsmaﬂstab (nur Maﬂstabszahl als ganze Zahl)",
            name="map_scale",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param2.filter.list = [5000, 10000, 20000, 25000]

        param3 = arcpy.Parameter(
            displayName="Bezeichnung des ID-Attributes der Eingabe Polygon FeatureClass (Feldname als Zeichenkette)",
            name="id_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.value = 'id'

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if parameters[0].altered:
            try:




        # check whether CRS of input FC uses 'meter' as baisc unit. not 'degree'
        # pruefe CRS von Input FC, ob Unit gleich meters #Spatial Reference
                spatial_ref = arcpy.Describe(parameters[0].valueAsText).spatialReference

                if spatial_ref.type == "Projected":

                    if spatial_ref.linearUnitName <> "Meter":
                        parameters[0].setErrorMessage('Das Koordinatensystem der Eingabe-Daten muss als Einheit Meter verwenden! Bitte vorher das CRS anpassen.')
                    if spatial_ref.linearUnitName == "Meter":
                        pass
                if spatial_ref.type == "Geographic":

                    if spatial_ref.angularUnitName == "Degree":
                        parameters[0].setErrorMessage('Das Koordinatensystem der Eingabe-Daten muss als Einheit Meter verwenden! Bitte vorher das CRS anpassen.')
                    if spatial_ref.angularUnitName <> "Degree":
                        pass




        # check, whether user-given string for ID_field is existing in fieldnames of input FC

                lstFields = arcpy.ListFields(parameters[0].valueAsText)

                bool_id = False
                bool_id_user_given = False

        ##        id_datatype = ''
        ##        id_length = -1

                for field in lstFields:
                    if field.name == "id":
                        bool_id = True
                    if field.name == str(parameters[3].valueAsText):
                        bool_id_user_given = True
                if bool_id_user_given == False:
                    parameters[3].setErrorMessage('Bitte geben Sie einen Feldnamen ein, der bereits in der Eingabe FC existiert.')

                # weitere Eingabe-Checks

                                # Pfade auf Umlaute und sz pruefen
                # Pfade auf Leerzeichen pruefen
                error = False

                inFeatures = parameters[0].valueAsText

                if ' ' in inFeatures:
                    error = True
                if inFeatures.encode('utf-8').count('‰') > 0:
                    error = True
                if inFeatures.encode('utf-8').count('ˆ') > 0:
                    error = True
                if inFeatures.encode('utf-8').count('¸') > 0:
                    error = True
                if inFeatures.encode('utf-8').count('ﬂ') > 0:
                    error = True

                if error == True:
                    parameters[0].setErrorMessage('Der Pfad darf weder Sonderzeichen, Leerzeichen noch Umlaute enthalten!')
                # pruefen, ob ueberhaupt Features enthalten sind
                if int(arcpy.GetCount_management(inFeatures)[0]) == 0:
                    parameters[0].setErrorMessage("{0} hat keine Polygone!.".format(inFeatures.encode('utf-8')))
##                if int(arcpy.GetCount_management(inFeatures)[0]) == 1:
##                    parameters[0].setWarningMessage("{0} mit einer Linie".format(inFeatures.encode('utf-8')))
##                if int(arcpy.GetCount_management(inFeatures)[0]) > 1:
##                    parameters[0].setWarningMessage("{0} mit {1} Linien".format(inFeatures.encode('utf-8'), arcpy.GetCount_management(inFeatures)[0]))

                # Pfad auf Laenge pruefen
                laenge = len(inFeatures)
                if laenge > 200:
                    arcpy.AddError("Der Pfad fuer die Eingabe-FC ist zu lang.")



            except arcpy.ExecuteError:
                msgs = arcpy.GetMessages(2)
                arcpy.AddMessage(msgs)
            except UnicodeDecodeError:
                parameters[0].setErrorMessage('Der Pfad darf weder Sonderzeichen, Leerzeichen noch Umlaute enthalten!')


        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # take over parameters values
        inFeatures = parameters[0].valueAsText
        outFeatures = parameters[1].valueAsText
        map_scale = parameters[2].valueAsText
        id_field = parameters[3].valueAsText

        env.overwriteOutput = True

        # create new Object for the whole proccess

        # the object made from class 'Geb_generalisieren()' is the entry point for this programm

        newObj = Geb_generalisieren()


        newObj.init(inFeatures, outFeatures, map_scale, id_field)

        # remove object to finish the programm
        del newObj








        return

# ++++++++++++++++ Objekte ++++++++++++++++++++++++

# all objects - which will be needed - will declared here:
##class Point2D:
##    def __init__(self, x, y):
##        #ID ist eine fortlaufende Punkt-Nummer pro Feature
##        self.__id = -1
##        self.__x = x
##        self.__y = y
##
##        #der dem Punkt dazugehoerige Innenwinkel!
##        self.__innenwinkel = 0.0
##
##
##    def setID(self, id):
##        self.__id = id
##        return
##    def getID(self):
##        return copy.deepcopy(self.__id)
##    def getX(self):
##        return copy.deepcopy(self.__x)
##    def getY(self):
##        return copy.deepcopy(self.__y)
##    def setInnenwinkel(self, innenwinkel):
##        self.__innenwinkel = innenwinkel
##
##        print('setInnenwinkel fuer Point ID: ' + str(self.getID()) + ' mit Innenwinkel = ' + str(innenwinkel))
##
##        return
##    def getInnenwinkel(self):
##
##        return copy.deepcopy(self.__innenwinkel)
##
##
##class Polygon:
##    def __init__(self):
##        #beim Initialisieren ein leeres Array anlegen
##        self.__punkte = []
##        return
##    def addPunkt(self, point2D):
##        self.__punkte.append(point2D)
##        return
##    def getAllPoints(self):
##        return copy.deepcopy(self.__punkte)
##    def getPoint(self, index):
##        return copy.deepcopy(self.__punkte[index])
##    def getNumberOfPoints(self):
##        return copy.deepcopy(len(self.__punkte))

class DPAlgorithm():
    # source: https://stackoverrun.com/de/q/10459600
    # by Momow

       def distance(self,  a, b):
           return  math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

       def point_line_distance(self,  point, start, end):
           if (start == end):
               return self.distance(point, start)
           else:
               n = abs(
                   (end[0] - start[0]) * (start[1] - point[1]) - (start[0] - point[0]) * (end[1] - start[1])
               )
               d = math.sqrt(
                   (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2
               )
               return n / d

       def rdp(self, points, epsilon):
           """
           Reduces a series of points to a simplified version that loses detail, but
           maintains the general shape of the series.
           """
           dmax = 0.0
           index = 0
           i=1
           for i in range(1, len(points) - 1):
               d = self.point_line_distance(points[i], points[0], points[-1])
               if d > dmax :
                   index = i
                   dmax = d

           if dmax >= epsilon :
               results = self.rdp(points[:index+1], epsilon)[:-1] + self.rdp(points[index:], epsilon)
           else:
               results = [points[0], points[-1]]
           return results



class Geb_generalisieren:
    def init(self, inFeatures, outFeatures, map_scale, id_field):
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ENTRY POINT for whole programm!
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # report some facts on arcpy-report
        arcpy.AddMessage('------ PARAMETER ------')
        arcpy.AddMessage('Input FC: ' + str(inFeatures))
        arcpy.AddMessage('Output FC: ' + str(outFeatures))
        arcpy.AddMessage('Bezugsmaﬂstab: ' + str(map_scale))
        arcpy.AddMessage('ID Feldname: ' + str(id_field))

        # CRS of Input FC
        spatial_ref = arcpy.Describe(inFeatures).spatialReference

        arcpy.AddMessage('------ CRS ------')
        arcpy.AddMessage('Eingabe CRS: ' + str(spatial_ref.name))

        # number of input features in fc
        number_obj_input = arcpy.GetCount_management(inFeatures)[0]

        arcpy.AddMessage('------ Anzahl ------')
        arcpy.AddMessage('Anzahl Objekte in Eingabe FC: ' + str(number_obj_input))


        arcpy.AddMessage('------ Calculate Minimum Dimensions  ------')

        #+++++++++++++++++++Bezugsmassstab / minimum dimensions +++++++
        min_kante = 0.70 #mm
        min_flaeche = 0.1225 # mm^2

        # fuer Bezugsmassstab die Minimal-Dimensionen ausrechnen
        # jetzt in Metern

        akt_min_kante = min_kante / 1000 * int(map_scale)

        akt_min_flaeche = akt_min_kante ** 2
        #akt_min_flaeche = min_flaeche / 1000 * int(map_scale)

        arcpy.AddMessage('Minimum Length: ' + str(akt_min_kante))
        arcpy.AddMessage('Minimum Area: ' + str(akt_min_flaeche))





        # load Input Data
        # and process the first improvements of input data


        # copy input FC to temp FC, to do some data manipulations

        # so, input FC will not be edited. only tempFC and output FC


        tempFC = r"" + os.path.dirname(outFeatures) + "/temp1.shp"
        arcpy.CopyFeatures_management(inFeatures, tempFC)

        # concerning ID field in input feature class


        arcpy.AddMessage('------ ID Feld  ------')

        # check (again) if id field ist existing
        lstFields = arcpy.ListFields(inFeatures)

        bool_id = False
        bool_id_user_given = False

##        id_datatype = ''
##        id_length = -1

        for field in lstFields:
            if field.name == "id":
                bool_id = True
            if field.name == str(id_field):
                bool_id_user_given = True


        if bool_id == False:
            arcpy.AddMessage("Feldname 'id' existiert noch nicht")
            # add field 'id'
            arcpy.AddField_management(tempFC, "id", "TEXT", "", "", 100)
            arcpy.AddMessage("neues Feld 'id' hinzugefuegt")

            # copy all data from user-given ID field to new 'id' field
            # updateCursor
            with arcpy.da.UpdateCursor(tempFC, [id_field, 'id']) as cursor:
                for row in cursor:
                    # set new 'id' field = unser-given id-field
                    row[1] = row[0]
                    #arcpy.AddMessage(str(row[0]) + '  ' + str(row[1]))
                    cursor.updateRow(row)
            del cursor




        if bool_id == True:
            arcpy.AddMessage("Feldname 'id' existiert bereits")

        if bool_id_user_given == False:
            arcpy.AddMessage("(vom Nutzer gegebener) Feldname '" + str(id_field) + "' existiert nicht!")

        if bool_id_user_given == True:
            arcpy.AddMessage("(vom Nutzer gegebener) Feldname '" + str(id_field) + "' existiert")



        arcpy.AddMessage('------ Multipart to Singlepart  ------')
        tempFC_2 = r"" + os.path.dirname(outFeatures) + "/temp2.shp"

        arcpy.MultipartToSinglepart_management(tempFC, tempFC_2)


        arcpy.AddMessage('------ Dissolven  ------')

        tempFC_3 = r"" + os.path.dirname(outFeatures) + "/temp3.shp"

        arcpy.Dissolve_management(tempFC_2, tempFC_3, [], "", "SINGLE_PART")

        # Spatial Join - to keep at least one ID
        tempFC_4 = r"" + os.path.dirname(outFeatures) + "/temp4.shp"
        arcpy.SpatialJoin_analysis(tempFC_3, tempFC_2, tempFC_4, "JOIN_ONE_TO_ONE", "KEEP_ALL", '', "INTERSECT", "", "")

        arcpy.DeleteField_management(tempFC_4, 'id')
        arcpy.AddField_management(tempFC_4, "id", "TEXT", "", "", 100)

        with arcpy.da.UpdateCursor(tempFC_4, ['id_1', 'id']) as cursor:
            for row in cursor:
                # set new 'id' field = unser-given id-field
                row[1] = row[0]
                #arcpy.AddMessage(str(row[0]) + '  ' + str(row[1]))
                cursor.updateRow(row)
        del cursor


        # DOUGLAS PEUCKER ... to remove point on the same line
        arcpy.AddMessage('------ Douglas Peucker  ------')
        arcpy.AddMessage('Epsilon = 0.10 Meter')

        tempFC_5 = r"" + os.path.dirname(outFeatures) + "/temp5.shp"
        arcpy.CopyFeatures_management(tempFC_4, tempFC_5)


        with arcpy.da.UpdateCursor(tempFC_5, ['id', 'OID@', 'SHAPE@']) as cursor:

                DP_Object = DPAlgorithm()

                for row in cursor:
                    arrayFeature = arcpy.Array()
                    arrayFeature.removeAll

                    for part in row[2]:
                        # create new empty array for part
                        arrayPart = arcpy.Array()
                        arrayPart.removeAll

                        # list for douglas peucker algorithm
                        dg_array = []

                        # iterate over all vertices of polygon
                        for pnt in part:
                            if pnt:
                                # fill array for Douglas Peucker algorithm
                                dg_array.append([pnt.X, pnt.Y])

##                            else:
##                        # If pnt is None, this represents an interior ring
##                        #hier einfach einen NULL Point an das Array anhaengen
##                                #PointObject = arcpy.Point(None)
##                                #arrayPart.append(PointObject)
##                                arrayPart.append(None)

                        # run Douglas Peucker Algorithm by using epsilon = 0.1 meters

                        dg_resultat = DP_Object.rdp(dg_array, 0.1)

                        # read edited points and save back to array to write finnaly back into FC
                        for k in range(0, len(dg_resultat)):
                            PointObject = arcpy.Point(dg_resultat[k][0],dg_resultat[k][1])
                            arrayPart.append(PointObject)
                            del PointObject


                        arrayFeature.append(arrayPart)

                    # write / update modified geometry of polygon
                    row[2] = arcpy.Polygon(arrayFeature, spatial_ref)
                    cursor.updateRow(row)

                del DP_Object




        del cursor


        # minimum area criteria

        arcpy.AddMessage('------ Minimum Area Criteria  ------')

        tempFC_6 = r"" + os.path.dirname(outFeatures) + "/temp6.shp"
        arcpy.CopyFeatures_management(tempFC_5, tempFC_6)


        with arcpy.da.UpdateCursor(tempFC_6, ['id', 'OID@', 'SHAPE@AREA']) as cursor:
            for row in cursor:
                # if polygon smaller than criteria
                arcpy.AddMessage(row[2])
                if row[2] <= akt_min_flaeche:
                    #arcpy.AddMessage('loeschen')
                    cursor.deleteRow()





        del cursor

        # orientation of polygon vertices

        arcpy.AddMessage('------ Orientation of Polygons  ------')

        tempFC_7 = r"" + os.path.dirname(outFeatures) + "/temp7.shp"
        arcpy.CopyFeatures_management(tempFC_6, tempFC_7)


        with arcpy.da.UpdateCursor(tempFC_7, ['id', 'OID@', 'SHAPE@']) as cursor:

                for row in cursor:
                    arrayFeature = arcpy.Array()
                    arrayFeature.removeAll

                    for part in row[2]:
                        # create new empty array for part
                        arrayPart = arcpy.Array()
                        arrayPart.removeAll

                        # list for douglas peucker algorithm
                        orient_array = []

                        # iterate over all vertices of polygon
                        for pnt in part:
                            if pnt:
                                # fill array for Douglas Peucker algorithm
                                orient_array.append([pnt.X, pnt.Y])

##                            else:
##                        # If pnt is None, this represents an interior ring
##                        #hier einfach einen NULL Point an das Array anhaengen
##                                #PointObject = arcpy.Point(None)
##                                #arrayPart.append(PointObject)
##                                arrayPart.append(None)

                        #ORIENTIERUNG:
                        #pruefe, ob die Punkte nun im Uhrzeigersinn orientiert sind, oder nicht

                        #folgender Algorithmus:
                        #summe uber strecken: (x2-x1)(y2+y1). Wenn Ergebnis positiv ist es im Uhrzeigersinn. Wenn negativ, dann gegen UZS
                        summe = 0
                        for m in range(0, len(orient_array)):
                            if m == len(orient_array)-1:

                                produkt = (orient_array[0][0] - orient_array[m][0]) * (orient_array[0][1] + orient_array[m][1])
                                summe = summe + produkt
                                del produkt
                            else:
                                produkt = (orient_array[m+1][0] - orient_array[m][0]) * (orient_array[m+1][1] + orient_array[m][1])
                                summe = summe + produkt
                                del produkt
                        arcpy.AddMessage(str(summe) + '  Anz Vertices ' + str(len(orient_array)))

                        #kehre evt. die Reihenfolge um, wenn summe positiv ist:
                        if summe > 0:
                            orient_array.reverse()

                        # read edited points and save back to array to write finnaly back into FC
                        for k in range(0, len(orient_array)):
                            PointObject = arcpy.Point(orient_array[k][0],orient_array[k][1])
                            arrayPart.append(PointObject)
                            del PointObject


                        arrayFeature.append(arrayPart)

                    # write / update modified geometry of polygon
                    row[2] = arcpy.Polygon(arrayFeature, spatial_ref)
                    cursor.updateRow(row)

        del cursor

        # calcukate interior angle of polygon vertices

        arcpy.AddMessage('------ Interior Angle of Polygons  ------')

        #tempFC_8 = r"" + os.path.dirname(outFeatures) + "/temp8.shp"
        tempFC_8 = outFeatures
        arcpy.CopyFeatures_management(tempFC_7, tempFC_8)


        with arcpy.da.UpdateCursor(tempFC_8, ['id', 'OID@', 'SHAPE@']) as cursor:

                for row in cursor:
                    arrayFeature = arcpy.Array()
                    arrayFeature.removeAll

                    for part in row[2]:
                        # create new empty array for part
                        arrayPart = arcpy.Array()
                        arrayPart.removeAll

                        # list for coordinates of vertices
                        pkt_array = []
                        arcpy_array = arcpy.Polygon(part, spatial_ref)      # for intersection: point in polygon operation

                        # iterate over all vertices of polygon
                        for pnt in part:
                            if pnt:
                                # fill array for editing
                                pkt_array.append([pnt.X, pnt.Y])



##                            else:
##                        # If pnt is None, this represents an interior ring
##                        #hier einfach einen NULL Point an das Array anhaengen
##                                #PointObject = arcpy.Point(None)
##                                #arrayPart.append(PointObject)
##                                arrayPart.append(None)

                        # remove last point
                        del pkt_array[len(pkt_array)-1]



                        # calculate interior angles of each vertice

                        list_interior_angles = []
                        # number of '+' and '-' vertices .. will be counted later
                        anzahl_plus = 0
                        anzahl_minus = 0
                        for k in range(0, len(pkt_array)):
                            aktuell = -1
                            vorgaenger = -1
                            nachfolger = -1

                            if k == 0:
                                aktuell = 0
                                vorgaenger = len(pkt_array)-1
                                nachfolger = 1

                            if k == len(pkt_array)-1:
                                aktuell = len(pkt_array)-1
                                vorgaenger = len(pkt_array)-2
                                nachfolger = 0

                            if k > 0 and k < (len(pkt_array)-1) :
                                aktuell = k
                                vorgaenger = k - 1
                                nachfolger = k + 1

                            # construct triangle between i, i-1 and i+1 vertice

                            # calculate angle within triangle for vertice i

                            # Kosinus Satz
                            seite_a = math.sqrt((pkt_array[aktuell][0]-pkt_array[vorgaenger][0])**2+(pkt_array[aktuell][1]-pkt_array[vorgaenger][1])**2)
                            seite_b = math.sqrt((pkt_array[aktuell][0]-pkt_array[nachfolger][0])**2+(pkt_array[aktuell][1]-pkt_array[nachfolger][1])**2)
                            seite_c = math.sqrt((pkt_array[nachfolger][0]-pkt_array[vorgaenger][0])**2+(pkt_array[nachfolger][1]-pkt_array[vorgaenger][1])**2)

                            cos_gamma = (seite_a**2 + seite_b**2 - seite_c**2)/(2 * seite_a * seite_b)

                            winkel_gamma = math.acos(cos_gamma)

                            # check, if angle is interior or exterior of polygon:

                            # create new point N half between i-1 and i+1
                            N_x = (pkt_array[nachfolger][0] + pkt_array[vorgaenger][0]) / 2
                            N_y = (pkt_array[nachfolger][1] + pkt_array[vorgaenger][1]) / 2

                            # create new point P, go 1 cm from i in the direction of N
                            Vektor_x = N_x - pkt_array[aktuell][0]
                            Vektor_y = N_y - pkt_array[aktuell][1]
                            Vektor_betrag = math.sqrt(Vektor_x**2 + Vektor_y**2)

                            P_x = pkt_array[aktuell][0] + Vektor_x / Vektor_betrag * 0.01
                            P_y = pkt_array[aktuell][1] + Vektor_y / Vektor_betrag * 0.01

                            #
                            PointObject = arcpy.Point(P_x, P_y)

                            # if this new point intersects the polygon, everything is fine
                            angle = winkel_gamma
                            vorzeichen = '-'

                            if arcpy_array.contains(PointObject) == True:
                                anzahl_minus += 1
                            else:
                                # if not, angle will be 360∞-alpha / 2pi - alpha
                                angle = 2 * math.pi - winkel_gamma
                                vorzeichen = '+'
                                anzahl_plus += 1

                            del PointObject

                            list_interior_angles.append([pkt_array[aktuell][0], pkt_array[aktuell][1], angle, vorzeichen, 'True'])
                            # the last columns - after vorzeichen - shows, whether the vertice will be removed ore will be kept


                        arcpy.AddMessage(list_interior_angles)
                        arcpy.AddMessage('-----------')


                        # Generalisierung  --> anhand den berechneten Innenwinkeln den Grundriss nach Merkmalen (Vorspruengen, etc.) untersuchen


                        # if at least two '+' angles are existing:
                        if anzahl_plus >= 2:

                            # find position / index of '+' vertices
                            list_index = []
                            for k in range(0, len(list_interior_angles)):
                                if list_interior_angles[k][3] == '+':
                                    list_index.append(k)

                            # jump from '+' to '+' vertices and examine the intervalles between this points, including the '+' points before and after

                            #iterate over number of '+' vertices, because it is the same number of intervalls between '+' vertices
                            for i in range(0, anzahl_plus):
                                # handle the first intervalls in a different way compared to the last intervall between '+' vertices
                                if i < anzahl_plus - 1:
                                    # check, if there are minimum two '-' vertices in between
                                    # it is enough to calc the difference of index ... all points in between will be '-' points
                                    if list_index[i+1] - list_index[i] >= 3:
                                        # if yes: create little polygon and compare area to minimum dimension
                                        arr = arcpy.Array()
                                        arr.removeAll
                                        for x in range(list_index[i], list_index[i+1]+1):
                                            arr.append(arcpy.Point(list_interior_angles[x][0], list_interior_angles[x][1]))

                                        # add first point again
                                        arr.append(arcpy.Point(list_interior_angles[list_index[i]][0], list_interior_angles[list_index[i]][1]))
                                        poly = arcpy.Polygon(arr, spatial_ref)

                                        # if to little, remove the points between by using "False" boolean in list
                                        if poly.area < akt_min_flaeche:
                                            for x in range(list_index[i]+1, list_index[i+1]+1-1):
                                                list_interior_angles[x][4] = 'False'
                                        del arr, poly




                                if i == anzahl_plus - 1:
                                    # this is the last intervall, which reach the end of the point list.
                                    #so also vertices from the beginning of the list should be included


                                    # check, if there are minimum two '-' vertices in between
                                    # it is enough to calc the difference of index ... all points in between will be '-' points

                                    if ((len(list_interior_angles)-1) - list_index[i]) + (list_index[0]) >= 3:
                                        # if yes: create little polygon and compare area to minimum dimension
                                        arr = arcpy.Array()
                                        arr.removeAll
                                        for x in range(list_index[i], len(list_interior_angles)):
                                            arr.append(arcpy.Point(list_interior_angles[x][0], list_interior_angles[x][1]))
                                        for x in range(0, list_index[0]+1):
                                            arr.append(arcpy.Point(list_interior_angles[x][0], list_interior_angles[x][1]))


                                        # add first point again
                                        arr.append(arcpy.Point(list_interior_angles[list_index[i]][0], list_interior_angles[list_index[i]][1]))
                                        poly = arcpy.Polygon(arr, spatial_ref)

                                        # if to little, remove the points between by using "False" boolean in list
                                        if poly.area < akt_min_flaeche:
                                            arcpy.AddMessage('Punkte geloescht (+) - ID: ' + str(row[0]))

                                            for x in range(list_index[i], len(list_interior_angles)):
                                                list_interior_angles[x][4] = 'False'
                                            for x in range(0, list_index[0]+1):
                                                list_interior_angles[x][4] = 'False'

                                        del arr, poly















                        # the other way round: !!!

                        # jump from '-' to '-' vertices
                        # create selections of this vertices, including the '-' points itself
                        # check, if there are minimum two '+' vertices in between

                        # if yes: create little polygon and compare area to minimum dimension


                        # if to little, remove the points between by using "False" boolean in list


                        # if at least two '-' angles are existing:
                        if anzahl_minus >= 2:

                            # find position / index of '+' vertices
                            list_index = []
                            for k in range(0, len(list_interior_angles)):
                                if list_interior_angles[k][3] == '-':
                                    list_index.append(k)

                            # jump from '-' to '-' vertices and examine the intervalles between this points, including the '-' points before and after

                            #iterate over number of '-' vertices, because it is the same number of intervalls between '-' vertices
                            for i in range(0, anzahl_minus):
                                # handle the first intervalls in a different way compared to the last intervall between '-' vertices
                                if i < anzahl_minus - 1:
                                    # check, if there are minimum two '+' vertices in between
                                    # it is enough to calc the difference of index ... all points in between will be '+' points
                                    if list_index[i+1] - list_index[i] >= 3:
                                        # if yes: create little polygon and compare area to minimum dimension
                                        arr = arcpy.Array()
                                        arr.removeAll
                                        for x in range(list_index[i], list_index[i+1]+1):
                                            arr.append(arcpy.Point(list_interior_angles[x][0], list_interior_angles[x][1]))

                                        # add first point again
                                        arr.append(arcpy.Point(list_interior_angles[list_index[i]][0], list_interior_angles[list_index[i]][1]))
                                        poly = arcpy.Polygon(arr, spatial_ref)

                                        # if to little, remove the points between by using "False" boolean in list
                                        if poly.area < akt_min_flaeche:
                                            for x in range(list_index[i]+1, list_index[i+1]+1-1):
                                                list_interior_angles[x][4] = 'False'
                                        del arr, poly




                                if i == anzahl_minus - 1:
                                    # this is the last intervall, which reach the end of the point list.
                                    #so also vertices from the beginning of the list should be included


                                    # check, if there are minimum two '+' vertices in between
                                    # it is enough to calc the difference of index ... all points in between will be '+' points

                                    if ((len(list_interior_angles)-1) - list_index[i]) + (list_index[0]) >= 3:
                                        # if yes: create little polygon and compare area to minimum dimension
                                        arr = arcpy.Array()
                                        arr.removeAll
                                        for x in range(list_index[i], len(list_interior_angles)):
                                            arr.append(arcpy.Point(list_interior_angles[x][0], list_interior_angles[x][1]))
                                        for x in range(0, list_index[0]+1):
                                            arr.append(arcpy.Point(list_interior_angles[x][0], list_interior_angles[x][1]))


                                        # add first point again
                                        arr.append(arcpy.Point(list_interior_angles[list_index[i]][0], list_interior_angles[list_index[i]][1]))
                                        poly = arcpy.Polygon(arr, spatial_ref)

                                        # if to little, remove the points between by using "False" boolean in list
                                        if poly.area < akt_min_flaeche:
                                            arcpy.AddMessage('Punkte geloescht (-) - ID: ' + str(row[0]))

                                            for x in range(list_index[i], len(list_interior_angles)):
                                                list_interior_angles[x][4] = 'False'
                                            for x in range(0, list_index[0]+1):
                                                list_interior_angles[x][4] = 'False'

                                        del arr, poly









                       # Douglas Peucker again, to remove all forgotten points on the same line









                        startPoint = arcpy.Point(None)
                        count_true_points = 0

                        # read edited points and save back to array to write finnaly back into FC
                        for k in range(0, len(list_interior_angles)):
                            if list_interior_angles[k][4] == 'True':

                                PointObject = arcpy.Point(list_interior_angles[k][0],list_interior_angles[k][1])
                                arrayPart.append(PointObject)
                                startPoint = PointObject
                                del PointObject
                                count_true_points += 1

                        # copy first point again to the end...!
                        arrayPart.append(startPoint)

                        arrayFeature.append(arrayPart)

                    # write / update modified geometry of polygon
                    row[2] = arcpy.Polygon(arrayFeature, spatial_ref)
                    cursor.updateRow(row)





        del cursor














        return

def berechneStrecke_zweiPunkte(punkt1, punkt2):

    return math.sqrt((punkt1.x-punkt2.x)**2+(punkt1.y-punkt2.y)**2)

def orientiere_Polygon(Liste_coords):


        #ORIENTIERUNG:
    #pruefe, ob die Punkte nun im Uhrzeigersinn orientiert sind, oder nicht

    #folgender Algorithmus:
    #summe uber strecken: (x2-x1)(y2+y1). Wenn Ergebnis positiv ist es im Uhrzeigersinn. Wenn negativ, dann gegen UZS
    summe = 0
    for m in range(0, len(arrAktivePunkteID_sortiert)):
        if m == len(arrAktivePunkteID_sortiert)-1:

            produkt = (self.getPoint_byID(arrAktivePunkteID_sortiert[0]).getX()-self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getX()) * (self.getPoint_byID(arrAktivePunkteID_sortiert[0]).getY()+self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getY())
            summe = summe + produkt
            del produkt
        else:
            produkt = (self.getPoint_byID(arrAktivePunkteID_sortiert[m+1]).getX()-self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getX()) * (self.getPoint_byID(arrAktivePunkteID_sortiert[m+1]).getY()+self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getY())
            summe = summe + produkt
            del produkt
    print(summe)
    #kehre evt. die Reihenfolge um, wenn summe positiv ist:
    if summe > 0:
        arrAktivePunkteID_sortiert.reverse()



##
##def main():
##        tbx=Toolbox()
##        tool=Tool()
##        tool.execute(tool.getParameterInfo(),None)
##
##if __name__=='__main__':
##        main()
