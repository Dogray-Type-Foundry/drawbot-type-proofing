from fontPens.marginPen import MarginPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.agl import UV2AGL
import unicodedata
from numpy import linspace
from statistics import mean, fmean, geometric_mean, harmonic_mean, median, median_grouped
from math import ceil
from drawBotGrid import Grid

myFont = "fonts/WorkSans-Regular.ttf"

f = TTFont(myFont)
glist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

useMean = False

fsize = 1000
frmdur = 0.5
zonevalue = 75
expandedsize = 20
high = (255/255,102/255,102/255)
neutral = (115/255,220/255,150/255)
low = (255/255,204/255,102/255)

capTimes = 9
xHghtTimes = 7
descTimes = 3
ascTimes = 3
extraTimes = 3

capHeight = f['OS/2'].sCapHeight
xHeight = f['OS/2'].sxHeight

overshootbounds = BoundsPen(f.getGlyphSet()['o'])
fovrsht = f.getGlyphSet()['o'].draw(overshootbounds)
overshoot = overshootbounds.bounds[1]

ascbounds = BoundsPen(f.getGlyphSet()['f'])
fasc = f.getGlyphSet()['f'].draw(ascbounds)
ascender = ascbounds.bounds[3] + overshoot

descbounds = BoundsPen(f.getGlyphSet()['y'])
fdesc = f.getGlyphSet()['y'].draw(descbounds)
descender = descbounds.bounds[1] - overshoot

alignments = [descender, 0, xHeight, capHeight, ascender]

def makeRange(start, end, subdivisions):
    full_range = []
    value = (float(end - start)) / float(subdivisions-1)
    make_range = linspace(float(start), float(end), num=subdivisions)
    for r in make_range:
        if r == start:
            pass
        else:
            full_range.append(r)
    full_range.sort()
    return full_range, value


def expandRange(value, amount, times):
    expanded_range = []
    final_value = value
    for i in range(times):
        final_value += amount
        expanded_range.append(final_value)
    expanded_range.sort()
    return expanded_range


ucHeights = [
    *expandRange(descender,makeRange(0, descender, descTimes)[1],extraTimes),
    *makeRange(0, descender, descTimes)[0],
    0,
    *makeRange(0, capHeight, capTimes)[0],
    *expandRange(capHeight, makeRange(0, capHeight, capTimes)[1], extraTimes)
]
lcHeights = [
    *expandRange(descender, makeRange(0, descender, descTimes)[1], extraTimes),
    *makeRange(0, descender, descTimes)[0],
    0,
    *makeRange(0, xHeight, xHghtTimes)[0],
    *makeRange(xHeight, ascender, ascTimes)[0],
    *expandRange(ascender, makeRange(xHeight, ascender, ascTimes)[1], extraTimes)
]
otherHeights = [
    *expandRange(descender, makeRange(0, descender, descTimes)[1], extraTimes),
    *makeRange(0, descender, descTimes)[0],
    0,
    *makeRange(0, xHeight, xHghtTimes)[0],
    *makeRange(xHeight, ascender, ascTimes)[0],
    *expandRange(ascender, makeRange(xHeight, ascender, ascTimes)[1], extraTimes)
]


def getBez(g):
    B = BezierPath()
    B.text(g, font=myFont, fontSize=fsize)
    return B


def midDist(g):
    vertBounds = BoundsPen(f.getGlyphSet()[g])
    vB = f.getGlyphSet()[g].draw(vertBounds)
    topBound = vertBounds.bounds[3]
    bottomBound = vertBounds.bounds[1]
    halfway = (topBound - bottomBound)/2
    
    B = getBez(g)
    pen = MarginPen(dict(), halfway, isHorizontal=True)
    B.drawToPen(pen)
    
    cmargs = pen.getContourMargins()
    margs = pen.getMargins()
        
    middistval = int(margs[0])
    return middistval


def drawGlyph(g):
    stroke(None)
    fill(0.77,0.77,0.75,0.75)
    B = BezierPath()
    B.text(g, font=myFont, fontSize=fsize)
    drawPath(B)
    stroke(0)
    fill(None)


