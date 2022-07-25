# piec chart having label function to genearte a better look

%matplotlib inline
def mm2inch(mm):
    return mm / 25.4

def pie_label_function(pct):
    return ('%1.1f%%' % pct) if pct > 4 else ''

def my_level_list(data, values, threshold):
   list = []
   for i in range(len(data)):
       if values[i] > threshold : #2%
           list.append('LU Nr.'+str(data[i]))
       else:
           list.append('')
   return list

df_groupby0.plot(kind = 'pie', 
           y = 'this is a y label', 
           autopct=pie_label_function, 
           startangle=90, 
           shadow=False, 
           #labels=my_level_list(df_groupby0['lu_nr'], df_groupby0['Anteil_Fläche'], 3), 
           legend = False, 
           fontsize=10,
           title='this is the title',
           figsize=(8,8)
          )
