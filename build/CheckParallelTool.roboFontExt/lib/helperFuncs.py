"""
Helper functions for checkParallel
"""

def calcSlope(pt1, pt2):
    (xA, yA) = pt1
    (xB, yB) = pt2

    try:
        return (yB - yA) / (xB - xA)
    except ZeroDivisionError:
        return 0 # Not entirely accurate for vertical lines, but works


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