def drawContour(g, gB):
    B = gB
    ldistsmean = []
    rdistsmean = []
    
    fg = UV2AGL[ord(g)]
    
    ldistvals = {}
    rdistvals = {}
    
    glf = f.getGlyphSet()[fg]
    quarterwidth = int(glf.width/4)
    
    if unicodedata.category(g) == 'Lu':
        heights = ucHeights
    elif unicodedata.category(g) == 'Ll':
        heights = lcHeights
    elif unicodedata.category(g) == 'Nd':
        heights = ucHeights
    else:
        heights = lcHeights

    for y in heights:
        if y in alignments:
            stroke(0.9, 0, 0, 0.4)
            strokeWidth(4)
        else:
            stroke(0,0,0,0.1)
            strokeWidth(2)
        line((-800, y), (width()+300, y))

        pen = MarginPen(dict(), y, isHorizontal=True)
        B.drawToPen(pen)
        stroke(0)
    
        cmargs = pen.getContourMargins()
        margs = pen.getMargins()
        
        if not margs:
            ldistvals[y] = None
            rdistvals[y] = None
        elif margs:
            lmarg = margs[0]
            rmarg = margs[1]
            strokeWidth(6)
            stroke(179/255, 102/255, 255/255,0.5)
            line((0,y), (margs[0], y))
            line((rmarg,y), (glf.width, y))

            ldist = lmarg
            rdist = glf.width - rmarg
        
            ldistvals[y] = int(ldist)
            rdistvals[y] = int(rdist)        

            if unicodedata.category(g) == 'Lu' or unicodedata.category(g) == 'Nd' and y >= 0 and y <= capHeight:
                if ldist < quarterwidth and ldist != 0:
                    ldistsmean.append(abs(ldist))
                else:
                    ldistsmean.append(abs(quarterwidth))
                if rdist < quarterwidth and rdist != 0:
                    rdistsmean.append(abs(rdist))
                else:
                    rdistsmean.append(abs(quarterwidth))
            elif unicodedata.category(g) == 'Ll' and y >= 0 and y <= xHeight:
                if ldist < quarterwidth and ldist != 0:
                    ldistsmean.append(abs(ldist))
                else:
                    ldistsmean.append(abs(quarterwidth))
                if rdist < quarterwidth and rdist != 0:
                    rdistsmean.append(abs(rdist))
                else:
                    rdistsmean.append(abs(quarterwidth))
            elif y >= 0 and y <= xHeight:
                if ldist < quarterwidth and ldist != 0:
                    ldistsmean.append(abs(ldist))
                else:
                    ldistsmean.append(abs(quarterwidth))
                if rdist < quarterwidth and rdist != 0:
                    rdistsmean.append(abs(rdist))
                else:
                    rdistsmean.append(abs(quarterwidth))
    
    if useMean:
        #print(g,ldistsmean, rdistsmean)
        lmean = int(geometric_mean(ldistsmean))
        #lmean = int(fmean(ldistsmean))
        # if lmean > quarterwidth:
        #    lmean = quarterwidth
        rmean = int(geometric_mean(rdistsmean))
        #rmean = int(fmean(rdistsmean))
        # if rmean > quarterwidth:
        #    rmean = quarterwidth
    else:
        if unicodedata.category(g) == 'Lu':
            lmean = ucAvg
            rmean = ucAvg
        elif unicodedata.category(g) == 'Ll':
            lmean = lcAvg
            rmean = lcAvg
        elif unicodedata.category(g) == 'Nd':
            lmean = ucAvg
            rmean = ucAvg
        else:
            lmean = lcAvg
            rmean = lcAvg

    strokeWidth(1)

    stroke(0)
    lineDash(14, 14)
    line((0, -500),(0,height()+500))
    line((glf.width, -500),(glf.width,height()+500))
    stroke(0, 0, 0, 0.5)
    lineDash(4, 4)
    line((glf.width/2, -500),(glf.width/2,height()+500))

    lineDash(6,6)
    stroke(0, 0, 1)
    line((lmean, -500),(lmean,height()+500))
    line((glf.width - rmean, -500),(glf.width - rmean,height()+500))

    lrange = int(lmean / 2)
    rrange = int(rmean / 2)

    lcontour = []
    rcontour = []
    
    lineDash(None)
    
    drawGlyph(g)

    stroke(0, 0, 1)
    strokeWidth(3)
    for i, j in ldistvals.items():
        zone = 0
        if j == None:
            zone = 0+zonevalue
        elif j in range(lmean-lrange, lmean+lrange):
            zone = 0
        elif j not in range(lmean-lrange, lmean+lrange) and j > lmean + lrange:
            zone = 0+zonevalue
        elif j not in range(lmean-lrange, lmean+lrange) and j < lmean - lrange:
            zone = 0-zonevalue
        lcontour.append(tuple((zone, i)))

    for i, j in rdistvals.items():
        zone = glf.width
        if j == None:
            zone = glf.width-zonevalue
        elif j in range(rmean-rrange, rmean+rrange):
            zone = glf.width
        elif j not in range(rmean-rrange, rmean+rrange) and j > rmean + rrange:
            zone = glf.width-zonevalue
        elif j not in range(rmean-rrange, rmean+rrange) and j < rmean - rrange:
            zone = glf.width+zonevalue
        rcontour.append(tuple((zone, i)))
    
    for i, pt in enumerate(lcontour):
        if i == len(lcontour)-1:
            continue
        else:
            stroke(None)
            B = BezierPath()
            B.moveTo(pt)
            B.lineTo(lcontour[i+1])
            B.closePath()
            E = B.expandStroke(expandedsize)
            if pt[0] == zonevalue and lcontour[i+1][0] == zonevalue:
                fill(*low)
            elif pt[0] == -zonevalue and lcontour[i+1][0] == -zonevalue:
                fill(*high)
            elif pt[0] == 0 and lcontour[i+1][0] == 0:
                fill(*neutral)
            elif pt[0] == -zonevalue and lcontour[i+1][0] == 0:
                linearGradient((-zonevalue,0),(0,0),[(high),(neutral)])
            elif pt[0] == 0 and lcontour[i+1][0] == -zonevalue:
                linearGradient((0,0),(-zonevalue,0),[(neutral),(high)])
            elif pt[0] == -zonevalue and lcontour[i+1][0] == zonevalue:
                linearGradient((-zonevalue,0),(zonevalue,0),[(high),(low)])
            elif pt[0] == zonevalue and lcontour[i+1][0] == -zonevalue:
                linearGradient((zonevalue,0),(-zonevalue,0),[(low),(high)])
            elif pt[0] == zonevalue and lcontour[i+1][0] == 0:
                linearGradient((zonevalue,0),(0,0),[(low),(neutral)])
            elif pt[0] == 0 and lcontour[i+1][0] == zonevalue:
                linearGradient((0,0),(zonevalue,0),[(neutral),(low)])
            else:
                fill(0.6,0.6,0.6)
            drawPath(E)
    
    for i, pt in enumerate(rcontour):
        if i == len(rcontour)-1:
            continue
        else:
            stroke(None)
            B = BezierPath()
            B.moveTo(pt)
            B.lineTo(rcontour[i+1])
            B.closePath()
            E = B.expandStroke(expandedsize)
            if glf.width - pt[0] == zonevalue and glf.width - rcontour[i+1][0] == zonevalue:
                fill(*low)
            elif glf.width - pt[0] == -zonevalue and glf.width - rcontour[i+1][0] == -zonevalue:
                fill(*high)
            elif glf.width - pt[0] == 0 and glf.width - rcontour[i+1][0] == 0:
                fill(*neutral)
            elif glf.width - pt[0] == -zonevalue and glf.width - rcontour[i+1][0] == 0:
                linearGradient((glf.width+zonevalue,0),(glf.width,0),[(high),(neutral)])
            elif glf.width - pt[0] == 0 and glf.width - rcontour[i+1][0] == -zonevalue:
                linearGradient((glf.width,0),(glf.width+zonevalue,0),[(neutral),(high)])
            elif glf.width - pt[0] == -zonevalue and glf.width - rcontour[i+1][0] == zonevalue:
                linearGradient((glf.width+zonevalue,0),(glf.width-zonevalue,0),[(high),(low)])
            elif glf.width - pt[0] == zonevalue and glf.width - rcontour[i+1][0] == -zonevalue:
                linearGradient((glf.width-zonevalue,0),(glf.width+zonevalue,0),[(low),(high)])
            elif glf.width - pt[0] == zonevalue and glf.width - rcontour[i+1][0] == 0:
                linearGradient((glf.width-zonevalue,0),(glf.width,0),[(low),(neutral)])
            elif glf.width - pt[0] == 0 and glf.width - rcontour[i+1][0] == zonevalue:
                linearGradient((glf.width,0),(glf.width-zonevalue,0),[(neutral),(low)])
            else:
                fill(0.6,0.6,0.6)
            drawPath(E)


