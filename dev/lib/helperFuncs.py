"""
Helper functions for checkParallel
They're here because I don't like having to scroll around too much
"""

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

def checkIfSegmentHasBeenSelected(contour):
    """
    Function takes in contour and return true if
    any segment has been selected
    """
    for segment in contour:
        if segment.selected:
            return True

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

def collectAllPointsInContour(contour):
    pointsList = []
    for point in contour.points:
        pointsList.append(point)

    return pointsList

def findPrevOnCurvePt(point, pointsList):
    onCurves = []
    # Find all the non offcurves
    for pt in pointsList:
        if pt.type != "offcurve":
            onCurves.append(pt)
    # Find the matching point from a list of onCurves and
    # and return the *preceding* point
    for index, pt in enumerate(onCurves):
        if pt == point:
            return onCurves[index - 1]
