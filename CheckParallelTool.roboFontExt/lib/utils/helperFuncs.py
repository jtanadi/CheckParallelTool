"""
Helper functions for CheckParallel and ToleranceWindow
They're here because I don't like having to scroll around too much
"""
import math

def readSetting(settingDir):
    """
    Read value of setting file. If file is somehow missing,
    write one with an abitrary value (0.05) for now.
    This is shared between CheckParallel() and ToleranceWindow()
    """
    try:
        with open(settingDir, "r") as settingFile:
            tolerance = float(settingFile.read())
    except FileNotFoundError:
        with open(settingDir, "w+") as settingFile:
            tolerance = 2.5
            settingFile.write(str(tolerance))
    return tolerance

def getSlopeAndIntercept(pt0, pt1):
    x0, y0 = pt0
    x1, y1 = pt1

    try:
        slope = (y1 - y0) / (x1 - x0)
    except ZeroDivisionError:
        slope = None

    # y = mx + b
    if slope is not None:
        intercept = y0 - (slope * x0)
    else:
        intercept = 0

    return slope, intercept

def makeRectFromTwoPoints(pt0, pt1, width):
    """
    Return 4 points that make a rectangle
    pt0 and pt1 are midpoints of opposite sides
    """
    pt0x, pt0y = pt0
    pt1x, pt1y = pt1

    slope, intercept = getSlopeAndIntercept(pt0, pt1)

    dx = 0
    dy = 0
    # Vertical
    if slope is None:
        dx = width / 2
    # Horizontal
    elif slope == 0:
        dy = width / 2
    else:
        perpSlope = -1 / slope
        dx = math.sqrt(width**2 / (1 + perpSlope**2)) / 2
        dy = perpSlope * dx

    ax = round(pt0x - dx)
    ay = round(pt0y - dy)
    bx = round(pt1x - dx)
    by = round(pt1y - dy)
    cx = round(pt1x + dx)
    cy = round(pt1y + dy)
    dx = round(pt0x + dx)
    dy = round(pt0y + dy)

    return ((ax, ay), (bx, by), (cx, cy), (dx, dy))

def calcAreaOfTriangle(pt0, pt1, pt2):
    """
    Return area of triangle defined by 3 points
    """
    ax, ay = pt0
    bx, by = pt1
    cx, cy = pt2

    return abs((ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)) / 2)

def isPointInLine(point, line, scale):
    """
    Check if point is w/in line, with some tolerance.

    "Tolerance" is achieved by drawing a rectangle along
    the line and testing whether the point is inside or
    outside of the rectangle.

    More on point-in-rectangle checking here:
    https://bit.ly/2PYwLQY
    """
    if point is None or line is None:
        return False

    # tolerance rect gets larger as user
    # zooms out, smaller as user zooms in,
    # to certain sizes
    if scale >= 2:
        scale = 2
    elif scale <= 0.3:
        scale = 0.3

    tolerance = 10 * scale
    pt0, pt1 = line

    clickableRect = makeRectFromTwoPoints(pt0, pt1, tolerance)
    a = clickableRect[0]
    b = clickableRect[1]
    c = clickableRect[2]
    d = clickableRect[3]

    rectArea = calcAreaOfTriangle(a, b, c) + calcAreaOfTriangle(a, c, d)
    triPAB = calcAreaOfTriangle(point, a, b)
    triPBC = calcAreaOfTriangle(point, b, c)
    triPCD = calcAreaOfTriangle(point, c, d)
    triPAD = calcAreaOfTriangle(point, a, d)

    return rectArea == triPAB + triPBC + triPCD + triPAD

def areTheyParallel(line1, line2, tolerance=0):
    """
    Checks if 2 lines are parallel by comparing their slopes
    line1 and line2 should be a tuple of tuples each: ((x0, y0), (x1, y1))
    tolerance defaults to 0
    """
    ((x0, y0), (x1, y1)) = line1
    ((x2, y2), (x3, y3)) = line2

    # atan returns rads, so convert to angle
    angle1 = abs(math.atan2((y1 - y0), (x1 - x0)) * 180 / math.pi)
    angle2 = abs(math.atan2((y3 - y2), (x3 - x2)) * 180 / math.pi)

    # instead of checking for absolute equality,
    # allow for some tolerance
    return abs(angle1 - angle2) <= tolerance

def findPrevPt(point, contour, pointType=None):
    """
    Find the matching point from a contour and
    return the PREV point of the specified type.
    If pointType isn't specified, look for non-offcurves(lines and curves)
    """
    if pointType is None:
        pointsOfType = [pt for pt in contour.points if pt.type != "offcurve"]
    else:
        pointsOfType = [pt for pt in contour.points if pt.type == pointType]

    for index, pt in enumerate(pointsOfType):
        if pt == point:
            return pointsOfType[index - 1]

def findNextPt(point, contour, pointType=None):
    """
    Find the matching point from a contour and
    return the NEXT point of the specified type.
    If pointType isn't specified, look for non-offcurves(lines and curves)
    """
    if pointType is None:
        pointsOfType = [pt for pt in contour.points if pt.type != "offcurve"]
    else:
        pointsOfType = [pt for pt in contour.points if pt.type == pointType]

    for index, pt in enumerate(pointsOfType):
        if pt == point:
            # return None

            # If next point doesn't exist (last point), return first point
            try:
                return pointsOfType[index + 1]
            except IndexError:
                return contour.points[0]

def writeSetting(settingDir, value):
    """
    Write setting to file or make new file if
    setting file doesn't exist.
    """
    with open(settingDir, "w+") as settingFile:
        settingFile.write(str(value))

if __name__ == "__main__":
    # print(makeRectFromTwoPoints((20, 20), (100, 100), 6))
    # print(calcAreaOfTriangle((20, 20), (40, 40), (30, 80)))

    line = ((477, 406), (410, 490))
    print(isPointInLine((436.518, 455.973), line))