ucAvg = midDist("H")
lcAvg = midDist("n")


newPage("A4Landscape")
colCount = 0
rowCount = -1

scalingValue = 0.1
col_subs = 6
row_subs = 4


grid = Grid.from_margins((-50, -50, -50, -50), 
                         column_subdivisions=col_subs, 
                         row_subdivisions=row_subs, 
                         column_gutter=5, 
                         row_gutter=5)


for g, gname in enumerate(glist):
    if colCount == col_subs:
        rowCount -= 1
        colCount = 0
    if rowCount == -(row_subs+1):
        rowCount = -1
        newPage("A4Landscape")
        
    fg = UV2AGL[ord(gname)]
    glf = f.getGlyphSet()[fg]
    hMid = glf.width/2
    vMid = xHeight/2
    
    path = BezierPath()
    path.rect(grid.columns[colCount], grid.rows[rowCount], grid.columns*1, grid.rows*-1)
    
    with savedState():
        clipPath(path)
        translate((grid.columns[colCount]+(grid.width/(col_subs*2)))-(hMid * scalingValue),
                  (grid.rows[rowCount]-(grid.height/row_subs))+(grid.width/(row_subs*3.1))-(vMid * scalingValue))
        scale(scalingValue)
        gB = getBez(gname)
        drawContour(gname, gB)

    fill(None)
    stroke(0.75,0.75,0.75)
    strokeWidth(0.75)
    drawPath(path)
    colCount += 1

db.saveImage(f"proofs/Profiler_test.pdf")


