#import arcpy
import os
import sys
import math
import json
import csv
import copy

import numpy as np

#import external python file in same folder:
import polygon_triangulate as ptri

#fuer die Time der exportierten Files:
import time

from time import gmtime, strftime

#JSON Online Viewer
#http://jsonviewer.stack.hu/

#fuer graham-algorithm reduce ist notwendig
from functools import reduce


# ++++++++++++++++ Objekte ++++++++++++++++++++++++
class Point2D:
    def __init__(self, x, y):
        #ID ist eine fortlaufende Punkt-Nummer pro Feature
        self.__id = -1
        self.__x = x
        self.__y = y


        #der dem Punkt dazugehoerige Bewegungsvektor!
        self.__v_x = 0.0
        self.__v_y = 0.0

    def setID(self, id):
        self.__id = id
        return
    def getID(self):
        return self.__id
    def getX(self):
        return self.__x
    def getY(self):
        return self.__y
    def setBewegungsvektor(self, v_x, v_y):
        self.__v_x = v_x
        self.__v_y = v_y
        print('setBewegungsvektor fuer Point ID: ' + str(self.getID()) + ' mit v_x = ' + str(v_x) + ' v_y = ' + str(v_y))

        return
    def getBewegungsvektor(self):

        return copy.deepcopy(self.__v_x), copy.deepcopy(self.__v_y)

##class Line:
##    def __init__(self):
##        self.__arrLine = []
##
##        return
##    def addPunkt(self, point2D):
##        self.__arrLine.append(point2D)
##        return
##
##
##class Line_segment:
##    def __init__(self):
##        #ein Liniensegment zwischen genau zwei Punkten,
##        self.__pointID1 = -1
##        self.__pointID2 = -1
##
##        return

class Line_weighted:
    def __init__(self, p1, p2, w, z):
        #erbt von Line_segment

        self.__pointID1 = p1
        self.__pointID2 = p2
        self.__weight = w
        self.__zyklusNr = z
        self.__id = -1
        return

    def getPointID1(self):
        return self.__pointID1
    def getPointID2(self):
        return self.__pointID2
    def getWeight(self):
        return self.__weight
    def getZyklusNr(self):
        return self.__zyklusNr

    def getID(self):
        return self.__id
    def setID(self, id):
        self.__id = id
        return



class Line_move:
    def __init__(self, p1, p2, z):
        #Bewegungsvektor
        #erbt von Line_segment
        self.__pointID1 = p1
        self.__pointID2 = p2
        self.__zyklusNr = z
        self.__id = -1
        return
    def getPointID1(self):
        return self.__pointID1
    def getPointID2(self):
        return self.__pointID2
    def getZyklusNr(self):
        return self.__zyklusNr
    def getID(self):
        return self.__id
    def setID(self, id):
        self.__id = id
        return

class Dreieck():
    def __init__(self, p1, p2, p3):
        self.__pointID1 = -1
        self.__pointID2 = -1
        self.__pointID3 = -1

        self.__pointID1 = p1
        self.__pointID2 = p2
        self.__pointID3 = p3

        self.__id = -1

        #t = collapes time... -1.0 = unendlich ; -2.0 = noch nicht berechnet
        self.__collapseTime = -2.0

        #wichtig beim init wird gleich auf kollinearitaet/ Punkte auf einer Linie geprueft
        #und unter Umstaenden ein neues Event in der Eventliste angehaengt

    def getID(self):
        return self.__id
    def setID(self, id):
        self.__id = id
        return

    def getPointID1(self):
        return self.__pointID1
    def getPointID2(self):
        return self.__pointID2
    def getPointID3(self):
        return self.__pointID3

    def getCollapseTime(self):
        return self.__collapseTime

    def setCollapseTime(self, time):
        #Zeit zuweisen
        self.__collapseTime = time

        return


##class Polygon:
##    def __init__(self):
##        #beim Initialisieren ein leeres Array anlegen
##        self.__punkte = []
##        return
##    def addPunkt(self, point2D):
##        self.__punkte.append(point2D)
##        return
##    def getAllPoints(self):
##        return self.__punkte
##    def getPoint(self, index):
##        return self.__punkte[index]
##    def getNumberOfPoints(self):
##        return len(self.__punkte)
##    def getTriangulation(self):
##
##
##        return triangulation
##    def toMatplotlib(self):
##        #convert geometry data to drav in matplotlib
##
##        return datastructure

