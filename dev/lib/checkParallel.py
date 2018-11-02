import mojo.drawingTools as dt
from mojo.events import EditingTool, installTool
from mojo.UI import UpdateCurrentGlyphView
from AppKit import NSImage
import os.path

currentDir = os.path.dirname(__file__)
iconFileDir = os.path.join(currentDir, "..", "resources", "checkParallelIcon.pdf")
toolbarIcon = NSImage.alloc().initWithContentsOfFile_(iconFileDir)

class CheckParallel(EditingTool):
    def setup(self):
        self.glyph = CurrentGlyph()
        self.tolerance = 0.05

        # These are lists so we can track how many of each is selected
        self.selectedContours = []
        self.selectedSegments = []

    def _collectPointsInContour(self, contour):
        pointsList = []
        for point in contour.points:
            pointsList.append(point)
        
        return pointsList
        
    def _findPrevOnCurvePt(self, point, pointsList):
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

    def _calcSlope(self, pt1, pt2):
        (xA, yA) = pt1
        (xB, yB) = pt2

        try:
            return (yB - yA) / (xB - xA)
        except ZeroDivisionError:
            return 0 # Not entirely accurate for vertical lines, but works

    def _checkParallel(self, line1, line2):        
        ((x0, y0), (x1, y1)) = line1
        ((x2, y2), (x3, y3)) = line2

        m1 = self._calcSlope((x0, y0), (x1, y1))
        m2 = self._calcSlope((x2, y2), (x3, y3))

        # instead of checking for absolute equality (m1 == m2),
        # allow for some tolerance
        return abs(m1 - m2) <= self.tolerance
    
    def mouseDown(self, point, clickCount):
        pass
        # Implement a double click to change tolerance later
        # if clickCount == 2:
            

    def draw(self, scale):
        # g = info["glyph"]

        self.selectedContours = []
        self.selectedSegments = []

        # Find selected segment... 
        # is this the best way (ie. do I have to iterate?)
        for contour in self.glyph.contours:
            for segment in contour:
                # When segments are selected, add to list and log the parent contour
                if segment.selected:
                    if segment.type != "curve":
                        continue
                    self.selectedSegments.append(segment)
                    if segment.contour not in self.selectedContours:
                        self.selectedContours.append(segment.contour)
                # Maybe point is selected instead, so iterate to see
                # if a point is selected, and then find its segment
                else:
                    for point in segment.points:
                        if point.type != "offcurve" or not point.selected:
                            continue
                        self.selectedSegments.append(segment)
                        if segment.contour not in self.selectedContours:
                            self.selectedContours.append(segment.contour)

        self.drawLines(scale)
        
    def drawLines(self, lineThickness):
        # Don't do anything if no segments have been selected,
        # or if more than 1 contour has been selected
        if not self.selectedSegments or len(self.selectedContours) > 1:
            return

        contourPoints = self._collectPointsInContour(self.selectedContours[0])

        for segment in self.selectedSegments:
            selectedOnCurves = []
            selectedOffCurves = []
            for point in segment.points:
                if point.type == "offcurve":
                    selectedOffCurves.append(point)
                else:
                    selectedOnCurves.append(point)
                    
            pt0 = self._findPrevOnCurvePt(selectedOnCurves[0], contourPoints).position
            pt1 = selectedOnCurves[0].position
            pt2 = selectedOffCurves[0].position
            pt3 = selectedOffCurves[1].position

            # if lines are parallel, lines are green; otherwise, red
            if self._checkParallel((pt0, pt1), (pt2, pt3)):
                dt.stroke(0, 1, 0, 1)
            else:
                dt.stroke(1, 0, 0, 1)

            dt.strokeWidth(lineThickness)
            dt.line(pt0, pt1)
            dt.line(pt2, pt3)

    def getToolbarIcon(self):
        return toolbarIcon

    def getToolbarTip(self):
        return "Check Parallel Tool"

installTool(CheckParallel())
