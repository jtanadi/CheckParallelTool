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

def getDistance(pt0, pt1):
    """
    Return distance between two points
    """
    if isinstance(pt0, tuple):
        pt0x = pt0[0]
        pt0y = pt0[1]
    else:
        pt0x = pt0.x
        pt0y = pt0.y

    if isinstance(pt1, tuple):
        pt1x = pt1[0]
        pt1y = pt1[1]
    else:
        pt1x = pt1.x
        pt1y = pt1.y

    return math.sqrt((pt1x - pt0x)**2 + (pt1y - pt0y)**2)

def isPointInLine(point, line, scale):
    """
    Check if point is w/in line, with some tolerance.

    "Tolerance" is achieved by testing whether the
    distance b/w the point and either end of the line
    is close enough to the length of the line.

    Sort of like this idea: https://bit.ly/2PYwLQY

    (Thanks Frederik!)
    """
    if point is None or line is None:
        return False

    # tolerance rect gets larger as user
    # zooms out, smaller as user zooms in,
    # to certain sizes
    if scale >= 1.5:
        scale = 1.5
    elif scale <= 0.3:
        scale = 0.3

    pt0, pt1 = line

    lineLength = getDistance(pt0, pt1)
    distance1 = getDistance(point, pt0)
    distance2 = getDistance(point, pt1)

    return abs(distance1 + distance2 - lineLength) < scale

def areTheyParallel(line1, line2, tolerance=0):
    """
    Checks if 2 lines are parallel by comparing their slopes
    line1 and line2 should be a tuple of tuples each: ((x0, y0), (x1, y1))
    tolerance defaults to 0
    """
    p0, p1 = line1
    p2, p3 = line2

    # atan returns rads, so convert to angle
    angle1 = abs(math.atan2((p1.y - p0.y), (p1.x - p0.x)) * 180 / math.pi)
    angle2 = abs(math.atan2((p3.y - p2.y), (p3.x - p2.x)) * 180 / math.pi)

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
    print(isPointInLine((436.518, 455.973), line, 1))