class Skeleton_Object:
    def __init__(self):
        #die Punkteliste speichert die Objekte vom Typ Point2D als Punkte-Vorrat.
        #Der Index im Array steht fuer die lokale ID pro Polygon.
        #Die Liste ist geordnet, aber der erste Punkt ist nicht doppelt am Ende!
        #jeder Punkt ist unique, bekommt eine eindeutige ID
        self.__storagePoint2D = []

        #eine Liste an Objekten vom Typ "Line_weighted".
        #Die dort verwendeten IDs referenzieren auf den Index der Punkte im Array.
        #Die Gewichte der Kanten werden in den Linien-Objekten gespeichert.
        self.__kanten = []

        #eine Liste an Objekten vom Typ "Line_move".
        #Die dort verwendeten IDs referenzieren auf den Index der Punkte im Array.
        #Die Zeiten der Generierung der Bewegungsvektoren werden im Objekt gespeichert.
        self.__bewegungsvektoren = []

        #eine Liste fuer die Polygone der Triangulation
        #diese werden jeweils als Dreiecke mit den Point-IDs abgespeichert....
        #vom Typ "Dreieck"
        self.__triangulation = []

        #LISTE aller Cycle-Objects , also von jeder durchgefuehrten Runde im Schrumpfungsprozess
        self.__ListeCycleObjects = []

        #beim Initialisieren gleich ein Objekt vom Typ EventList erstellen
        self.__EventList = EventList()

        #hier werden die erzeugten NODES des SKELETON S als Point ID abgelegt... bei EDGE und SPLIT event
        self.__skeleton = []


        return

    def addPoint2D(self, point2D, duplikateZulassen='no'):

        #wichtig: hier pruefen, ob es die Koordinaten des Punktes schon gibt!
        #entsprechendes ReturnObjekt zurueckgeben, ob erfolgreich, wenn nein, welche alte ID verwendet werden muss

        #wenn nein, dann Punkt speichern und ihm eine neue ID geben
        #wenn ja, dann ReturnObj zurueckgeben, dass schon existiert

        #ebenfalls Objektfang/ Snapping einfuehren
        #wenn der neue Punkt naeher als 1 mm an einem anderen existieren Punkt liegt, dann wird er nicht neu erstellt!

        if duplikateZulassen == 'no':
            ergebnis = -1
            status = 'yes'
            for i in range(0, len(self.__storagePoint2D)):
                if self.__storagePoint2D[i].getX() == point2D.getX() and self.__storagePoint2D[i].getY() == point2D.getY():
                    status = 'no'
                    ergebnis = i
                else:
                    #berechne Abstand zwischen altem Punkt und neuem Punkt
                    distanz = math.sqrt((self.__storagePoint2D[i].getX() - point2D.getX())**2 + (self.__storagePoint2D[i].getY() - point2D.getY())**2)
                    #SNAP/ OBJEKTFANG Toleranz 1 mm
                    if distanz < 0.001:
                        status = 'no'
                        ergebnis = i
                    del distanz
            if status == 'yes':

                self.__storagePoint2D.append(point2D)
                id = len(self.__storagePoint2D)-1
                self.__storagePoint2D[id].setID(id)
                returnMessage = 'Point2D hinzugefuegt - ID: ' + str(id) + ' x = ' + str(self.__storagePoint2D[id].getX()) + ' y = ' + str(self.__storagePoint2D[id].getY())
                ergebnis = id
            else:
                returnMessage = 'Point2D nicht hinzugefuegt, da schon vorhanden - siehe ID ' + str(ergebnis)
                status = 'no'

        else:
            #bei einem SPLIT-Event muessen zwei separate Punkte uebereinander liegen, aber mit unterschiedlichen Bewegungsvektoren!!!
            #der SNAP und die Regeln werden also ausser Kraft gesetzt!!!!!!!!!
            self.__storagePoint2D.append(point2D)
            id = len(self.__storagePoint2D)-1
            self.__storagePoint2D[id].setID(id)
            returnMessage = 'Point2D hinzugefuegt - ID: ' + str(id) + ' x = ' + str(self.__storagePoint2D[id].getX()) + ' y = ' + str(self.__storagePoint2D[id].getY())
            print('ACHTUNG: SPLIT-EVENT. Punkt wurde ohne Duplikate-Pruefung/ SNAPPING gespeichert!')
            ergebnis = id
            statis = 'yes'


        #es wird eine ID zurueckgegeben, entweder die des neuen Punktes, oder die das schon existierenden Punktes
        retour = returnObject(returnMessage, status, ergebnis)
        return retour

    def getPointID_byCoordinates(self, x, y):
        #gibt die Punkte-ID zurueck, die zu der gegebenen x und y Koordinate passen
        ergebnis = -1
        for i in range(0, len(self.__storagePoint2D)):
            if self.__storagePoint2D[i].getX() == x and self.__storagePoint2D[i].getY() == y:
                ergebnis = i
        #wenn es den Punkt noch nicht gibt, wird -1 zurueckgegeben
        return ergebnis

    def getPoint_byID(self, id):

        return copy.deepcopy(self.__storagePoint2D[id])
    def getNumberOfPoints(self):
        return len(self.__storagePoint2D)

    def add_Line_weighted(self, wl):
        self.__kanten.append(wl)
        #Id nach nachtraeglich setzen, ist gleich dem Index im array...
        id = len(self.__kanten)-1
        self.__kanten[id].setID(id)
        message = 'Line_weighted hinzugefuegt - ID: ' + str(id) + ' - P1 ' + str(self.__kanten[id].getPointID1()) + ' - P2 ' + str(self.__kanten[id].getPointID2()) + ' weight = ' + str(self.__kanten[id].getWeight())
        status = 'yes'
        retour = returnObject(message, status, id)

        return retour
    def getNumberOfLine_weighted(self):
        return len(self.__kanten)
    def getLine_weightedID_byGivenPointID(self, id):
        #gibt alle Line_weighted IDs zurueck, die diese PointID enthalten
        listeID = []
        for i in range(0, len(self.__kanten)):
            if (self.__kanten[i].getPointID1() == id) or (self.__kanten[i].getPointID2() == id):
                listeID.append(i)
        returnMessage = 'gefundene Line_weighted fuer PointID = ' + str(id) + ' - Anzahl: ' + str(len(listeID))
        status = ''
        retour = returnObject(returnMessage, status, -1, listeID)
        return retour

    def getLine_weightedID_byTwoGivenPointID(self, p1, p2):
        #gibt alle Line_weighted IDs zurueck, die diese PointID enthalten
        ergebnis = -1
        for i in range(0, len(self.__kanten)):
            if (self.__kanten[i].getPointID1() == p1) and (self.__kanten[i].getPointID2() == p2):
                ergebnis = i
            if (self.__kanten[i].getPointID1() == p2) and (self.__kanten[i].getPointID2() == p1):
                ergebnis = i
        return ergebnis

    def getLine_weighted_byID(self, id):
        return copy.deepcopy(self.__kanten[id])


    def add_Dreieck(self, tri):
        self.__triangulation.append(tri)
        #Id nach nachtraeglich setzen, ist gleich dem Index im array...
        id = len(self.__triangulation)-1
        self.__triangulation[id].setID(id)
        message = 'Dreieck hinzugefuegt - ID: ' + str(self.__triangulation[id].getID()) + ' - P1 ' + str(self.__triangulation[id].getPointID1()) + ' - P2 ' + str(self.__triangulation[id].getPointID2()) + ' - P3 ' + str(self.__triangulation[id].getPointID3())
        status = 'yes'
        #hier ein ReturnObject verwenden, um die vergebene ID zurueckschicken zu koennen, damit kann das Dreieck aktiv gesetzt werden!
        retour = returnObject(message, status, id)
        return retour

    def getDreieck_byID(self, id):
        return copy.deepcopy(self.__triangulation[id])

    def getDreieck_byTwoGivenPointID(self, id1, id2):
        #ein Array mit allen passenden Dreiecken fuer die beiden geg Punkte ID wird zurueckgegeben
        ergebnis = []
        for i in range(0, len(self.__triangulation)):
            if (self.__triangulation[i].getPointID1() == id1) and (self.__triangulation[i].getPointID2() == id2):
                ergebnis.append(i)
            if (self.__triangulation[i].getPointID1() == id2) and (self.__triangulation[i].getPointID2() == id1):
                ergebnis.append(i)

            if (self.__triangulation[i].getPointID2() == id1) and (self.__triangulation[i].getPointID3() == id2):
                ergebnis.append(i)
            if (self.__triangulation[i].getPointID2() == id2) and (self.__triangulation[i].getPointID3() == id1):
                ergebnis.append(i)

            if (self.__triangulation[i].getPointID3() == id1) and (self.__triangulation[i].getPointID1() == id2):
                ergebnis.append(i)
            if (self.__triangulation[i].getPointID3() == id2) and (self.__triangulation[i].getPointID1() == id1):
                ergebnis.append(i)

        return ergebnis
    def getDreieck_byThreeGivenPointID(self, id1, id2, id3):
        #ein Array mit allen passenden Dreiecken fuer die drei geg Punkte ID wird zurueckgegeben
        ergebnis = []

        for i in range(0, len(self.__triangulation)):
            idList = []
            idList.append(self.__triangulation[i].getPointID1())
            idList.append(self.__triangulation[i].getPointID2())
            idList.append(self.__triangulation[i].getPointID3())

            #wenn alle drei Punkte enthalten sind (Reihenfolge dabei egal)
            if (idList.count(id1) > 0) and (idList.count(id2) > 0) and (idList.count(id3) > 0):
                ergebnis.append(i)
            del idList

        return ergebnis

    def add_Line_move(self, line_move):
        self.__bewegungsvektoren.append(line_move)
        #Id nach nachtraeglich setzen, ist gleich dem Index im array...
        id = len(self.__bewegungsvektoren)-1
        self.__bewegungsvektoren[id].setID(id)
        message = 'Line_move hinzugefuegt - ID: ' + str(id) + ' - P1 ' + str(self.__bewegungsvektoren[id].getPointID1()) + ' - P2 ' + str(self.__bewegungsvektoren[id].getPointID2())
        status = 'yes'
        retour = returnObject(message, status, id)

        return retour

    def getLine_move_byID(self, id):
        return self.__bewegungsvektoren[id]

    def getLine_moveID_byGivenPointID(self, id):
        #gibt alle Line_move IDs zurueck, die diese PointID enthalten
        listeID = []
        for i in range(0, len(self.__bewegungsvektoren)):
            if (self.__bewegungsvektoren[i].getPointID1() == id) or (self.__bewegungsvektoren[i].getPointID2() == id):
                listeID.append(i)
        returnMessage = 'gefundene Line_move fuer PointID = ' + str(id) + ' - Anzahl: ' + str(len(listeID))
        status = ''
        retour = returnObject(returnMessage, status, -1, listeID)
        return retour


    def add_CycleObject(self, cycle_obj):
        self.__ListeCycleObjects.append(cycle_obj)
        return
    def getNumberOfCycles(self):
        return len(self.__ListeCycleObjects)

    def addActivePointID(self, pointID, zyklusnr):
        self.__ListeCycleObjects[zyklusnr].addActivePointID(pointID)
        print('Active Point hinzugefuegt - ID: ' + str(pointID) + ' - Zyklus Nr.: ' + str(zyklusnr))
        return

    def addActiveLine_weightedID(self, lineID, zyklusnr):
        self.__ListeCycleObjects[zyklusnr].addActiveLine_weightedID(lineID)
        print('Active Line_weighted hinzugefuegt - ID: ' + str(lineID) + ' - Zyklus Nr.: ' + str(zyklusnr))
        return

    def addActiveLine_moveID(self, lineID, zyklusnr):
        self.__ListeCycleObjects[zyklusnr].addActiveBewegungsvektor(lineID)
        print('Active Line_move hinzugefuegt - ID: ' + str(lineID) + ' - Zyklus Nr.: ' + str(zyklusnr))
        return

    def addActiveDreieckID(self, triID, zyklusnr):
        self.__ListeCycleObjects[zyklusnr].addActiveDreieckID(triID)
        print('Active Dreieck hinzugefuegt - ID: ' + str(triID) + ' - Zyklus Nr.: ' + str(zyklusnr))
        return

    def get_storagePoint2D(self):
        return self.__storagePoint2D

    def getAllActivePointID(self, zyklusnr):
        return self.__ListeCycleObjects[zyklusnr].getAllActivePointID()
    def getAllActiveLine_weighted(self, zyklusnr):
        return self.__ListeCycleObjects[zyklusnr].getAllActiveLine_weighted()
    def getAllActiveDreiecke(self, zyklusnr):
        return self.__ListeCycleObjects[zyklusnr].getAllActiveDreiecke()
    def getAllActiveBewegungsvektoren(self, zyklusnr):
        return self.__ListeCycleObjects[zyklusnr].getAllActiveBewegungsvektoren()


    def getLength_Line_weighted(self, line_id):
        #gibt Strecke zu gegebener Line_weighted ID zurueck

        line = self.getLine_weighted_byID(id)
        p1 = self.getPoint_byID(line.getPointID1())
        p2 = self.getPoint_byID(line.getPointID2())
        return math.sqrt((p1.getX()-p2.getX())**2+(p1.getY()-p2.getY())**2)

    def getDifference_XandY_Line_weighted(self, line_id):
        #gibt Differenzen von X und Y als 2 Werte zu gegebener Line_weighted ID zurueck

        line = self.getLine_weighted_byID(line_id)
        p1 = self.getPoint_byID(line.getPointID1())
        p2 = self.getPoint_byID(line.getPointID2())

        return p1.getX()-p2.getX(), p1.getY()-p2.getY()

    def getNormalenvektor_byLine_weighted_ID(self, id):
        #hier wird der gewichtete Normalenvektor berechnet

        #das Gewicht der Kante ist einzubeziehen
        #und die Richtung ist wichtig! weil ja nach Innen das Polygon geschrupft werden soll
        #Richtungsvektor nach Links/ Innen zeigend: (-delta_y, delta_x)
        delta_x, delta_y = self.getDifference_XandY_Line_weighted(id)

        #Normieren! auf Betrag/ Laenge 1 bringen
        #eventuell doch nicht???
        betrag = math.sqrt(delta_x**2 + delta_y**2)

        x = 0
        y = 0

        if betrag!=0:
            #normieren:
            nX = -1.0 * delta_y
            nY = delta_x

            #mit Gewicht der Kante multiplizieren!  evt. auch einen globalen Paramter "Faktor" einfuehren, der noch multipliziert wird...
            line = self.getLine_weighted_byID(id)
            x = nX * line.getWeight()
            y = nY * line.getWeight()

            del nX, nY, line

        else:
            Print('ACHTUNG: Normalenvektor mit Betrag = 0, line_weighted id: ' + str(id))


        return x, y


    def getOrientatedActivePointIDList(self, zyklusnr=-1):
        #nimm alle Punkt ID die im gegebenen Zyklus aktiv sind und sortiere sie gegen den UZS
        #falls am Ende noch nicht alle Punkte genutzt wurden, gehe diese wieder durch
        #mache dies solange bis es keine ungenutzten Punkte mehr gibt

        #OUTPUT ist ein Array 2D, pro Linienzug/ Polygon eine eigene Punktliste!
        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        #zuerst die aktiven Punkte IDs als Linienzug sortieren
        arrAktiveLine_weightedID = self.__ListeCycleObjects[zyklusnr].getAllActiveLine_weighted()
        arrAktivePunkteID = self.__ListeCycleObjects[zyklusnr].getAllActivePointID()

        output_2D_Array = []

        while len(arrAktivePunkteID) > 0:
        #gehe so lange durch die aktiven Punkt, und bilde sortierte orientierte Linienzuege, bis keine Punkte mehr uebrig sind!

