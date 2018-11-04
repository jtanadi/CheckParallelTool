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

        # Use a dict so we can keep track of what each selectedSegment belongs to
        self.selectedContours = {}

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

        # Only draw if something has been selected
        if self.selectedContours.values():
            self.drawLines(scale)

    def analyzeSelection(self):
        self.selectedContours.clear()

        # Find which segments in each contour are selected
        for contour in self.glyph:
            selectedSegments = []

            # Check if any segment has been selected first.
            # If not, when we check if an oncurve point is selected later,
            # we won't know if a segment has been selected,
            # and the point AND the next segment will be selected.
            if hf.checkIfSegmentHasBeenSelected(contour):
                selectedSegments = [segment for segment in contour\
                                    if segment.selected and segment.type == "curve"]
            else:
                for segment in contour:
                    for point in segment:
                        if point.selected and point.type == "offcurve":
                            selectedSegments.append(segment)
                        elif point.selected:
                            # When an oncurve point is selected,
                            # append current segment and next segment,
                            # so user can balance point between 2 segments
                            segmentIndex = segment.index
                            selectedSegments.append(segment)
                            # If it's the last segment (no next index),
                            # add the first segment
                            try:
                                selectedSegments.append(contour[segmentIndex + 1])
                            except IndexError:
                                selectedSegments.append(contour[0])

            self.selectedContours[contour.index] = selectedSegments

    def drawLines(self, lineThickness):
        for index in self.selectedContours:
            contourPoints = hf.collectAllPointsInContour(self.glyph.contours[index])
            for segment in self.selectedContours[index]:
                selectedOnCurves = [point for point in segment.points if point.type != "offcurve"]
                selectedOffCurves = [point for point in segment.points if point.type == "offcurve"]

                pt0 = hf.findPrevOnCurvePt(selectedOnCurves[0], contourPoints).position
                pt1 = selectedOnCurves[0].position
                pt2 = selectedOffCurves[0].position
                pt3 = selectedOffCurves[1].position

                # if lines are parallel, lines are green; otherwise, red
                if hf.areTheyParallel((pt0, pt1), (pt2, pt3), self.tolerance):
                    dt.stroke(0, 0, 1, 1)
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
