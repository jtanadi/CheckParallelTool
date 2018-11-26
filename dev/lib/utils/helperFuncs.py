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

def getSlopeAndIntercept(pt1, pt2):
    x0, y0 = pt1
    x1, y1 = pt2

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

def isPointInLine(clickPt, line):
    """
    Check if click point is w/in line
    drawn between bcps (+ tolerance)
    """
    if clickPt is None or line is None:
        return

    tolerance = 4
    xClick, yClick = clickPt
    pt1, pt2 = line
    slope, intercept = getSlopeAndIntercept(pt1, pt2)

    # Vertical line, so just check if clickPt is within tolerance
    # of line's x value and between pt1 y and pt2 y
    if slope is None:
        return abs(xClick - pt1[0]) <= tolerance\
            and ((pt1[1] > yClick > pt2[1])\
            or (pt1[1] < yClick < pt2[1]))

    calculatedY = (slope * xClick) + intercept

    return abs(yClick - calculatedY) <= tolerance\
        and ((pt1[0] > xClick > pt2[0])\
        or (pt1[0] < xClick < pt2[0]))

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
    import os.path
    currentDir = os.path.dirname(__file__)
    vizSetting = os.path.join(currentDir, "..", "..", "resources", "vizSetting.txt")

    toggleVizSetting(vizSetting)