##        print('aktive Punkte: ')
##        print(arrAktivePunkteID)
##        print('aktive Linien: ')
##        print(arrAktiveLine_weightedID)
            arrAktivePunkteID_sortiert = []
            genutzte_Line_weighted_ID = []
            #beginne mit Index 0 der dortigen PointID
            startID = arrAktivePunkteID[0]
            arrAktivePunkteID_sortiert.append(startID)
            #selektiere alle von dort weiterfuehrenden Line_weighted
            #reduziere die Liste der Line-weighted IDs auf die der gerade aktiven Line-weighted
            #falls mehr als eine Line existiert, nimm diejenigen, dessen andere PointID geringer ist

            #LINIENZUG aufbauen.
            #lege so eine neue Sortierung der aktiven Punkte an
            #solange, bis wir wieder beim Startpunkt angekommen sind
            nextPoint = startID
            zaehler = 0
            while 1 == 1:
                zaehler = zaehler+1
                aktuell = nextPoint

                result = self.getLine_weightedID_byGivenPointID(aktuell)
                #.valueList enthaelt alle gefundenen LinienID
                #zuerst die Linie zum Vorgaenger wieder loeschen um nicht rueckwaerts zu gehen
                if len(arrAktivePunkteID_sortiert) > 1:
                    #loesche Linie ID
                    result.valueList.remove(self.getLine_weightedID_byTwoGivenPointID(arrAktivePunkteID_sortiert[len(arrAktivePunkteID_sortiert)-2],aktuell))

                #nur Linien nehmen, die gerade aktiv sind - loesche alle die nicht aktiv sind
                lines = []
                for j in range(0, len(result.valueList)):
                    if arrAktiveLine_weightedID.count(result.valueList[j]) > 0:
                        lines.append(result.valueList[j])
                #target ID aus Line_weighted extrahieren
                targets = []
                for k in range(0, len(lines)):
                    current = self.getLine_weighted_byID(lines[k])
                    if current.getPointID1() != aktuell:
                        targets.append(current.getPointID1())
                    if current.getPointID2() != aktuell:
                        targets.append(current.getPointID2())
                    del current
                #gib bei mehreren next points den mit der kleinsten ID zurueck
                nextPoint = min(targets)

                #wann wird die Schleife gestoppt:
                if nextPoint==startID:
                    break
                if zaehler > 100000:
                    break

                # genutzte Linie ID anhaengen
                genutzte_Line_weighted_ID.append(self.getLine_weightedID_byTwoGivenPointID(aktuell, nextPoint))

                arrAktivePunkteID_sortiert.append(nextPoint)

                del result, lines, targets

            print('Linienzug zusammenhaengend (Point IDs):')
            print(arrAktivePunkteID_sortiert)


            #nun die genutzten Punkte und Linien aus arrAktivePunkteID und arrAktiveLine_weightedID loeschen!
            for m in range(0, len(arrAktivePunkteID_sortiert)):
                arrAktivePunkteID.remove(arrAktivePunkteID_sortiert[m])

            for m in range(0, len(genutzte_Line_weighted_ID)):
                arrAktiveLine_weightedID.remove(genutzte_Line_weighted_ID[m])

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

            print('Linienzug gegen UZS (Point IDs): ')
            print(arrAktivePunkteID_sortiert)
            del summe
            del startID

            #Punkte Liste an output anhaengen
            output_2D_Array.append(arrAktivePunkteID_sortiert)
        #returnObject mit Array zurueckgeben!
        retour = returnObject('aktive Point2D wurden orientiert und sortiert', 'yes', -1, output_2D_Array)

        return retour

    def triangulate(self, zyklusnr=-1):
        #hier wird die Triangulation mit den aktiven Points aus diesem Zyklus durchgefuehrt

        #wenn die Zyklusnr. fuer den die Triangulation berechnet werden soll NICHT angegeben wurde, nimm die zuletzt hinzugefuegte
        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        print('++++++++++++++++++++++++++++++++')
        print('Triangulation fuer Zyklus Nr.: ' + str(zyklusnr))
        #die entstehenden Dreiecke werden aber zuerst in Skeleton_object der Liste Dreiecke angehaengt
        #und dann ihre IDs als aktive Dreiecke hier vermerkt


        #fuer die importierte Function 'ptri.polygon_triangulate' benoetigen wir die Punkte entgegen dem Uhrzeigersinn!

        #zuerst die aktiven Punkte IDs als Linienzug sortieren
        arrAktiveLine_weightedID = self.__ListeCycleObjects[zyklusnr].getAllActiveLine_weighted()


        arrAktivePunkteID = self.__ListeCycleObjects[zyklusnr].getAllActivePointID()
        arrAktivePunkteID_sortiert = []

        print('aktive Punkte: ')
        print(arrAktivePunkteID)
        print('aktive Linien: ')
        print(arrAktiveLine_weightedID)

        #beginne mit Index 0 der dortigen PointID
        startID = arrAktivePunkteID[0]
        arrAktivePunkteID_sortiert.append(startID)
        #selektiere alle von dort weiterfuehrenden Line_weighted
        #reduziere die Liste der Line-weighted IDs auf die der gerade aktiven Line-weighted
        #falls mehr als eine Line existiert, nimm diejenigen, dessen andere PointID geringer ist

        #lege so eine neue Sortierung der aktiven Punkte an
        #solange, bis wir wieder beim Startpunkt angekommen sind
        nextPoint = startID
        zaehler = 0
        while 1 == 1:
            zaehler = zaehler+1

            aktuell = nextPoint

            result = self.getLine_weightedID_byGivenPointID(aktuell)
            #.valueList enthaelt alle gefundenen LinienID
            #zuerst die Linie zum Vorgaenger wieder loeschen um nicht rueckwaerts zu gehen
            if len(arrAktivePunkteID_sortiert) > 1:
                #loesche Linie ID
                result.valueList.remove(self.getLine_weightedID_byTwoGivenPointID(arrAktivePunkteID_sortiert[len(arrAktivePunkteID_sortiert)-2],aktuell))

            #nur Linien nehmen, die gerade aktiv sind - loesche alle die nicht aktiv sind
            for j in range(0, len(result.valueList)):
                if arrAktiveLine_weightedID.count(result.valueList[j]) == 0:
                    result.valueList.pop(j)
            #target ID aus Line_weighted extrahieren
            targets = []
            for k in range(0, len(result.valueList)):
                current = self.getLine_weighted_byID(result.valueList[k])
                if current.getPointID1() != aktuell:
                    targets.append(current.getPointID1())
                if current.getPointID2() != aktuell:
                    targets.append(current.getPointID2())
                del current
            #gib bei mehreren next points den mit der kleinsten ID zurueck
            nextPoint = min(targets)


            if nextPoint==startID:
                break
            if zaehler > 100000:
                break
            arrAktivePunkteID_sortiert.append(nextPoint)

        print('Linienzug zusammenhaengend (Point IDs):')
        print(arrAktivePunkteID_sortiert)

        #pruefe, ob die Punkte nun im Uhrzeigersinn orientiert sind, oder nicht

        #folgender Algorithmus:
        #summe uber strecken: (x2-x1)(y2+y1). Wenn Ergebnis positiv ist es im Uhrzeigersinn. Wenn negativ, dann gegen UZS
        sum = 0
        for m in range(0, len(arrAktivePunkteID_sortiert)):
            if m == len(arrAktivePunkteID_sortiert)-1:

                produkt = (self.getPoint_byID(arrAktivePunkteID_sortiert[0]).getX()-self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getX()) * (self.getPoint_byID(arrAktivePunkteID_sortiert[0]).getY()+self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getY())
                sum = sum + produkt
                del produkt
            else:
                produkt = (self.getPoint_byID(arrAktivePunkteID_sortiert[m+1]).getX()-self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getX()) * (self.getPoint_byID(arrAktivePunkteID_sortiert[m+1]).getY()+self.getPoint_byID(arrAktivePunkteID_sortiert[m]).getY())
                sum = sum + produkt
                del produkt
        print(sum)
        #kehre evt. die Reihenfolge um, wenn Sum positiv ist:
        if sum > 0:
            arrAktivePunkteID_sortiert.reverse()

        print('Linienzug gegen UZS (Point IDs): ')
        print(arrAktivePunkteID_sortiert)
        del sum
        del startID


        #nun koennen letzte Vorbereitungen fuer den Triangulations-Algorithmus getroffen werden:
        n = len(arrAktivePunkteID_sortiert)

        listx = []
        listy = []
        for i in range(0, len(arrAktivePunkteID_sortiert)):
            listx.append(self.getPoint_byID(arrAktivePunkteID_sortiert[i]).getX())
            listy.append(self.getPoint_byID(arrAktivePunkteID_sortiert[i]).getY())

        x = np.array ( listx )
        y = np.array ( listy )
        #und nun Triangulieren!!! genutzt wird eine externe Ressource
        triangles = ptri.polygon_triangulate ( n, x, y )
#        print(triangles)
#        print(triangles[0,0])

        ptri.i4mat_print ( n - 2, 3, triangles, '  Dreiecke der Triangulation: ' )


        del listx, listy, n


        #nun koennen die neuen Dreiecke angelegt werden
        #WICHTIG!!! die IDs muessen wieder in die Korrekten PointIDs zurueckueberfuehrt werden!!!

        #es handelt sich um ein numpy array
        lengthRow = np.size(triangles, 0)
        lengthCol = np.size(triangles, 1)

        #loop over Dreiecke
        for o in range(0, lengthRow):
            tri = Dreieck(arrAktivePunkteID_sortiert[triangles[o, 0]], arrAktivePunkteID_sortiert[triangles[o, 1]], arrAktivePunkteID_sortiert[triangles[o, 2]])
            result = self.add_Dreieck(tri)
            print(result.message)


            #und auch Dreiecke als aktiv setzen, die ID wird beim addDreieck zurueckgegeben
            self.addActiveDreieckID(result.value, zyklusnr)
            del tri



        del lengthCol, lengthRow


        return






    def moveAllActivePoints(self, verstricheneZeit, zyklusnr=-1):
        #bewege alle aktiven Punkte nach Innen
        #verwende die Bewegungsvektoren, die die Punkte jeweils in sich gespeichert haben

        #vollziehe die Bewegung um genau den Faktor = verstrichene Zeit
        #fuer die Zeit koennte evt auch spaeter ein numpy.float128 anstelle dem Python float() verwendet werden, um eine hoehre Praezision zu erreichen!

        #wenn die Zyklusnr. fuer den die Bewegungsvektoren berechnet werden soll NICHT angegeben wurde, nimm die zuletzt hinzugefuegte
        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        print('++++++++++++++++++++++++++++++++')
        print('Verschiebe aktive Punkte fuer Zyklus Nr.: ' + str(zyklusnr) + ' verstrichene Zeit: ' + str(verstricheneZeit))


        #setze die verstrichene Zeit im aktuellen Cycle! --> die Laufzeit
        self.__ListeCycleObjects[zyklusnr].setVerstricheneZeit(verstricheneZeit)

        #hole die orientierten sortierten Linienzuege des akteullen Zyklus
        result3 = self.getOrientatedActivePointIDList(zyklusnr)
        orientatedPoints = result3.valueList
        print(orientatedPoints)
        del result3
        print('Anzahl an Linienzuegen: ' + str(len(orientatedPoints)))


        #Liste
        returnList = []

        #gehe alle Linienzuege durch /es kann bei SPlit-Event mehr als einen geben!
        for v in range(0, len(orientatedPoints)):

            #loop over active points
            for i in range(0, len(orientatedPoints[v])):
                #bewege jeden einzelnen aktiven Punkt
                print('bewege Punkt ID: ' + str(orientatedPoints[v][i]))

                #hole aktuellen Punkt und verwende seinen Bewegungsvektor sowie die verstrichene Zeit t fuer die Neupunktberechnung!
                punkt_aktuell = self.getPoint_byID(orientatedPoints[v][i])
                p_x = punkt_aktuell.getX()
                p_y = punkt_aktuell.getY()
                v_x, v_y = punkt_aktuell.getBewegungsvektor()

                #Koordinaten des neuen Punktes berechnen: in Abhaengigkeit zu dem Bewegungsvektor und der verstrichenen Zeit
                neu_x = p_x + verstricheneZeit * v_x
                neu_y = p_y + verstricheneZeit * v_y

                #neuen Punkt erstellen
                neuer_punkt = Point2D(neu_x, neu_y)
                neuer_punkt.setBewegungsvektor(v_x, v_y)

                #Punkt im Storage hinzuefuegen. Falls noch nicht existiert
                result = self.addPoint2D(neuer_punkt)
                print(result.message)

                #an Abbildungs-Array die neue Kombination anhaengen, falls schon existiert, dann genau diese ID
                #die Abbildung der alten Punkte auf die neuen Punkte als Tupel der valueList im returnObject zurueckgeben
                #damit koennen dann in der neuen Cycle-Object die Kanten und Dreiecke... verschoben werden
                #Liste mit zwei Spalten... [id_alt, id_neu]
                returnList.append([orientatedPoints[v][i], result.value])

                del punkt_aktuell, p_x, p_y, v_x, v_y, neu_x, neu_y, neuer_punkt, result


            print(returnList)
        #Bewegungsvektoren/ Line_move erstellen!!!
        for s in range(0, len(returnList)):
            #erstelle Line_move
            line = Line_move(returnList[s][0], returnList[s][1], zyklusnr)
            result = self.add_Line_move(line)
            print(result.message)

            # aktiv setzen
            self.addActiveLine_moveID(result.value, zyklusnr)
            del line, result

        #************************ N E U E R    Z Y K L U S ********************************************

        #neuer Zyklus wird generiert!
        self.add_CycleObject(Cycle_Object())
        print('++++ neuer Zyklus wurde generiert! ++++')
        #anhand der Abbildung Punkte_alt auf Punkte_neu koennen nun ...
        #... die neuen aktiven Punkte ID eingetragen werden:  (Duplikate werden automatisch nicht erstellt, siehe .addActivePointID()
        for s in range(0, len(returnList)):
            self.addActivePointID(returnList[s][1], zyklusnr+1)

        #... die aktiven Kanten geupdatet werden und neu erstellt werden!
        activeLine_weighted = self.getAllActiveLine_weighted(zyklusnr)
        print('active Line_weighted: ' + str(activeLine_weighted))
        outputListeLine_weighted = []
        for s in range(0, len(activeLine_weighted)):
            line = self.getLine_weighted_byID(activeLine_weighted[s])
            #ermittle neue Punkt ID , suche zuerst die Position der alten Punkt im returnList Array
            pos1 = 0
            pos2 = 0
            for t in range(0, len(returnList)):

                if returnList[t][0] == line.getPointID1():
                    pos1 = t
                if returnList[t][0] == line.getPointID2():
                    pos2 = t
            result = self.add_Line_weighted(Line_weighted(returnList[pos1][1], returnList[pos2][1], line.getWeight(), zyklusnr+1))
            print(result.message)
            #aktiv setzen
            self.addActiveLine_weightedID(result.value, zyklusnr+1)
            outputListeLine_weighted.append([activeLine_weighted[s], result.value])
            del line , pos1, pos2, result
        del activeLine_weighted

        #... die aktiven Dreiecke geupdatet werden... und neu erstellt werden!
        activeDreiecke = self.getAllActiveDreiecke(zyklusnr)

        print('active Dreiecke: ' + str(activeDreiecke))



        outputListDreiecke = []
        for s in range(0, len(activeDreiecke)):
            #bilde neue Dreiecke
            dreieck = self.getDreieck_byID(activeDreiecke[s])
            #ermittle neue Punkt ID , suche zuerst die Position der alten Punkt im returnList Array
            pos1 = 0
            pos2 = 0
            pos3 = 0
            for t in range(0, len(returnList)):

                if returnList[t][0] == dreieck.getPointID1():
                    pos1 = t
                if returnList[t][0] == dreieck.getPointID2():
                    pos2 = t
                if returnList[t][0] == dreieck.getPointID3():
                    pos3 = t
            result = self.add_Dreieck(Dreieck(returnList[pos1][1], returnList[pos2][1], returnList[pos3][1]))
            print(result.message)
            #aktiv setzen
            self.addActiveDreieckID(result.value, zyklusnr+1)
            outputListDreiecke.append([activeDreiecke[s], result.value])


            del dreieck, pos1, pos2, pos3, result

        return returnList, outputListeLine_weighted, outputListDreiecke


    def calculateCollapsTime_ofActiveTriangles(self, zyklusnr=-1):
        #wenn die Zyklusnr. fuer den die Collapse Times berechnet werden soll NICHT angegeben wurde, nimm die zuletzt hinzugefuegte
        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        print('++++++++++++++++++++++++++++++++')
        print('berechne Collapse Times fuer Zyklus Nr.: ' + str(zyklusnr))

        #fuer alle aktiven Dreiecke des gegebenen Zyklus: berechne jeweils die CollapsTime t, also wann das Dreieck zusammenklappen wird/ Area = gleich Null/ Kollinearitaet der Punkte
        activeTriangles = self.getAllActiveDreiecke(zyklusnr)
        #gehe die aktiven Dreiecke durch
        for s in range (0, len(activeTriangles)):
            dreieck_aktuell = self.getDreieck_byID(activeTriangles[s])
            #hole dir die Punkte
            punkt_o1 = self.getPoint_byID(dreieck_aktuell.getPointID1())
            punkt_o2 = self.getPoint_byID(dreieck_aktuell.getPointID2())
            punkt_o3 = self.getPoint_byID(dreieck_aktuell.getPointID3())

            o1_x = punkt_o1.getX()
            o1_y = punkt_o1.getY()
            o2_x = punkt_o2.getX()
            o2_y = punkt_o2.getY()
            o3_x = punkt_o3.getX()
            o3_y = punkt_o3.getY()

            #sektiere jeweils pro Punkt die passenden Bewegungsvektoren aus dem aktuellen Zyklus
            s1_x, s1_y = punkt_o1.getBewegungsvektor()
            s2_x, s2_y = punkt_o2.getBewegungsvektor()
            s3_x, s3_y = punkt_o3.getBewegungsvektor()

            #berechne die Zeit t
            #es kann eine, zwei oder gar keine Loesungen geben

            #umsetzen der P-Q-Formel fuer Quadratische Formeln
