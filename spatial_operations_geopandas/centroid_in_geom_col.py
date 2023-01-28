# determine centroid of poylgon geometry and replace geometry column
%matplotlib inline
import os
import math
import numpy as np
import pandas as pd
import geopandas as gpd

from shapely import geometry

# generate centroid
def returnPointGeometryFromXY(polygon_geometry):
        ## Calculate x and y of the centroid
        centroid_x,centroid_y = polygon_geometry.centroid.x,polygon_geometry.centroid.y
        ## Create a shapely Point geometry of the x and y coords
        point_geometry = geometry.Point(centroid_x,centroid_y)
        return point_geometry
      
      



# replace polygon geometry by centroid point
data_spatial["geometry"] = data_spatial['geometry'].apply(returnPointGeometryFromXY)

# show result 
# now, it should contrinas POINT() instead of POLYGON()
data_spatial.head()
