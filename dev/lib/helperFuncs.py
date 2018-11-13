"""
Helper functions for CheckParallel and ToleranceWindow
They're here because I don't like having to scroll around too much
"""

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
            tolerance = 0.025
            settingFile.write(str(tolerance))
    return tolerance

def calcSlope(pt1, pt2):
    """
    Given 2 points, calculate slope using m = y1 - y0 / x1 - x0
    pt1 and pt2 should be a tuple each (x, y)
    """
    (xA, yA) = pt1
    (xB, yB) = pt2

    try:
        return (yB - yA) / (xB - xA)
    except ZeroDivisionError:
        return 0 # Not entirely accurate for vertical lines, but works

def areTheyParallel(line1, line2, tolerance=0):
    """
    Checks if 2 lines are parallel by comparing their slopes
    line1 and line2 should be a tuple of tuples each: ((x0, y0), (x1, y1))
    tolerance defaults to 0
    """
    ((x0, y0), (x1, y1)) = line1
    ((x2, y2), (x3, y3)) = line2

    m1 = calcSlope((x0, y0), (x1, y1))
    m2 = calcSlope((x2, y2), (x3, y3))

    # instead of checking for absolute equality (m1 == m2),
    # allow for some tolerance
    return abs(m1 - m2) <= tolerance


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
            # If next point doesn't exist (last point), return first point
            try:
                return pointsOfType[index + 1]
            except IndexError:
                return contour.points[0]