##            faktor_Grad2 = 1.0 * (s1_y * s2_x + s1_x * s2_y + s1_y * s3_x - s2_y * s3_x - s1_x * s3_y + s2_x * s3_y)
##            faktor_Grad1 = 1.0 * (o2_y * s1_x - o3_y * s1_x - o2_x * s1_y + o3_x * s1_y - o1_y * s2_x + o3_y * s2_x + o1_x * s2_y - o3_x * s2_y + o1_y * s3_x - o2_y * s3_x - o1_x * s3_y + o2_x * s3_y)
##            faktor_Grad0 = 1.0 * (-1.0 * o1_y * o2_x + o1_x * o2_y + o1_y * o3_x - o2_y * o3_x - o1_x * o3_y + o2_x * o3_y)

            faktor_Grad2 = 1.0 * (s2_x*s3_y + s1_x*s2_y + s1_y*s3_x - s2_x*s1_y - s3_x*s2_y - s3_y*s1_x)
            faktor_Grad1 = 1.0 * (s2_x*o3_y + s3_y*o2_x + s1_x*o2_y + s2_y*o1_x + s1_y*o3_x + s3_x*o1_y - s2_x*o1_y - s1_y*o2_x - s3_x*o2_y - s2_y*o3_x - s3_y*o1_x - s1_x*o3_y)
            faktor_Grad0 = 1.0 * (o2_x*o3_y + o1_x*o2_y + o1_y*o3_x - o2_x*o1_y - o3_x*o2_y - o3_y*o1_x)

            #in die Normalform bringen (bei x^2 kein Faktor mehr stehen)
            p = faktor_Grad1 / faktor_Grad2
            q = faktor_Grad0 / faktor_Grad2
            radikant = (p * 0.5) * (p * 0.5) - q

            #loesen und Anzahl Loesungen verarbeiten!
            zeit = 0.0
            #Anzahl Loesungen
            if radikant < 0:
                zeit = -1.0
                #keine Loesungen
            if radikant == 0:
                #eine Loesung
                zeit = -1.0 * p * 0.5
            if radikant > 0:
                #bei zwei Loesungen
                t1 = -1.0 * p * 0.5 + math.sqrt(radikant)
                t2 = -1.0 * p * 0.5 - math.sqrt(radikant)
                if (min(t1, t2) < 0) and (max(t1, t2) >= 0):
                    zeit = max(t1, t2)
                if (t1 >= 0) and (t2 >= 0):
                    zeit = min(t1, t2)
                if (t1 < 0) and (t2 < 0):
                    zeit = -1.0
                del t1, t2
            print('fuer Dreieck ID: ' + str(dreieck_aktuell.getID()) + ' Collapes Time t = ' + str(zeit))
            #es reicht die kuerzere Zeit bei zwei Loesungen zu nehmen. Wenn es nicht zusammenklappt, dann -1.0 also unendlich!

            #setze die Zeit t beim Dreieck!
            self.__triangulation[activeTriangles[s]].setCollapseTime(zeit)

            del zeit, dreieck_aktuell, punkt_o1, punkt_o2, punkt_o3, o1_x, o1_y, o2_x, o2_y, o3_x, o3_y
            del s1_x, s1_y, s2_x, s2_y, s3_x, s3_y, faktor_Grad0, faktor_Grad1, faktor_Grad2, p, q, radikant

        return

    def handle_Event(self, zyklusnr=-1):
        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        print('++++++++++++++++++++++++++++++++')
        print('handle Events fuer Zyklus Nr.: ' + str(zyklusnr))
        #ermittle das Dreieck mit der kleinsten Collapse-Time (WICHTIG: ohne -1.0 und -2.0 Werte)
        activeDreiecke = self.getAllActiveDreiecke(zyklusnr)

        #zwei Listen anlegen: 1x mit DreieckID und 1x mit CollapseTime, verknuepft ueber die Listen-Index
        listDreieckID = []
        listCollapseTime = []
        #loop over active Dreieck
        for s in range(0, len(activeDreiecke)):
            dreieck = self.getDreieck_byID(activeDreiecke[s])
            listDreieckID.append(activeDreiecke[s])
            listCollapseTime.append(dreieck.getCollapseTime())
            del dreieck
        print('Collapse Time von Dreiecken: ' + str(listCollapseTime))
        print('ID Liste: ' + str(listDreieckID))
        #minimale CollapseTime ermitteln
        print('minimale Collapse Time von Dreiecken: ' + str(min(listCollapseTime)))

        print('Anzahl Dreiecke mit minimaler Collapse Time: ' + str(listCollapseTime.count(min(listCollapseTime))))
        anzahlDreiecke = listCollapseTime.count(min(listCollapseTime))

        #was passiert, wenn mehrere Dreiecke eine gleiche Zeit haben???
        #der normale Fall ist, dass es genau ein Dreieck gibt, welches zusammenklappt
        #wenn es mehrere gibt, dann mussen dort jeweils die Event-Typen bestimmt werden, aber auch Topologie/ Nachbarschaft...
        #also gemeinsame Kanten, Punkte... etc..
        if anzahlDreiecke == 1:
            #--------------bei genau einem Dreieck mit minimaler Collapse Time-----------------
            #Dreieck ID bestimmen
            aktuelles_Dreieck_ID = listDreieckID[listCollapseTime.index(min(listCollapseTime))]
            print(aktuelles_Dreieck_ID)

            #lege ein neues Event in der EvenList an
            event_aktuell = Event(zyklusnr, aktuelles_Dreieck_ID)

            #zuerst alle Punkte verschieben um den minimalen Collapse Time
            #... dabei wird ein neuer ZYKLUS erstellt!!!
            #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            updateListPoint, updateList_Line_weighted, resultListDreieck = self.moveAllActivePoints(min(listCollapseTime))

            #die Return List enthaelt Tupel mit alter und neuer Dreiecks-ID , ebenfalls fuer Punkte und Line_weighted
            #ID von dem nun zusammengeklappten Dreieck im neuen Zyklus erhalten

            dummyList = []
            for i in range(0, len(resultListDreieck)):
                dummyList.append(resultListDreieck[i][0])
            ID_dreieck_gecrashed = resultListDreieck[dummyList.index(aktuelles_Dreieck_ID)][1]
            print('Dreieck vorher ID: ' + str(aktuelles_Dreieck_ID) + ' ; neues zusammengeklapptes Dreieck ID: ' + str(ID_dreieck_gecrashed))

            #ermittle die Art des Events...


            #-alte Dreieck ID und neue Dreieck ID (vom zusammengeklappten Dreieck) ist nun ermittelt worden
            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #+++++++++ ANALYSE MATRIX +++++++++++++
            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

            #3 Spalten: 1x Kante (P1P2) 1x Kante (P2P3) 1x Kante (P3P1)

            #5 Zeilen:

            #-Kante IDs (neu)
            #-Kantentyp (neu) Legende -1 =unbekannt, 1=spoke, 2=Wavefront-Kante
            #Kantenlaenge (neu)
            #-die der Kante jeweils gegenueberliegenden Punkte (neu)
            #-die drei jetzigen benachbarten Dreiecke

            #Matrix hat 3 Spalten und 5 Zeilen. Default-Werte ist jeweils -1.0
            #ein numpy-Array!
            analyseMatrix = np.full((5,3), -1.0, dtype=np.float64)

            #Werte fuellen - altes und neues (zusammengeklapptes/ gecrashedes ) Dreieck holen
            dreieck_gecrashed = self.getDreieck_byID(ID_dreieck_gecrashed)
            p1_neu = self.getPoint_byID(dreieck_gecrashed.getPointID1())
            p2_neu = self.getPoint_byID(dreieck_gecrashed.getPointID2())
            p3_neu = self.getPoint_byID(dreieck_gecrashed.getPointID3())
            print('Punkte neu ' + str(p1_neu.getID()) + ' ; ' + str(p2_neu.getID()) + ' ; ' + str(p3_neu.getID()))

            dreieck_alt = self.getDreieck_byID(aktuelles_Dreieck_ID)
            p1_alt = self.getPoint_byID(dreieck_alt.getPointID1())
            p2_alt = self.getPoint_byID(dreieck_alt.getPointID2())
            p3_alt = self.getPoint_byID(dreieck_alt.getPointID3())
            print('Punkte alt ' + str(p1_alt.getID()) + ' ; ' + str(p2_alt.getID()) + ' ; ' + str(p3_alt.getID()))

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #fuer 5. ZEILE:
            #benachbarte Dreiecke selektieren ueber zwei gemeinsame Punkte der gemeinsamen Kante (neue Dreiecke)
            #wichtig! Dieser Vergleich mit den vorherigen alten Punkten machen...und dann zu den gefundenen Dreiecken die ID updaten auf den neuen Zyklus
            list_12 = self.getDreieck_byTwoGivenPointID(dreieck_alt.getPointID1(), dreieck_alt.getPointID2())
            print(list_12)
            list_23 = self.getDreieck_byTwoGivenPointID(dreieck_alt.getPointID2(), dreieck_alt.getPointID3())
            print(list_23)
            list_31 = self.getDreieck_byTwoGivenPointID(dreieck_alt.getPointID3(), dreieck_alt.getPointID1())
            print(list_31)
            print('returnList: ID Dreieck alt --> Id Dreieck Neu')
            print(resultListDreieck)

            #pruefen ob ueberhaupt benachbarte Dreiecke gefunden wurden
            #die eigene ID des alten Dreieckes loeschen , es soll nur Nachbarn und nicht das aktuelle Dreieck gespeichert werden
            if len(list_12) == 0 or len(list_12) == 1:
                analyseMatrix[4,0] = -1.0
            if len(list_23) == 0 or len(list_23) == 1:
                analyseMatrix[4,1] = -1.0
            if len(list_31) == 0 or len(list_31) == 1:
                analyseMatrix[4,2] = -1.0

            #aktive Dreieckes ID von vorherigen Zyklus laden, zum Abgleich:
            activeDreiecke_vorherigerZyklus = self.getAllActiveDreiecke(zyklusnr)
            print('active Dreiecke vorheriger Zyklus: ' + str(activeDreiecke_vorherigerZyklus))

            if len(list_12) > 1:
                list_12.remove(aktuelles_Dreieck_ID)
                if activeDreiecke_vorherigerZyklus.count(list_12[0]) > 0:
                    analyseMatrix[4,0] = resultListDreieck[dummyList.index(list_12[0])][1]
                else:
                    analyseMatrix[4,0] = -1.0

            if len(list_23) > 1:
                list_23.remove(aktuelles_Dreieck_ID)
                if activeDreiecke_vorherigerZyklus.count(list_12[0]) > 0:
                    analyseMatrix[4,1] = resultListDreieck[dummyList.index(list_23[0])][1]
                else:
                    analyseMatrix[4,1] = -1.0

            if len(list_31) > 1:
                list_31.remove(aktuelles_Dreieck_ID)
                if activeDreiecke_vorherigerZyklus.count(list_12[0]) > 0:
                    analyseMatrix[4,2] = resultListDreieck[dummyList.index(list_31[0])][1]
                else:
                    analyseMatrix[4,2] = -1.0

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #fuer 1. ZEILE
            #Kanten IDs fuer die drei Kanten (falls es Edges/ Wavefront - Kanten sind! nicht bei Spokes) (neue Kanten)
            #wenn kein Treffer wird automatisch eine -1 zurueckgegeben

            #ueber alte Kanten im nicht zusammengeklappten gehen und dann die neuen daraus selektieren
            k1 = self.getLine_weightedID_byTwoGivenPointID(p1_alt.getID(), p2_alt.getID())
            k2 = self.getLine_weightedID_byTwoGivenPointID(p2_alt.getID(), p3_alt.getID())
            k3 = self.getLine_weightedID_byTwoGivenPointID(p3_alt.getID(), p1_alt.getID())


            dummyListLine_weighted = []
            for i in range(0, len(updateList_Line_weighted)):
                dummyListLine_weighted.append(updateList_Line_weighted[i][0])

            if k1 == -1:
                analyseMatrix[0,0] = -1
            else:
                analyseMatrix[0,0] = updateList_Line_weighted[dummyListLine_weighted.index(k1)][1]

            if k2 == -1:
                analyseMatrix[0,1] = -1
            else:
                analyseMatrix[0,1] = updateList_Line_weighted[dummyListLine_weighted.index(k2)][1]

            if k3 == -1:
                analyseMatrix[0,2] = -1
            else:
                analyseMatrix[0,2] = updateList_Line_weighted[dummyListLine_weighted.index(k3)][1]

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #fuer 2. ZEILE
            #kantentypen suchen:
            #wenn eine Line_weighted/ Kanten-ID gefunden wurde, dann ist die Seite eine Wavefront-Kante! also = 2
            #wenn keine gefunden wurde, ist es eine Spoke, eine sonstige Dreieckesseite... also = 1
            if analyseMatrix[0,0] == -1:
                analyseMatrix[1,0] = 1
            else:
                analyseMatrix[1,0] = 2

            if analyseMatrix[0,1] == -1:
                analyseMatrix[1,1] = 1
            else:
                analyseMatrix[1,1] = 2

            if analyseMatrix[0,2] == -1:
                analyseMatrix[1,2] = 1
            else:
                analyseMatrix[1,2] = 2

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #fuer 3. ZEILE
            #Kantenlaengen fuer die drei Kanten (neue Kanten)
            analyseMatrix[2,0] = math.sqrt((p1_neu.getX() - p2_neu.getX())**2 + (p1_neu.getY() - p2_neu.getY())**2)
            analyseMatrix[2,1] = math.sqrt((p2_neu.getX() - p3_neu.getX())**2 + (p2_neu.getY() - p3_neu.getY())**2)
            analyseMatrix[2,2] = math.sqrt((p3_neu.getX() - p1_neu.getX())**2 + (p3_neu.getY() - p1_neu.getY())**2)

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #fuer 4. ZEILE
            #ID von gegenueber liegenden Punkt (neues Punkte)
            analyseMatrix[3,0] = p3_neu.getID()
            analyseMatrix[3,1] = p1_neu.getID()
            analyseMatrix[3,2] = p2_neu.getID()



            #Matrix ausgeben auf Konsole
            print('Analyse Matrix fuer Event: ')
            print(analyseMatrix)
            #entscheide dann, welcher Event-Typ vorliegt

            #+++++++++++ Event-Typ anhand der Matrix abpruefen ++++++++++++++
            event_type = ''
            #EDGE Event pruefen:
                #wenn mindestens eine Seite Laenge gleich Null hat gleichzeitig eine Wavefront-Kante ist (=2)
            if (analyseMatrix[1,0] == 2 and analyseMatrix[2,0] == 0) or (analyseMatrix[1,1] == 2 and analyseMatrix[2,1] == 0) or (analyseMatrix[1,2] == 2 and analyseMatrix[2,2] == 0):
                print('EDGE Event wurde erkannt')
                event_type = 'EDGE'

            #FLIP und SPLIT Event pruefen:
            if analyseMatrix[2,0] > 0 and analyseMatrix[2,1] > 0 and analyseMatrix[2,2] > 0:
                #wenn alle Seitenlaengen groesser Null sind (obwohl Dreieck Flaeche gleich Null)

                #finde laengste Seite:
                listFindeMaximum = [analyseMatrix[2,0], analyseMatrix[2,1], analyseMatrix[2,2]]

                if (analyseMatrix[2,0] == max(listFindeMaximum) and analyseMatrix[1,0] == 2) or (analyseMatrix[2,1] == max(listFindeMaximum) and analyseMatrix[1,1] == 2) or (analyseMatrix[2,2] == max(listFindeMaximum) and analyseMatrix[1,2] == 2):
                    #SPLIT , da laengste Seite eine Wavefront-Kante ist
                    print('SPLIT Event wurde erkannt')
                    event_type = 'SPLIT'
                if (analyseMatrix[2,0] == max(listFindeMaximum) and analyseMatrix[1,0] == 1) or (analyseMatrix[2,1] == max(listFindeMaximum) and analyseMatrix[1,1] == 1) or (analyseMatrix[2,2] == max(listFindeMaximum) and analyseMatrix[1,2] == 1):
                    #FLIP, da laengste Seite eine Spoke / Dreiecksseite ist, keine Wavefront Kante
                    print('FLIP Event wurde erkannt')
                    event_type = 'FLIP'

            #+++++++++++ anhand ermittelten event_type nun die Geometrien aktualisieren ++++++++++++
            if event_type == 'EDGE':
                # loesche die auf Laenge Null gegangene Kante aus den aktiven Line_weighted_IDs
                loescheKanteID = -1
                updatePunktID = -1
                if analyseMatrix[2,0] == 0:
                   loescheKanteID = analyseMatrix[0,0]
                   updatePunktID = analyseMatrix[3,0]
                if analyseMatrix[2,1] == 0:
                   loescheKanteID = analyseMatrix[0,1]
                   updatePunktID = analyseMatrix[3,1]
                if analyseMatrix[2,2] == 0:
                   loescheKanteID = analyseMatrix[0,2]
                   updatePunktID = analyseMatrix[3,2]

                self.__ListeCycleObjects[zyklusnr+1].removeActiveLine_weightedID_byID(loescheKanteID)
                del loescheKanteID
                #loesche das zusammengeklappte Dreieck!
                self.__ListeCycleObjects[zyklusnr+1].removeActiveDreieckID_byID(ID_dreieck_gecrashed)

                #Richtung und Geschwindigkeit des knoten aendern sich:
                #berechne fuer den Knoten einen neuen Bewegungsvektor
                self.calculate_Bewegungsvektor_byActivePointID([updatePunktID])

                del loescheKanteID, updatePunktID

            if event_type == 'FLIP':
                #ermittle die laengste Kante des zusammengeklappten Dreieckes
                nachbarDreieckID = -1
                gegenueberPunuktID = -1
                if (analyseMatrix[2,0] >  analyseMatrix[2,1]) and (analyseMatrix[2,0] >  analyseMatrix[2,2]):
                    nachbarDreieckID = analyseMatrix[4,0]
                    gegenueberPunuktID = analyseMatrix[3,0]
                if (analyseMatrix[2,1] >  analyseMatrix[2,0]) and (analyseMatrix[2,1] >  analyseMatrix[2,2]):
                    nachbarDreieckID = analyseMatrix[4,1]
                    gegenueberPunuktID = analyseMatrix[3,1]
                if (analyseMatrix[2,2] >  analyseMatrix[2,0]) and (analyseMatrix[2,2] >  analyseMatrix[2,1]):
                    nachbarDreieckID = analyseMatrix[4,2]
                    gegenueberPunuktID = analyseMatrix[3,2]

                #hole /get das benachbarte Dreieck
                nachbarDreieck = self.getDreieck_byID(int(nachbarDreieckID))

                #ermittle den Dreiecks-Punkt im benachbarten Dreieck, welcher nicht zum gecrashden Dreieck gehoert
                nachbarPunkte = [nachbarDreieck.getPointID1(), nachbarDreieck.getPointID2(), nachbarDreieck.getPointID3()]
                print('Punkte benachbartes Dreieck: ' + str(nachbarPunkte))
                dreieckPunkte = [analyseMatrix[3,0], analyseMatrix[3,1], analyseMatrix[3,2]]
                #Schnittmenge bilden mit den beiden gemeinsamen Punkten , fuer die beidne neuen Dreiecke
                gemeinsamePunkte = list(set(nachbarPunkte) & set(dreieckPunkte))
                print('gemeinsame Punkte: ' + str(gemeinsamePunkte))

                #falls der Fall eintritt, dass  nachbardreieck und aktuelles dreieck gleiche punkte haben:
                if set(dreieckPunkte) == set(nachbarPunkte):
                     print('ACHTUNG identische Dreiecke')
                     return


                try:
                    nachbarPunkte.remove(analyseMatrix[3,0])
                except ValueError:
                    pass
                try:
                    nachbarPunkte.remove(analyseMatrix[3,1])
                except ValueError:
                    pass
                try:
                    nachbarPunkte.remove(analyseMatrix[3,2])
                except ValueError:
                    pass

                #nachdem alle gemeinsamen Punkte wieder abgezogen wurden, musste der gewuenschte Punkt auf Index [0] uebrig bleiben


                #loesche das benachbarte Dreieck
                self.__ListeCycleObjects[zyklusnr+1].removeActiveDreieckID_byID(ID_dreieck_gecrashed)

                #erstelle zwei Neue Dreiecke
                result = self.add_Dreieck(Dreieck(int(gemeinsamePunkte[0]), int(nachbarPunkte[0]), int(gegenueberPunuktID)))
                print(result.message)
                #aktiv setzen
                self.addActiveDreieckID(result.value, zyklusnr+1)
                del result
                result = self.add_Dreieck(Dreieck(int(gemeinsamePunkte[1]), int(nachbarPunkte[0]), int(gegenueberPunuktID)))
                #aktiv setzen
                self.addActiveDreieckID(result.value, zyklusnr+1)
                del result

            del dummyList, event_type, analyseMatrix

        if anzahlDreiecke > 1:
            #was passiert, wenn mehrere Dreiecke eine gleiche Zeit haben???
            #der normale Fall ist, dass es genau ein Dreieck gibt, welches zusammenklappt
            #wenn es mehrere gibt, dann mussen dort jeweils die Event-Typen bestimmt werden, aber auch Topologie/ Nachbarschaft...
            #also gemeinsame Kanten, Punkte... etc..
            pass
        return




    def calculate_Bewegungsvektor_byActivePointID(self, pointID_list, zyklusnr=-1):

        #hier wird fuer alle gegebenen Punkte aus der pointID_list der entsprechende Bewegungsvektor berechnet
        #der Bewegungsvektor steht fuer die Strecke, die dieser aktive Punkt in einer Zeiteinheit t=1 zuruecklegen wuerde...

        #dieser wird dann mit setBewegungsvektor diesem Punkt uebergeben...
        #aufgrund der Liste kann auch nur ein einzelner Punkt unter Umstaenden einen neuen Vektor bekommen (nach einem entsprechenden Event)

        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        print('++++++++++++++++++++++++++++++++')
        print('Bewegungsvektoren berechnen fuer Zyklus Nr.: ' + str(zyklusnr))
        print('fuer die Punkte ID List: ' + str(pointID_list))

        #hole die gegen den Uhrzeigersinn orientierte sortie Punkt-Liste aller aktiven Punkte im angefragten Zyklus
        #da auch mehrere Polygone zurueckgegeben werden koennen, muessen diese mit einer for-schleife durchlaufen werden...
        result3 = self.getOrientatedActivePointIDList(zyklusnr)
        orientatedPoints = result3.valueList
        print('orientierte Punkte: ' + str(orientatedPoints))
        del result3
        print('Anzahl an Linienzuegen/ Polygonen: ' + str(len(orientatedPoints)))

        #gehe alle Linienzuege durch /es kann nach einem SPlit-Event mehr als einen geben!
        for v in range(0, len(orientatedPoints)):

            #loop over active points
            for i in range(0, len(orientatedPoints[v])):
                #pruefe, ob dieser Punkt einer der in der PointIDListe angegeben Punkte ist!

                if pointID_list.count(orientatedPoints[v][i]) > 0:
                    #der Punkt soll einen neuen Bewegungsvektor bekommen!

                    print('berechne Bew-Vektor fuer Punkt ID: ' + str(orientatedPoints[v][i]))

                    #bestimme die 3 Punkte - ermittle Vorgaenger und Nachfolger
                    id1 = 0
                    id2 = 0
                    if i == 0:
                        id1 = len(orientatedPoints[v])-1
                        id2 = i+1
                    if i == len(orientatedPoints[v])-1:
                        id1 = i-1
                        id2 = 0
                    if (i > 0) and (i < len(orientatedPoints[v])-1):
                        id1 = i-1
                        id2 = i+1

                    punkt_aktuell = self.getPoint_byID(orientatedPoints[v][i])
                    punkt_vorgaenger = self.getPoint_byID(orientatedPoints[v][id1])
                    punkt_nachfolger = self.getPoint_byID(orientatedPoints[v][id2])
                    del id1, id2

                    #Linie 1/ Kante1 liegt zwischen aktuellem Punkt und dem Vorgaenger
                    kante1 = self.getLine_weighted_byID(self.getLine_weightedID_byTwoGivenPointID(punkt_vorgaenger.getID(), punkt_aktuell.getID()))
                    #Linie 2/ Kante2 liegt zwischen aktuellem Punkt und dem Nachfolger
                    kante2 = self.getLine_weighted_byID(self.getLine_weightedID_byTwoGivenPointID(punkt_aktuell.getID(), punkt_nachfolger.getID()))

                    #x,y Differenzen der Kanten berechnen fuer Linie l1 und Linie l2
                    l1_x = punkt_aktuell.getX() - punkt_vorgaenger.getX()
                    l1_y = punkt_aktuell.getY() - punkt_vorgaenger.getY()
                    l2_x = punkt_nachfolger.getX() - punkt_aktuell.getX()
                    l2_y = punkt_nachfolger.getY() - punkt_aktuell.getY()

                    #Normalen-Vektoren berechnen fuer die beiden Kanten (nach links in Kantenrichtung zeigend, da gegen den UZS orientiert = nach Innen zeigend!)
                    n1_x = -1 * l1_y
                    n1_y = l1_x
                    n2_x = -1 * l2_y
                    n2_y = l2_x

                    #normalen-Vektor normieren und mit Kantengewichten als Skalar multiplizieren
                    betrag_n1 = math.sqrt(n1_x**2 + n1_y**2)
                    betrag_n2 = math.sqrt(n2_x**2 + n2_y**2)

                    normal1_x = 0.0
                    normal1_y = 0.0
                    if betrag_n1 != 0:
                        normal1_x = kante1.getWeight() * (1 / betrag_n1) * n1_x
                        normal1_y = kante1.getWeight() * (1 / betrag_n1) * n1_y
                    else:
                        print('ACHTUNG: division by zero, Bewegungsvektor/ Normal1 fuer Point ID: ' + str(orientatedPoints[v][i]))

                    normal2_x = 0.0
                    normal2_y = 0.0
                    if betrag_n2 != 0:
                        normal2_x = kante2.getWeight() * (1 / betrag_n2) * n2_x
                        normal2_y = kante2.getWeight() * (1 / betrag_n2) * n2_y
                    else:
                        print('ACHTUNG: division by zero, Bewegungsvektor/ Normal2 fuer Point ID: ' + str(orientatedPoints[v][i]))

                    #die beiden neuen Geraden aufstellen, gleichsetzen und den gemeinsamen Schnittpunkt finden
                    #SCHNITTPUNKT zweier Geraden

