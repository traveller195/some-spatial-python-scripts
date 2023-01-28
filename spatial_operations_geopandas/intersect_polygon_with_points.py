# problem: from the view of polygons to POIs, it is no 1:1 relation. One polygon could intersect also no, one or a lot of POIs, as well!
# thus, a rule to handle this is required

# goal is also, to store the following values of the intersected POIs/ points for each polygon:
# number of POIs / count
# sum of the POIs in reference to a specific attribute
# average/ mean of the POIs in reference to a specific attribute

# new empty columns (use here np.nan instead of None)
data_polygon['pois_sum'] = np.nan
data_polygon['pois_avg'] = np.nan
data_polygon['pois_count'] = np.nan

for index, row in data_polygon.iterrows():
    current_polygon = data_polygon.loc[index, 'geometry']
    tmp_current_polygon = {'id':[0], 'geometry': [current_polygon]}
    gdf_current_polygon = gpd.GeoDataFrame(tmp_current_polygon, crs="EPSG:4326")
    
    # determine all intersected POIs 

    pois = gpd.sjoin(data_pois[['geometry', 'specific_attribute']], gdf_current_polygon, predicate='intersects')
    
    # print in same line to inform about progress 
    print('index = ' + str(index) + ' - count of POIs = ' + str(len(pois)), end='\r')
    
    # set new values
    if len(pois) > 0:
        data_polygon.at[index, 'pois_sum'] = pois['specific_attribute'].sum() # important: here only one [], no series for .sum()
        data_polygon.at[index, 'pois_avg'] = pois['specific_attribute'].mean() # important: here only one [], no series for .mean()
        data_polygon.at[index, 'pois_count'] = pois['specific_attribute'].count() # important: here only one [], no series for .count()        
    # remove all current objects within iteration
    del pois, current_polygon, tmp_current_hexagon, gdf_current_polygon
# print result
data_polygon.head()
