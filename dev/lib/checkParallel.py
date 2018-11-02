import helperFuncs as hf
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

    def mouseDown(self, point, clickCount):
        pass
        # Implement a double click to change tolerance later
        # if clickCount == 2:

    def draw(self, scale):
        """
        Only using this like a middleperson so I can name the process
        (ie. with functions)
        scale is given by RF (part of BaseEventTool.draw())
        """
        self.analyzeSelection()

        # If AT LEAST one segment from ONLY one contour has been selected
        if self.selectedSegments and len(self.selectedContours) == 1:
            self.drawLines(scale)
    
    def analyzeSelection(self):
        self.selectedContours.clear()
        self.selectedSegments.clear()

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

    def drawLines(self, lineThickness):
        contourPoints = hf.collectAllPointsInContour(self.selectedContours[0])

        for segment in self.selectedSegments:
            selectedOnCurves = []
            selectedOffCurves = []
            for point in segment.points:
                if point.type == "offcurve":
                    selectedOffCurves.append(point)
                else:
                    selectedOnCurves.append(point)

            pt0 = hf.findPrevOnCurvePt(selectedOnCurves[0], contourPoints).position
            pt1 = selectedOnCurves[0].position
            pt2 = selectedOffCurves[0].position
            pt3 = selectedOffCurves[1].position

            # if lines are parallel, lines are green; otherwise, red
            if hf.areTheyParallel((pt0, pt1), (pt2, pt3), self.tolerance):
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