#                    theta = (punkt_vorgaenger.getX() + normal1_x - punkt_nachfolger.getX() - normal2_x) / (punkt_nachfolger.getX() + punkt_vorgaenger.getX() - 2.0 * punkt_aktuell.getX())

                    #SUBSTITUTION mit a,b,c,d,e,f durchfuehren
                    a = punkt_nachfolger.getX() + normal2_x - punkt_vorgaenger.getX() - normal1_x
                    b = l2_x
                    c = l1_y
                    d = punkt_nachfolger.getY() + normal2_y - punkt_vorgaenger.getY() - normal1_y
                    e = l2_y
                    f = l1_x
                    #damit Beta ausrechnen
                    beta = 0.0
                    if (b * c - e * f) != 0:
                        beta = (d * f - a * c) / (b * c - e * f)
                    else:
                        print('division by zero!')

                    #Schnittpunkt anhand von dem Beta ausrechnen (wichtig: in gerade2 also kante 2 einsetzen!)
                    schnitt_x = punkt_nachfolger.getX() + normal2_x + beta * l2_x
                    schnitt_y = punkt_nachfolger.getY() + normal2_y + beta * l2_y

                    #bewegungsvektor berechnen, zwischen dem aktuellen Punkt und dem neu berechneten Schnittpunkt
                    v_x = schnitt_x - punkt_aktuell.getX()
                    v_y = schnitt_y - punkt_aktuell.getY()

                    #diesen Vektor nun mit set-Methode dem entsprechenden Punkt mitgeben!
                    self.__storagePoint2D[orientatedPoints[v][i]].setBewegungsvektor(v_x, v_y)

                    del kante1, kante2, l1_x, l1_y, l2_x, l2_y, n1_x, n1_y, n2_x, n2_y, v_x, v_y
                    del normal1_x, normal1_y, normal2_x, normal2_y
                    del punkt_aktuell, punkt_nachfolger, punkt_vorgaenger
                    del beta, a, b, c, d, e, f

        return

    def getTotalAreaOfActiveTriangles(self, zyklusnr=-1):
        #berechnet die Komplette Flaeche aller aktiven Dreiecke im gegeben Zyklus
        #ist ein Entscheidungskriterium fuer die WHILE Schleife, wann der Schrumpfungsprozess vorbei ist

        if zyklusnr==-1:
            zyklusnr=len(self.__ListeCycleObjects)-1

        print('++++++++++++++++++++++++++++++++')
        print('Gesamtflaeche (aller Dreiecke) berechnen fuer Zyklus Nr.: ' + str(zyklusnr))

        flaeche = 0.0

        activeDreiecke = self.__ListeCycleObjects[zyklusnr].getAllActiveDreiecke()

        #Anzahl Dreiecke untersuchen
        print('Anzahl aktiver Dreiecke: ' + str(len(activeDreiecke)))
        if len(activeDreiecke) == 0:
            pass
            #flacheninhalt bleibt bei null, keine Flaeche mehr vorhanden
        if len(activeDreiecke) > 0:

            for s in range(0, len(activeDreiecke)):

                dreieck = self.getDreieck_byID(activeDreiecke[s])
                p1 = self.getPoint_byID(dreieck.getPointID1())
                p2 = self.getPoint_byID(dreieck.getPointID2())
                p3 = self.getPoint_byID(dreieck.getPointID3())

                #SATZ des HERON
                a = math.sqrt((p2.getX() - p1.getX())**2 + (p2.getY() - p1.getY())**2)
                b = math.sqrt((p3.getX() - p2.getX())**2 + (p3.getY() - p2.getY())**2)
                c = math.sqrt((p1.getX() - p3.getX())**2 + (p1.getY() - p3.getY())**2)
                strecke = (a + b + c)  * 0.5
                dreieck_flaeche = math.sqrt(strecke * (strecke - a) * (strecke - b) * (strecke - c))
