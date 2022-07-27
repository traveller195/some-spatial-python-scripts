

# first, load input data into DataFrames/ GeoDataFrames

# create Array to store every new line (after data manipulation)

arr_output_table = []


# append new line to array (not to DataFrame, which is not longer supported)

for i, row in data_input.iterrows():
    
    #current IDs
    current_ID = len(arr_output_table)



    # insert new row to table 'geometries'
    new_row = {'geometry_id': current_ID, 'source_id': data_input.loc[i,'gml_id'], 'geometry_geom':data_input.loc[i,'geometry']}

    arr_output_table.append(new_row)
    del new_row
    

# bring complete array into output DataFrame / GeoDataFrame
out_geometries = gpd.GeoDataFrame(arr_output_table, columns=['geometry_id', 'source_id', 'geometry_geom'], geometry='geometry_geom')


# do some more important stuff:

out_geometries = out_geometries.set_crs(3857, allow_override=True)

# set data types of columns
print(str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + '  set data types for columns')

convert_dict = {'geometry_id': int,
                'source_id': str
                } 
out_geometries = out_geometries.astype(convert_dict)
del convert_dict

# now, It can saves for example as GeoJSON or Shapefile...
