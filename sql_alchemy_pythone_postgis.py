
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString

#Spatial Join
from geopandas.tools import sjoin

import psycopg2
from sqlalchemy import create_engine

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ database connection +++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



db_connection_url = "postgresql+psycopg2://postgres:postgres@goat_db_01:5432/postgres"

con = create_engine(db_connection_url)  

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ select into GeoDataFrame ++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

sql = "SELECT * FROM schemaname.tablename LIMIT 10;"

df_test = gpd.read_postgis(sql, con,geom_col='geometry')  
print (df_test.head())
df_test.info()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++ further CRUD operations  ++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

con.execute("CREATE TABLE schemaname.new_tablename AS SELECT * FROM schemaname.tablename LIMIT 10;")