#                dreieck_flaeche = 0.5 * (p1.getX() * (p2.getY() - p3.getY()) + p2.getX() + (p3.getY() - p1.getY()) + p3.getX() * (p1.getY() - p2.getY()))
                flaeche = flaeche + dreieck_flaeche
                print('Dreieckflaeche fuer ID: ' + str(activeDreiecke[s]) + ' betraegt: ' + str(dreieck_flaeche))
                del dreieck, dreieck_flaeche, p1, p2, p3, a, b, c, strecke
        print('Gesamtflaeche: ' + str(flaeche))
        return flaeche



    def get_kanten(self):
        return self.__kanten

    def get_Polygon(self):
        #hier wird on-the-fly ein normales Polygon mit Punkt-Array ausgegeben
        #kopiere ersten Punkt an das Ende der Liste, fuer die Polygon Ausgabe
        pListe = self.__storagePoint2D
        pListe.append(self.__storagePoint2D[0])
        return pListe
##    def generate_Lines_from_PointStorage(self):
##        #falls Punkte-Anzahl in storagae mind. 2 betraegt, generiere jeweils zwischen nachfolgenden Punkten eine Objekt vom Typ Line_weighted
##        #und speichere es in der linien-Liste ab
##
##        return



    def toMatplotlib(self):
        #convert geometry data to draw in matplotlib

        return datastructure


    def toGeoJSON(self, filename):
        #geht alle Zyklen durch und erstellt jeweils die aktiven Punkte, Linien und Dreiecke als GeoJSON... eine Datei pro Gebaeude!

        #lade GeoJSON Template als Grundgeruest fuer die GeoJSON Datei
        with open(r'GeoJSON_template.geojson', 'r') as f:
            json_daten = json.load(f)

        #Feature Template
        feature_template = '{"type": "Feature", "properties": {"global_ID": 0}, "geometry": {"type": "LineString", "coordinates": []}}'


        #loop over zyklen
        global_id = 0

        for k in range(0, len(self.__ListeCycleObjects)):
            print('GeoJSON - Zyklus Nr: ' + str(k))


            #loop over aktive Points
            activePoints = self.getAllActivePointID(k)
            for m in range(0, len(activePoints)):

                point = self.getPoint_byID(activePoints[m])
                current_obj = json.loads(feature_template)
                current_obj['type'] = 'Feature'
                current_obj['properties']['ID'] = activePoints[m]
                current_obj['properties']['type'] = 'Point2D'
                current_obj['properties']['global_ID'] = global_id
                current_obj['properties']['zyklus_nr'] = k
                current_obj['geometry']['type'] = 'Point'
                current_obj['geometry']['coordinates'] = [point.getX(), point.getY()]
                global_id = global_id + 1


                json_daten['features'].append(current_obj)
                del current_obj, point


            activeLine_weighted = self.getAllActiveLine_weighted(k)
            #loop over aktive line_weighted
            for m in range(0, len(activeLine_weighted)):
                line = self.getLine_weighted_byID(activeLine_weighted[m])
                p1 = self.getPoint_byID(line.getPointID1())
                p2 = self.getPoint_byID(line.getPointID2())

                current_obj = json.loads(feature_template)
                current_obj['type'] = 'Feature'
                current_obj['properties']['ID'] = activeLine_weighted[m]
                current_obj['properties']['type'] = 'Line_weighted'
                current_obj['properties']['global_ID'] = global_id
                current_obj['properties']['zyklus_nr'] = k
                current_obj['properties']['weight'] = line.getWeight()
                current_obj['geometry']['type'] = 'LineString'
                current_obj['geometry']['coordinates'] = []
                current_obj['geometry']['coordinates'].append([p1.getX(), p1.getY()])
                current_obj['geometry']['coordinates'].append([p2.getX(), p2.getY()])
                global_id = global_id + 1


                json_daten['features'].append(current_obj)
                del current_obj, line, p1, p2


            activeDreicke = self.getAllActiveDreiecke(k)
            #loop over aktive dreiecke
            for m in range(0, len(activeDreicke)):
                dreieck = self.getDreieck_byID(activeDreicke[m])
                p1 = self.getPoint_byID(dreieck.getPointID1())
                p2 = self.getPoint_byID(dreieck.getPointID2())
                p3 = self.getPoint_byID(dreieck.getPointID3())

                current_obj = json.loads(feature_template)
                current_obj['type'] = 'Feature'
                current_obj['properties']['ID'] = activeDreicke[m]
                current_obj['properties']['type'] = 'Dreieck'
                current_obj['properties']['global_ID'] = global_id
                current_obj['properties']['zyklus_nr'] = k
                current_obj['geometry']['type'] = 'LineString'
                current_obj['geometry']['coordinates'] = []
                current_obj['geometry']['coordinates'].append([p1.getX(), p1.getY()])
                current_obj['geometry']['coordinates'].append([p2.getX(), p2.getY()])
                current_obj['geometry']['coordinates'].append([p3.getX(), p3.getY()])
                current_obj['geometry']['coordinates'].append([p1.getX(), p1.getY()])
                global_id = global_id + 1


                json_daten['features'].append(current_obj)
                del current_obj, dreieck, p1, p2, p3

            activeLine_move = self.getAllActiveBewegungsvektoren(k)
            #loop over aktive line_move = Bewegunsvektoren
            for m in range(0, len(activeLine_move)):
                line = self.getLine_move_byID(activeLine_move[m])
                p1 = self.getPoint_byID(line.getPointID1())
                p2 = self.getPoint_byID(line.getPointID2())

                current_obj = json.loads(feature_template)
                current_obj['type'] = 'Feature'
                current_obj['properties']['ID'] = activeLine_move[m]
                current_obj['properties']['type'] = 'Line_move'
                current_obj['properties']['global_ID'] = global_id
                current_obj['properties']['zyklus_nr'] = k

                current_obj['geometry']['type'] = 'LineString'
                current_obj['geometry']['coordinates'] = []
                current_obj['geometry']['coordinates'].append([p1.getX(), p1.getY()])
                current_obj['geometry']['coordinates'].append([p2.getX(), p2.getY()])
                global_id = global_id + 1


                json_daten['features'].append(current_obj)
                del current_obj, line, p1, p2


            del activePoints, activeLine_weighted, activeDreicke, activeLine_move


        #GeoJSON speichern
        with open(filename, 'w') as outfile:
            json.dump(json_daten, outfile)

        message = 'GeoJSON exportiert - Filename: ' + filename
        status = 'yes'
        value = 0
        retour = returnObject(message, status, value)
        return retour
    def toTXT_events_cycles(self, filename):
        #hier werden geometrie-lose Angaben zu den Cyclen (inkls. deren t) und den Events (inkl. dem Typ) als sortierte TXT Datei ausgegeben...



        return retour


