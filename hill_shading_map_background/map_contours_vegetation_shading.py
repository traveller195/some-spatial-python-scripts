#import sqlite3
#from sqlite3 import Error

#import gdal
#import ogr
#import overpy
#import shapely

import os
import sys
import math
import time
import arcpy

from arcpy.sa import *
#import csv

#import numpy
#import matplotlib

#import requests
#import json

def calculate_Beschnittzugabe(inputShapefile, outputShapefile):
    beschnittzugabe = 2

    R = 6371000000
    M = 120000
    piDurch180 = math.pi / 180
    rDurchM = R / M

    x_paper = 841 + 2*beschnittzugabe
    y_paper = 594 + 2*beschnittzugabe

    breite_minuten = 50

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(4326)

    #neue output Shapefile anlegen mit fields und CRS 4326
    head, tail = os.path.split(outputShapefile)
    arcpy.CreateFeatureclass_management(head, tail, "POLYGON", None, "DISABLED", "DISABLED", SpatialRef)
    arcpy.env.workspace = head
    arcpy.AddField_management(outputShapefile, "ID", "LONG")
    arcpy.AddField_management(outputShapefile, "nr_neu", "TEXT")

    #insertCursor
    cursorSchreiben = arcpy.da.InsertCursor(outputShapefile, ['ID', 'nr_neu', 'SHAPE@'])
    #zaehler fuer ID
    fid = 0
    #searchCursor
    with arcpy.da.SearchCursor(inputShapefile, ['typ', 'nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
            if row[0] != 1 and row[0] != 5:

                #nun vom Polygon die Punkte auslesen

                #neues Feature wird gelesen
                #neues leeres Array fuer Feature zum schreiben erstellen
                arrayFeature = arcpy.Array()
                arrayFeature.removeAll
                #set standard values of variables   for CRS EPSG 4327 - WGS84
                latMin = 80
                latMax = -80
                lonMin = 80
                lonMax = -80

                for part in row[3]:
            # neues leeres Array fuer den Part erstellen
                    arrayPart = arcpy.Array()
                    arrayPart.removeAll
            # durch jeden Vertex des Parts gehen
                    for pnt in part:
                        if pnt:
                    # Print x,y coordinates of current point
                    #******************************************************
                    #create bounding box / envelope of the polygon
                            if pnt.X < lonMin:
                                lonMin = pnt.X
                            if pnt.Y < latMin:
                                latMin = pnt.Y
                            if pnt.X > lonMax:
                                lonMax = pnt.X
                            if pnt.Y > latMax:
                                latMax = pnt.Y
                    #******************************************************
                    #calculate new points
                    #Kartenfeld in mm berechnen
                    kartenfeld_x = rDurchM * math.pi / 180 * breite_minuten / 60
                    kartenfeld_y = rDurchM * math.log(math.tan(45*piDurch180+latMax*0.5*piDurch180)) - rDurchM * math.log(math.tan(45*piDurch180+latMin*0.5*piDurch180))

                    ueberlappung_x = x_paper - kartenfeld_x
                    ueberlappung_y = y_paper - kartenfeld_y

                    neu_latMax = 2*(math.atan(math.exp((rDurchM*math.log(math.tan(45*piDurch180+0.5*latMax*piDurch180))+0.5*ueberlappung_y)/rDurchM))-45*piDurch180)*180/math.pi
                    neu_latMin = 2*(math.atan(math.exp((rDurchM*math.log(math.tan(45*piDurch180+0.5*latMin*piDurch180))-0.5*ueberlappung_y)/rDurchM))-45*piDurch180)*180/math.pi

                    shift_longitude = 0.5*ueberlappung_x / piDurch180 / rDurchM

#                    print row[1] + ' ' + str(lonMin) + ' ' + str(lonMax) + ' ' + str(latMin) + ' ' + str(latMax) + ' ' + str(kartenfeld_x) + ' ' + str(kartenfeld_y) + ' ' + str(ueberlappung_y)

                    punktNW = arcpy.Point(lonMin - shift_longitude, neu_latMax)
                    punktNO = arcpy.Point(lonMax + shift_longitude, neu_latMax)
                    punktSO = arcpy.Point(lonMax + shift_longitude, neu_latMin)
                    punktSW = arcpy.Point(lonMin - shift_longitude, neu_latMin)

                    #neues Polygon erzeugen

                    arrayPart.append(punktNW)
                    arrayPart.append(punktNO)
                    arrayPart.append(punktSO)
                    arrayPart.append(punktSW)
                    arrayPart.append(punktNW)

                    arrayFeature.append(arrayPart)

                    #neu berechnetes Feature mit alter Object ID hinzufuegen

                cursorSchreiben.insertRow([fid, row[1], arcpy.Polygon(arrayFeature, SpatialRef)])
                fid += 1
    del cursor
    del cursorSchreiben

def schreibeEinzelneKML (inputShapefile, outputFolder):
    #hier werden die einzelnen Blattschnitt-Polygone separat gespeichert und als KML File gespeichert.
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = outputFolder

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(4326)

    with arcpy.da.SearchCursor(inputShapefile, ['nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
            #write KML file with only one polygon
            arcpy.CreateFeatureclass_management(outputFolder, str(row[0]) + r".shp", "POLYGON", None, "DISABLED", "DISABLED", SpatialRef)
            arcpy.AddField_management(outputShapefile, "ID", "LONG")
            arcpy.AddField_management(outputShapefile, "nr_neu", "TEXT")

            #insertCursor
            cursorSchreiben = arcpy.da.InsertCursor(os.path.join(outputFolder, str(row[0]) + r".shp"), ['ID', 'nr_neu', 'SHAPE@'])
            cursorSchreiben.insertRow([row[1], row[0], row[2]])
            del cursorSchreiben

            arcpy.LayerToKML_conversion(outputFolder, str(row[0]) + r".shp", outputFolder, str(row[0]) + r".kml")

def cutASCII_Grid(inputShapefile, inputElevationgrid, inputSnapRaster, outputFolder):
    #cut all map polygons out of the generell united elevation grid. pixel position according to a generell snap raster
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = outputFolder

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(4326)

    arcpy.CheckOutExtension("Spatial")
    time.sleep(3)

    with arcpy.da.SearchCursor(inputShapefile, ['nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
            #extract by mask - to cut each polygon out of the universal elevation ASCII grid
            arcpy.env.snapRaster = inputSnapRaster

            outExtractByMask = arcpy.sa.ExtractByMask(inputElevationgrid, row[2])
            outExtractByMask.save(os.path.join(outputFolder, str(row[0]) + r"_WebMerc.tif"))
            del outExtractByMask
            arcpy.RasterToASCII_conversion(os.path.join(outputFolder, str(row[0]) + r"_WebMerc.tif"), os.path.join(outputFolder, str(row[0]) + r"_WebMerc.asc"))

            #WICHTIG: ich habe hier noch die PRJ Files fuer die ASCII Dateien vergessem!!!
            #also create new prj-files  - for ASCII grid
            content = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["central_meridian",0],PARAMETER["latitude_of_origin",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],UNIT["Meter",1],PARAMETER["standard_parallel_1",0.0]]'
            #lowercase current index of map
            lowerIndex = str(row[0]).lower()

            f = open(os.path.join(inputFolder, lowerIndex + r"_webmerc.prj"), "w")
            f.write(content)
            f.close

def generateContour_LinesAreas(inputShapefile, inputFolder, outputFolder):
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = outputFolder

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(4326)

    arcpy.CheckOutExtension("Spatial")
    time.sleep(3)

    #remapRange table/ array for elevtation areas
    remap = arcpy.sa.RemapRange([[-3000, 0, 99], [0, 250, 0], [250, 500, 1], [500, 750, 2], [750, 1000, 3], [1000, 1250, 4], [1250, 1500, 5], [1500, 1750, 6], [1750, 2000, 7], [2000, 2250, 8], [2250, 2500, 9], [2500, 2750, 10], [2750, 3000, 11], [3000, 3250, 12], [3250, 3500, 13], [3500, 6000, 14]])

    remapRed = arcpy.sa.RemapRange([[-3000, 0, 153], [0, 250, 254], [250, 500, 253], [500, 750, 253], [750, 1000, 253], [1000, 1250, 252], [1250, 1500, 252], [1500, 1750, 252], [1750, 2000, 252], [2000, 2250, 244], [2250, 2500, 237], [2500, 2750, 230], [2750, 3000, 220], [3000, 3250, 206], [3250, 3500, 192], [3500, 6000, 255]])
    remapGreen = arcpy.sa.RemapRange([[-3000, 0, 204], [0, 250, 240], [250, 500, 229], [500, 750, 219], [750, 1000, 209], [1000, 1250, 195], [1250, 1500, 177], [1500, 1750, 159], [1750, 2000, 141], [2000, 2250, 121], [2250, 2500, 102], [2500, 2750, 83], [2750, 3000, 63], [3000, 3250, 42], [3250, 3500, 21], [3500, 6000, 255]])
    remapBlue = arcpy.sa.RemapRange([[-3000, 0, 255], [0, 250, 217], [250, 500, 194], [500, 750, 171], [750, 1000, 140], [1000, 1250, 131], [1250, 1500, 117], [1500, 1750, 103], [1750, 2000, 89], [2000, 2250, 78], [2250, 2500, 67], [2500, 2750, 56], [2750, 3000, 43], [3000, 3250, 29], [3250, 3500, 14], [3500, 6000, 255]])

    with arcpy.da.SearchCursor(inputShapefile, ['nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
            #also create new prj-files  - for reclassify Raster Result
            content = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["central_meridian",0],PARAMETER["latitude_of_origin",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],UNIT["Meter",1],PARAMETER["standard_parallel_1",0.0]]'
            #lowercase current index of map
            lowerIndex = str(row[0]).lower()

            ge = open(os.path.join(outputFolder, str(row[0]) + r"_red.prj"), "w")
            ge.write(content)
            ge.close
            del ge

            fg = open(os.path.join(outputFolder, str(row[0]) + r"_green.prj"), "w")
            fg.write(content)
            fg.close
            del fg

            hk = open(os.path.join(outputFolder, str(row[0]) + r"_blue.prj"), "w")
            hk.write(content)
            hk.close
            del hk

            time.sleep(2)
            #generate contour lines
            arcpy.env.snapRaster = os.path.join(inputFolder, str(row[0]) + r"_WebMerc.asc")
            arcpy.sa.Contour(os.path.join(inputFolder, str(row[0]) + r"_WebMerc.asc"), os.path.join(outputFolder, str(row[0]).lower() + r"_contline.shp"), 250, 0)

            #generate contour areas as a raster - directly from ASCII grid to raster, no vectorization
            #from range like elevation in meters convert to numbers of elevation layer like 1 to 14
            #use rastercalculator and conditional cases
            #http://desktop.arcgis.com/de/arcmap/10.3/tools/spatial-analyst-toolbox/conditional-evaluation-with-con.htm
            #http://desktop.arcgis.com/de/arcmap/10.3/tools/spatial-analyst-toolbox/reclassify.htm
            #http://desktop.arcgis.com/de/arcmap/10.3/analyze/arcpy-spatial-analyst/an-overview-of-transformation-classes.htm
            outReclassRed = arcpy.sa.Reclassify(os.path.join(inputFolder, str(row[0]) + r"_WebMerc.asc"), "VALUE", remapRed)
            outReclassRed.save(os.path.join(outputFolder, str(row[0]) + r"_red.tif"))
            del outReclassRed

            outReclassGreen = arcpy.sa.Reclassify(os.path.join(inputFolder, str(row[0]) + r"_WebMerc.asc"), "VALUE", remapGreen)
            outReclassGreen.save(os.path.join(outputFolder, str(row[0]) + r"_green.tif"))
            del outReclassGreen

            outReclassBlue = arcpy.sa.Reclassify(os.path.join(inputFolder, str(row[0]) + r"_WebMerc.asc"), "VALUE", remapBlue)
            outReclassBlue.save(os.path.join(outputFolder, str(row[0]) + r"_blue.tif"))
            del outReclassBlue

            #postprocessing contor lines
            #add geometry attribut with length in meters
            arcpy.AddGeometryAttributes_management(os.path.join(outputFolder, str(row[0]).lower() + r'_contline.shp'), 'LENGTH_GEODESIC', 'METERS', '', '')

            #remove short lines
            arcpy.MakeFeatureLayer_management(os.path.join(outputFolder, str(row[0]).lower() + r'_contline.shp'), 'lyr')
            selection = arcpy.SelectLayerByAttribute_management('lyr', 'NEW_SELECTION', '"LENGTH_GEO" > 400')
            arcpy.CopyFeatures_management(selection, os.path.join(outputFolder, str(row[0]).lower() + r"_contline_length.shp"))
            arcpy.Delete_management('lyr')

            #generalize lines with PAEK algorithm
            arcpy.cartography.SmoothLine(os.path.join(outputFolder, str(row[0]) + r"_contline_length.shp"), os.path.join(outputFolder, str(row[0]) + r"_contline_FINAL.shp"), "PAEK", 60, "FIXED_CLOSED_ENDPOINT", "NO_CHECK")

            del selection
def Vegetation_Raster(inputShapefile, inputSnapRaster, inputVegetationShapefile, outputFolder):

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = outputFolder

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(3857)

    arcpy.CheckOutExtension("Spatial")
    arcpy.CheckOutExtension("ArcInfo")
    time.sleep(3)

    with arcpy.da.SearchCursor(inputShapefile, ['nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
#            arcpy.env.snapRaster = inputSnapRaster
            outputRaster = os.path.join(outputFolder, str(row[0]).lower() + r"_veg.tif")
            outputRaster8bit = os.path.join(outputFolder, str(row[0]).lower() + r"_veg_8bit.tif")

            #aktuelles Kartenblatt Polygon von 4326 nach 3857 transformieren
            polygon_WebMerc = row[2].projectAs(SpatialRef)
            arcpy.MakeFeatureLayer_management(polygon_WebMerc, "extent")

            #aktuelles Polygon als EXTENT verwenden!
            arcpy.env.extent = "extent"
            arcpy.env.cellsize = 10.16
            arcpy.env.outputCoordinateSystem = SpatialRef

            #nun zuerst ein Rasterbild aus lauter Nullen erzeugen
            extent_WebMerc = polygon_WebMerc.extent
#            print extent_WebMerc
#            print extent_WebMerc.XMax
            RasterNull = arcpy.sa.CreateConstantRaster(0, "INTEGER", 10.16, extent_WebMerc)

            RasterVeg = RasterNull

            #gesamt vector auf aktuelles Kartenblatt beschneiden/ clip
            arcpy.Clip_analysis(inputVegetationShapefile, polygon_WebMerc, os.path.join(outputFolder, str(row[0]).lower() + r"_clip.shp"))

            if int(arcpy.GetCount_management(os.path.join(outputFolder, str(row[0]).lower() + r"_clip.shp"))[0]) == 0:
                #wenn im aktuellen Kartenblatt keine Vegetation Features sind.
                pass
            else:
                #wenn mind ein Feature da ist
                #PolytonToRaster
                arcpy.PolygonToRaster_conversion(os.path.join(outputFolder, str(row[0]).lower() + r"_clip.shp"), "gridcode", outputRaster, "MAXIMUM_AREA", "", 10.16)
                RasterNodata = arcpy.sa.IsNull(outputRaster)
                RasterNodata2 = arcpy.sa.Con(RasterNodata == 1, 0, arcpy.Raster(outputRaster))

                RasterVeg = RasterNull + arcpy.sa.Con(RasterNodata2 == 1, 1, 0)
                del RasterNodata
                del RasterNodata2

            arcpy.Delete_management(os.path.join(outputFolder, str(row[0]).lower() + r"_clip.shp"))

            arcpy.CopyRaster_management(RasterVeg, outputRaster8bit,"","","","","","8_BIT_UNSIGNED")

            del outputRaster
            del outputRaster8bit
            del extent_WebMerc
            del polygon_WebMerc
            del RasterNull
            del RasterVeg

            arcpy.Delete_management("extent")

            content = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["central_meridian",0],PARAMETER["latitude_of_origin",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],UNIT["Meter",1],PARAMETER["standard_parallel_1",0.0]]'

            ge = open(os.path.join(outputFolder, str(row[0]).lower() + r"_veg_8bit.prj"), "w")
            ge.write(content)
            ge.close
            del ge


def unionAllRasterLayers(inputShapefile, inputShadingFolder, inputElevationAreaFolder, inputVegetationFolder, outputFolder):

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = outputFolder

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(3857)

    arcpy.CheckOutExtension("Spatial")
    time.sleep(3)

    with arcpy.da.SearchCursor(inputShapefile, ['nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
            RasterVegetation = os.path.join(inputVegetationFolder, str(row[0]).lower() + r"_veg_8bit.tif")
            RasterShading = os.path.join(inputShadingFolder, str(row[0]).lower() + r"_ShadedComb_8bit.tif")
            RasterRed = os.path.join(inputElevationAreaFolder, str(row[0]) + r"_red.tif")
            RasterGreen = os.path.join(inputElevationAreaFolder, str(row[0]) + r"_green.tif")
            RasterBlue = os.path.join(inputElevationAreaFolder, str(row[0]) + r"_blue.tif")

            outputPath = os.path.join(outputFolder, str(row[0]).lower() + r"_composite.tif")
            outputPath8bit = os.path.join(outputFolder, str(row[0]).lower() + r"_final_8bit.tif")

            #overtake the 300 dpi snap raster of vegetation raster = 10.16 meter cellsize
            arcpy.env.snapRaster = os.path.join(inputVegetationFolder, str(row[0]).lower() + r"_veg_8bit.tif")
            arcpy.env.extent = os.path.join(inputVegetationFolder, str(row[0]).lower() + r"_veg_8bit.tif")
            arcpy.env.cellsize = 10.16
            arcpy.env.outputCoordinateSystem = SpatialRef

            #was passiert im RasterCalculator bei unterschiedlichen Pixelgroessen?
            outputRed   = Int(Con(Raster(RasterVegetation) == 1, 0.3 * Raster(RasterShading) + 0.3 * Raster(RasterRed) + 0.4 * 52, 0.5 * Raster(RasterShading) + 0.5 * Raster(RasterRed)))
            outputGreen = Int(Con(Raster(RasterVegetation) == 1, 0.3 * Raster(RasterShading) + 0.3 * Raster(RasterGreen) + 0.4 * 161, 0.5 * Raster(RasterShading) + 0.5 * Raster(RasterGreen)))
            outputBlue  = Int(Con(Raster(RasterVegetation) == 1, 0.3 * Raster(RasterShading) + 0.3 * Raster(RasterBlue) + 0.4 * 44, 0.5 * Raster(RasterShading) + 0.5 * Raster(RasterBlue)))

            arcpy.CompositeBands_management([outputRed, outputGreen, outputBlue], outputPath)

            arcpy.CopyRaster_management(outputPath, outputPath8bit,"","","","","","8_BIT_UNSIGNED")

            del RasterVegetation, RasterShading
            del RasterRed, RasterGreen, RasterBlue
            del outputPath, outputPath8bit
            del outputRed, outputGreen, outputBlue

            content = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["central_meridian",0],PARAMETER["latitude_of_origin",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],UNIT["Meter",1],PARAMETER["standard_parallel_1",0.0]]'

            ge = open(os.path.join(outputFolder, str(row[0]).lower() + r"_final_8bit.prj"), "w")
            ge.write(content)
            ge.close
            del ge

def hillshading_combination(inputShapefile, inputFolder, outputFolder):
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = outputFolder

    #spatial reference system
    SpatialRef = arcpy.SpatialReference(4326)

    arcpy.CheckOutExtension("Spatial")
    time.sleep(3)

    with arcpy.da.SearchCursor(inputShapefile, ['nr_neu', 'OID@', 'SHAPE@']) as cursor:
        for row in cursor:
            arcpy.env.snapRaster = os.path.join(inputFolder, str(row[0]).lower() + r"_webmerc.asc")
            inputASCIIGrid = os.path.join(inputFolder, str(row[0]).lower() + r"_webmerc.asc")

            slopeRaster = arcpy.sa.Slope(inputASCIIGrid, 'DEGREE')
            shadingRaster = arcpy.sa.Hillshade(inputASCIIGrid, 315, 45)

            #Multiplikator/ Faktor-Raster aus SLOPE ableiten
#            FaktorRaster = arcpy.sa.Con(slopeRaster, 1.0, arcpy.sa.Con(slopeRaster, 2.0, 1.05, slopeRaster < 4), )
#            FaktorRaster = arcpy.sa.Con(slopeRaster > 7.0, 1.0, arcpy.sa.Con(slopeRaster < 4.0, 2.0, 1.05))


#            ZwischenRaster = arcpy.sa.Con(shadingRaster * FaktorRaster > 255.0, 255.0, shadingRaster * FaktorRaster)

            RasterEins = arcpy.sa.Float(0.5 * shadingRaster + 0.5 * (255.0 - slopeRaster * (255.0 / 90.0)))

#            RasterOut = arcpy.sa.Int(arcpy.sa.Con(RasterEins > 255.0, 255.0, RasterEins))
            RasterZwei = arcpy.sa.Int(RasterEins * 1.15)
            RasterOut = arcpy.sa.Con(RasterZwei > 255, 255, RasterZwei)

#            FaktorRaster.save(os.path.join(outputFolder, str(row[0]).lower() + r"_FaktorRaster.tif"))
#            RasterEins.save(os.path.join(outputFolder, str(row[0]).lower() + r"_R1.tif"))

            RasterOut.save(os.path.join(outputFolder, str(row[0]).lower() + r"_ShadedComb.tif"))
            arcpy.CopyRaster_management(RasterOut, os.path.join(outputFolder, str(row[0]).lower() + r"_ShadedComb_8bit.tif"),"","","","","","8_BIT_UNSIGNED")

            del slopeRaster
            del shadingRaster
            del inputASCIIGrid

            del RasterEins
            del RasterZwei
            del RasterOut
#            del FaktorRaster
#            del ZwischenRaster

            content = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["central_meridian",0],PARAMETER["latitude_of_origin",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],UNIT["Meter",1],PARAMETER["standard_parallel_1",0.0]]'

            ge = open(os.path.join(outputFolder, str(row[0]).lower() + r"_ShadedComb.prj"), "w")
            ge.write(content)
            ge.close
            del ge
#berechne ein SLOPE Bild mit Einheit Degree vom Input

#calculate_Beschnittzugabe(r'E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30Min_versetzt_zentriert.shp', r'E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30_zugabe5.shp')

#schreibeEinzelneKML(r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30_zugabe5.shp", r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_einzeln")


#cutASCII_Grid(r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30_zugabe5.shp", "E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\INPUT\SRTM\srtm1_all_3857.asc", r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\INPUT\srtm1_all_3857.asc", r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\INPUT\pro_kartenblatt")
#cutASCII_Grid(r'E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30_zugabe5.shp', r'D:\srtm.asc', r'D:\srtm.asc', r'D:\sss')
#generateContour_LinesAreas(r'D:\script\Blattschnitt_50x30_zugabe5.shp', r'D:\sss', r'D:\sst')
#generateContour_LinesAreas(r'D:\script\Blattschnitt_50x30_zugabe5.shp', r'E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\INPUT\SRTM\pro_kartenblatt\ASCII', r'D:\ssw')
#hillshading_combination(r'D:\script\Blattschnitt_50x30_zugabe5.shp', r'E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\INPUT\SRTM\pro_kartenblatt\ASCII', r'D:\shading')
#Vegetation_Raster(r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30_zugabe5.shp", "E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\INPUT\SRTM\srtm1_all_3857.asc", r"E:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Veg\Ergebnis\Veg_gridcode_1_dissolve_editTheo.shp", r"D:\veg4")
#unionAllRasterLayers(r"D:\s79630\Blattschnitt_50x30_zugabe5.shp", r"D:\s79630\Zwischenergebnisse\shading", r"D:\s79630\Zwischenergebnisse", r"D:\s79630\Zwischenergebnisse\vegetation", r"D:\s79630\Ergebnis")
unionAllRasterLayers(r"F:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Blattschnitt\Blattschnitt_50x30_zugabe5.shp", r"F:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Zwischenergebnisse\shading", r"F:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Zwischenergebnisse", r"F:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\Zwischenergebnisse\vegetation", r"F:\AC430-BACKUP\Semester-Master2\Marokko_Jaeschke\allgemeiner_Arbeitsablauf\OUTPUT")

