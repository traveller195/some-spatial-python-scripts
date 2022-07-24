

# for figsize
def mm2inch(mm):
    return mm / 25.4

#convert color format
def rgba2mpl(r,g,b,a=1.0):
    # build from 255,0,255,1 new form 1,0,1,1
    output = (0.0, 0.0, 0.0, 1.0)

    output = (r/255, g/255, b/255, a)

    return output

def rgb2hex(r,g,b):
    # build from 255,0,255,1 new hex color code

    return "#{:02x}{:02x}{:02x}".format(r,g,b)


# fill in points into numbers es a separator every 3 characters
def intWithCommas(x):
    # aus einer Zahl werden die Tausender-Trennzeichen eingefuegt!

#    if type(x) not in [type(0), type(0L)]:
#        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ".%03d%s" % (r, result)
    return "%d%s" % (x, result)

def intWithCommas_abbr(x):
    # aus einer Zahl werden die Tausender-Trennzeichen eingefuegt!
    # bei zu grossen Zahlen wird gerundet und mit K und M gearbeitet
    # somit kann Platz gespart werden

    if x < 0:
        return '-' + intWithCommas_abbr(-x)

    
    if x >= 0 and x < 1000: # bei 0 bis 999 gebe genau dies wieder zurueck
        return x

    if x >= 1000 and x < 100000: # runde auf eine Dezimalstelle und verwende 'K'
        a = x / 1000
        return str(round(a, 1)).replace('.', ',') + 'K'

    if x >= 100000 and x < 1000000: # runde auf null  Dezimalstellen und verwende 'K'
        a = x / 1000
        return str(round(a)).replace('.', ',') + 'K'

    if x >= 1000000:
        a = x / 1000000
        return str(round(a, 2)).replace('.', ',') + 'M'
      
      