class Cycle_Object:
    def __init__(self):
        #alle aktuellen Punkte (nur IDs) der gerade im Schrumpfungsprozess befindlichen Geometrie
        #diese Punkte werden jeweils nach Innen weiterbewegt (durch Bewegungsvektoren)
        #muss beim Befuellen gegen den UZS / counter clockwise sortiert werden!
        self.__activePoints = []

        #alle aktuellen Kanten (nur die IDs) der gerade im Schrumpfungsprozess befindlichen Geometrie
        self.__activeKanten = []

        #alle aktuellen Bewegungsvektoren
        self.__activeBewegungsvektoren = []

        #alle aktuellen Dreiecke der Triangulation
        self.__activeDreiecke = []

        #die Zeit, die in diesem Cycle von Event bis Event verstrichen ist... Laufzeit t ...
        #RUNDUNG und DATENTYP ist hier sehr wichtig!!!

        self.__laufzeit = 0.0


    def addActivePointID(self, id):
        #nur aufnehmen, wenn noch nicht dort existiert, keine Duplikate!
        if self.__activePoints.count(id) == 0:
            self.__activePoints.append(id)
        return
    def addActiveLine_weightedID(self, id):
        self.__activeKanten.append(id)
        return
    def addActiveDreieckID(self, id):
        self.__activeDreiecke.append(id)
        return
    def addActiveBewegungsvektor(self, id):
        self.__activeBewegungsvektoren.append(id)
        return


    def getAllActivePointID(self):
        #wichtig: !!!  Listen immer nur als Copy herausgeben, nicht original. !!!
        #ansonsten wird jede Aenderung sofort auch im gekapselten Objekt vorgenommen, also man vergibt ungewollt Schreibrechte!
        return copy.deepcopy(self.__activePoints)
    def getAllActiveLine_weighted(self):
        return copy.deepcopy(self.__activeKanten)
    def getAllActiveDreiecke(self):
        return copy.deepcopy(self.__activeDreiecke)
    def getAllActiveBewegungsvektoren(self):
        return copy.deepcopy(self.__activeBewegungsvektoren)

    #die verstrichene Zeit bzw. Laufzeit eines Zyklusses ist die Zeit zwischen dem Event davor und danach... solange war dieser Zyklus aktiv!

    def setVerstricheneZeit(self, time):
        self.__laufzeit = time
        return
    def getVerstricheneZeit(self):

        return self.__laufzeit

    def removeActivePointID_byID(self, id):
        self.__activePoints.remove(id)
        return
    def removeActiveLine_weightedID_byID(self, id):
        self.__activeKanten.remove(id)
        return
    def removeActiveLine_moveID_byID(self, id):
        self.__activeBewegungsvektoren.remove(id)
        return
    def removeActiveDreieckID_byID(self, id):
        self.__activeDreiecke.remove(id)
        return

class returnObject:
    def __init__(self, message, status, value=-1, valueList=[]):
        #gibt Rueckmeldung, wenn ein Point2D hinzugefuegt werden soll
        #message kann print() werden
        #status sagt, ob erfolgreich oder nicht. zum auswerten in if- gedacht
        #value ist default auf -1... ansonsten gibt er den punkt an, der schon existiert mit gleichen Koordinaten (die ID)

        self.message = message
        self.status = status
        self.value = value
        self.valueList = valueList
##class GeometryCollection:
##    #Container Objekt fuer beliebige Geometrien, egal ob Point2D, Line, Polygon...
##    def __init__(self):
##        self.__arrListe = []
##        return
##    def addGeometry(self, geometry):
##        self.__arrListe.append(geometry)
##        return
##    def getGeometryCollection(self):
##        return self.__arrListe

