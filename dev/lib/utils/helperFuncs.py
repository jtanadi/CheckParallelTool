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

def isPointInLine(point, line):
    """
    Check if point is w/in line.

    "Tolerance" is achieved by drawing a series of
    parallel lines and testing if point falls on any of them.

    For every iteration, draw 2 lines (one on either side)
    """
    if point is None or line is None:
        return False

    tolerance = 4
    x, y = round(point.x), round(point.y)
    pt0, pt1 = line
    line0Pt0x, line0Pt0y = pt0
    line0Pt1x, line0Pt1y = pt1

    # If point is outside of bounds, then obvs not in line
    if not line0Pt0x < x < line0Pt1x and\
        not line0Pt0y < y < line0Pt1y:
        return False
    line0Slope, line0Intercept = getSlopeAndIntercept(pt0, pt1)

    # Test with main line
    if y == round(line0Slope * x + line0Intercept):
        return True

    # Test with parallel lines
    lineIndex = 1
    for lineIndex in range(tolerance):
        dx = 0
        dy = 0
        # Vertical
        if line0Slope is None:
            dx = lineIndex
        # Horizontal
        elif line0Slope == 0:
            dy = lineIndex
        else:
            perpSlope = -1 / line0Slope
            dx = math.sqrt(lineIndex**2 / (1 + perpSlope**2)) / 2
            dy = perpSlope * dx

        # To the left of line0
        line1Pt0x = line0Pt0x - dx
        line1Pt0y = line0Pt0y - dy
        line1Pt1x = line0Pt1x - dx
        line1Pt1y = line0Pt1y - dy

        # To the right of line 0
        line2Pt0x = line0Pt1x + dx
        line2Pt0y = line0Pt1y + dy
        line2Pt1x = line0Pt0x + dx
        line2Pt1y = line0Pt0y + dy

        line1Slope, line1Intercept = getSlopeAndIntercept((line1Pt0x, line1Pt0y),
                                                          (line1Pt1x, line1Pt1y))
        line2Slope, line2Intercept = getSlopeAndIntercept((line2Pt0x, line2Pt0y),
                                                          (line2Pt1x, line2Pt1y))

        # Test with y = mx + b
        line1Y = round(line1Slope * x + line1Intercept)
        line2Y = round(line2Slope * x + line2Intercept)

        if y in (line1Y, line2Y):
            return True

    return False

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
