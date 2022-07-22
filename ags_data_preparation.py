# use lambda function 
def add_suffix_zeros(text):
    if len(text) == 2:
        text = text + '000000'
    if len(text) == 5:
        text = text + '000'
    if len(text) == 8:
        pass
    return text
  
  
  
  # complete AGS in column
  data_destatis['AGS'] = data_destatis['AGS'].apply(add_suffix_zeros)
  
  