class Event:
    def __init__(self, zyklusnr, dreieckID):
        self.__id = -1
        self.__status = 'init'
        self.__timeOfOccurance = -2.0
        self.__zyklusnr = zyklusnr
        #welches Dreieck ist zusammengeklappt?
        self.__dreieckID = dreieckID
        #array of 1-2 Point IDs... die am Event beteiligt waren...!
        self.__pointsID = []

        #Typ kann sein: 'FLIP' ; 'EDGE'; 'SPLIT' ; 'SPEED_CHANGE'
        self.__type = ''

        return
    def setStatusFinished(self):
        self.__status = 'finished'

    def determine_Eventtyp(self):
        #bestimme die Umstaende des Events
        # welcher Typ?
        #welcher Punkt/e ist beteiligt?
        #setze entsprechend den Typ und die PunkteIDs

        return retour

    def setID(self, id):
        self.__id = id
        return
    def getID(self):
        return self.__id
    def getStatus(self):
        return self.__status
    def getTimeOfOccurance(self):
        return self.__timeOfOccurance
    def getZyklusNr(self):
        return self.__zyklusnr
    def getDreieckID(self):
        return self.__dreieckID
    def getPointIDList(self):
        return self.__pointsID
    def getType(self):
        return self.__type


class EventList:
    def __init__(self):
        self.__events = []
    def addEvent(self, event):
        self.__events.append(event)
        id = len(self.__events)-1
        self.__events[id].setID(id)

        retour = returnObject('Event hinzugefuegt: ID = ' + str(id), 'yes', id)
        return retour

    def updateEvent(self):

        return

    def getEvent_byID(self, id):
        return self.__events[id]
    def getAllEvents(self):
        return copy.deepcopy(self.__events)

    def getNumberUnfinishedEvents(self):
        return

    def getOldestUnfinishedEvent(self):
        #wenn das Event mit der kleinsten Zeit herausgegeben wird, dann setze den Status auf "in Bearbeitung" oder so aehnlich


        return



# +++++++++++++++ FUNKTIONEN ++++++++++++++++++++++

def straight_skeleton_weighted(inputFile):


    #++++++++++++++++++++INPUT++++++++++++++++++++
    if inputFile:
        with open(inputFile, 'r') as f:
            json_daten = json.load(f)
#    anzahl_polygon = json_daten['number_polygons']

    print('----------------------------------------')

    print('Datei lesen')
    print('CRS = ' + str(json_daten['crs']['properties']['name']))


    #+++++++++++++++++++Ausgabe Datei vorbereiten+++++++




    #++++++++++++++++++++VERARBEITUNG++++++++++++++++++++
    #ermittle die eindeutigen IDs von jedem Gebauede (DISTINCT)
    print('ermittle alle eindeutigen Gebaeude-IDs aus INPUT-Datei')
    liste_ID = []
    for i in range(0, len(json_daten['features'])):
        print('i = ' + str(i) + ' und Gebaeude-ID = ' + str(json_daten['features'][i]['properties']['id']))
        liste_ID.append(json_daten['features'][i]['properties']['id'])
    #nur unique valus
    liste_ID_distinct = set(liste_ID)

    print('Liste mit unique IDs:')
    print(liste_ID_distinct)
    #pro Gebaeude
    for id, value in enumerate(liste_ID_distinct):
        print('****************************************')
        print('----------------------------------------')
        print('Start neues Gebaeude - Nr. : ' + str(id) + ' - Gebauede-ID: ' + str(value))
        #erstelle Objekte und Datenstrukturen
        #erzeuge das Rahmen-Objekt fuer den kompletten Schrumpfungs-Prozess
        frame = Skeleton_Object()

        #erzeuge das akteulle Zyklus-Objekt fuer die erste Runde im Schrumpfungs-Prozess
        frame.add_CycleObject(Cycle_Object())


        #zb getrennt in Punkte, linien, Polygone... jeweils mit IDs

        #Punkte importieren
        for k in range(0, len(json_daten['features'])):
            #alle Linien iterieren, wenn ID gleich der aktuellen Gebaeude ID ist, dann die Punkte iterieren und importieren
            if json_daten['features'][k]['properties']['id'] == value:
                for m in range(0, len(json_daten['features'][k]['geometry']['coordinates'])):
                    #fuege Punkt hinzu
                    result = frame.addPoint2D(Point2D(json_daten['features'][k]['geometry']['coordinates'][m][0], json_daten['features'][k]['geometry']['coordinates'][m][1]))
                    print(result.message)
                    del result

        #Linien importieren
        for k in range(0, len(json_daten['features'])):
            #alle Linien iterieren, wenn ID gleich der aktuellen Gebaeude ID ist, dann die Linien einfuegen
            #ueber Koordinaten der Punkt die ID ermitteln:

            if json_daten['features'][k]['properties']['id'] == value:
                #es wird nun nicht getestet, ob es die Linie so schon gibt...
                weight = json_daten['features'][k]['properties']['weight']
                p1_id = frame.getPointID_byCoordinates(json_daten['features'][k]['geometry']['coordinates'][0][0], json_daten['features'][k]['geometry']['coordinates'][0][1])
                p2_id = frame.getPointID_byCoordinates(json_daten['features'][k]['geometry']['coordinates'][1][0], json_daten['features'][k]['geometry']['coordinates'][1][1])

                #es ist der nullte Zyklus, also 0
                currentLine = Line_weighted(p1_id, p2_id, weight, 0)
                result = frame.add_Line_weighted(currentLine)
                print(result.message)
                del weight, p1_id, p2_id, currentLine, result

        #erster Zyklus/ Cycle_Object mit allen aktiven IDs von Punkten, Linien befuellen
        for i in range(0, frame.getNumberOfPoints()):
            frame.addActivePointID(i, 0)
        for i in range(0, frame.getNumberOfLine_weighted()):
            frame.addActiveLine_weightedID(i, 0)

        #Triangulation des ersten Zyklus!
        frame.triangulate()


        #EventList() wurde bereits im frame beim Initialisieren hinzugefuegt


        #berechne Bewegung pro Punkt (nimm die IDs aus der aktuellen_Punkte-Liste)
        #diese Bewegungsvektoren bleiben bestehen und werden immmer wieder weitergegeben
        #ausser bei Edge und Split Event werden sie neu berechnet fuer diesen Punkt
        result = frame.getAllActivePointID(0)
        frame.calculate_Bewegungsvektor_byActivePointID(result)
        del result



        #SCHRUMPFUNGS-PROZESS - ein Zyklus geht von Event bis Event
        #die Schleife terminiert, wenn der Flaecheninhalt aller aktiven Dreiecke null ist, also die gesamte originale Geometrie bearbeitet wurde
        durchlauf = 0
        while (frame.getTotalAreaOfActiveTriangles() > 0.05) and (durchlauf < 500):
            #berechne die collapse times von allen aktiven Dreiecken, also zu welcher Zeit t sie zusammenklappen werden
            frame.calculateCollapsTime_ofActiveTriangles()

            #bearbeite das Dreieck mit der kleinsten Collaps Time als Event
            frame.handle_Event()

            #SICHERUNG beschraenkt auf 500 Durchlauefe
            durchlauf = durchlauf + 1



        #Ausgabe an Ausgabe-Datei anhaengen?


        #evt. eine extra Skeleton-Datei exportieren. Mit Allen line_move, mit den Line_weighted des letzten Zyklus und den NODES
        #--->


        #evt pro Gebaeude eine Datei GeoJSON
        result = frame.toGeoJSON(r'output/' + strftime("%Y_%m_%d-%H_%M_%S", gmtime()) + '_export_' + str(value).replace('/', '') + r'.geojson')
        print(result.message)
        #inklusive Dreiecke als Linien

        #Ausgabe als TXT fuer alle Zyklen und Events

        #----> TO DO!

        del frame




    #++++++++++++++++++++OUTPUT++++++++++++++++++++




    #++++++++++++++++++++DELETE Objects++++++++++++++++++++








    return
def berechneStrecke_zweiPunkte(punkt1, punkt2):

    return math.sqrt((punkt1.x-punkt2.x)**2+(punkt1.y-punkt2.y)**2)


def GeoJSON_Polygon2LineSegment(inputFile, outputFile):
    #Polygone lesen

    if inputFile:
        with open(inputFile, 'r') as f:
            json_daten = json.load(f)

    if inputFile:
        with open(inputFile, 'r') as f:
            output_json_data = json.load(f)
    anzahl_polygon = len(json_daten['features'])
#    print(json_daten['features'])
    print(anzahl_polygon)

    #die output JSON data entspricht zunaechst dem Input JSON data
    #alle Features dort loeschen, damit die LineSegmente angehaengt werden koennen

    output_json_data['features'] = []
##    output_json_data['features'] = ['test1', 'test2']
##    output_json_data['features'].append('test3')
    print(output_json_data)

    global_line_ID = 0

    for i in range(0,anzahl_polygon):
        #pro Gebaeude

        anzahl_vertices = len(json_daten['features'][i]['geometry']['coordinates'][0])
        print(anzahl_vertices)

        for j in range(0,anzahl_vertices-1):

            #Line Segmente bilden
            #j und j+1 Element

            #copy ist hier wichtig damit keine Referenz entsteht

            current_obj = copy.deepcopy(json_daten['features'][i])

            current_obj['geometry']['coordinates'] = []
            current_obj['geometry']['type'] = 'LineString'
            current_obj['geometry']['coordinates'].append([json_daten['features'][i]['geometry']['coordinates'][0][j][0], json_daten['features'][i]['geometry']['coordinates'][0][j][1]])
            current_obj['geometry']['coordinates'].append([json_daten['features'][i]['geometry']['coordinates'][0][j+1][0], json_daten['features'][i]['geometry']['coordinates'][0][j+1][1]])
            current_obj['properties']['weight'] = 1
            current_obj['properties']['global_line_ID'] = global_line_ID
#            print(current_obj)

#            print(json_daten['features'][j])

            output_json_data['features'].append(current_obj)
            del current_obj
            global_line_ID = global_line_ID + 1
        del anzahl_vertices

    #anzahl Polygone als Attribut der GeoJSON explizit mitgeben
    output_json_data['number_polygons'] = anzahl_polygon

    print(output_json_data)
    with open(outputFile, 'w') as outfile:
        json.dump(output_json_data, outfile)

#GeoJSON_Polygon2LineSegment(r'F:\AC430-BACKUP\Semester-Master3\G384_3D-Stadtmodelle\06_Projekt_StraightSkeleton\03_Testdaten\konvexe_testgeometrien_theo.geojson', r'F:\AC430-BACKUP\Semester-Master3\G384_3D-Stadtmodelle\06_Projekt_StraightSkeleton\03_Testdaten\konvexe_testgeometrien_theo_lines.geojson')
straight_skeleton_weighted(r'F:\AC430-BACKUP\Semester-Master3\G384_3D-Stadtmodelle\06_Projekt_StraightSkeleton\03_Testdaten\OSM_building_yes_beispiel_25833_lines_onlyOne.geojson')
#straight_skeleton_weighted(r'F:\AC430-BACKUP\Semester-Master3\G384_3D-Stadtmodelle\06_Projekt_StraightSkeleton\03_Testdaten\testgeometrien_lines.geojson')


