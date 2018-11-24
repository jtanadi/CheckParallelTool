"""
A simple tool to check & visualize if the line connecting handles
and the line connecting on-curve points are parallel.

Inspired by the What I learned from Rod Cavazos section of
OHno Type Co's "Drawing Vectors for Type & Lettering":
https://ohnotype.co/blog/drawing-vectors

When active, this tool adds an observer to keep an eye on
the tolerance setting posted by ToleranceWindow.
"""
from AppKit import NSImage
import os.path

import mojo.drawingTools as dt
from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView

from toleranceWindow import ToleranceWindow
import utils.helperFuncs as hf

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "resources", "toleranceSetting.txt")
iconFileDir = os.path.join(currentDir, "..", "resources", "checkParallelIcon.pdf")
toolbarIcon = NSImage.alloc().initWithContentsOfFile_(iconFileDir)

class CheckParallelTool(EditingTool):
    def setup(self):
        """
        Watch for events posted by ToleranceWindow():
        - Settings have changed -> run self.applyTolerance()
        - ToleranceWindow() is open -> toggle switch (prevents 2 windows)
        - ToleranceWindow() is closed -> toggle switch (to allow open next time)
        """
        self.glyph = CurrentGlyph()
        self.tolerance = hf.readSetting(settingDir)
        self.toleranceWindow = ToleranceWindow()

        self.mouseDownPoint = None
        self.canMarquee = True
        self.lineWeightMultiplier = 1

        # Use a dict so we can keep track of what each selectedSegment belongs to
        self.selectedContours = {}

        addObserver(self, "_applyTolerance", "com.ToleranceSettingChanged")

    def getToolbarIcon(self):
        return toolbarIcon

    def getToolbarTip(self):
        return "Check Parallel Tool"

    def becomeInactive(self):
        removeObserver(self, "com.ToleranceSettingChanged")

    def mouseDown(self, point, clickCount):
        """
        Mouse down stuff.
        On double click, open toleranceWindow

        Otherwise, record mouse position,
        oncurve & bcp positions, and do some math.
        """
        if clickCount == 2:
            self.toleranceWindow.w.open()

        self.ptsFromSelectedCtrs = self._getPointsFromSelectedContours()
        if len(self.ptsFromSelectedCtrs) != 1:
            return

        # Get positions of mouse & bcps and do some math
        self.mouseDownPoint = point

        for cluster in self.ptsFromSelectedCtrs:
            self.pt0, self.pt1, self.pt2, self.pt3 =\
            cluster[0], cluster[1], cluster[2], cluster[3]    

        self.pt0Pos = self.pt0.position
        self.pt1Pos = self.pt1.position
        self.pt2Pos = self.pt2.position
        self.pt3Pos = self.pt3.position

        self.slope0, self.intercept0 = hf.getSlopeAndIntercept(self.pt0Pos, self.pt2Pos)
        self.slope1, self.intercept1 = hf.getSlopeAndIntercept(self.pt1Pos, self.pt3Pos)

        self._keepSegmentSelected()

    def mouseUp(self, point):
        """
        Reset some values
        """
        self._keepSegmentSelected()
        self.mouseDownPoint = None
        self.canMarquee = True
        self.lineWeightMultiplier = 1
        self.glyph.performUndo()

    def mouseDragged(self, point, delta):
        """
        Do some math and figure out where BCPs should
        go as the mouse is being dragged around.
        """
        self.glyph.prepareUndo("Move handles")

        # For now, only allow editing when one segment is selected
        if len(self.ptsFromSelectedCtrs) != 1:
            return
        if self.mouseDownPoint is None:
            return

        # Differences b/w mousedown point and bcp points
        pt2DiffX = self.mouseDownPoint.x - self.pt2Pos[0]
        pt2DiffY = self.mouseDownPoint.y - self.pt2Pos[1]
        pt3DiffX = self.mouseDownPoint.x - self.pt3Pos[0]
        pt3DiffY = self.mouseDownPoint.y - self.pt3Pos[1]

        # Calculate now, but some will be overidden below
        pt2XtoUse = point.x - pt2DiffX
        pt2YtoUse = point.y - pt2DiffY
        pt3XtoUse = point.x - pt3DiffX
        pt3YtoUse = point.y - pt3DiffY

        # First BCP
        # X = difference b/w mouse X and point's X
        # Y =  point's current Y (horizontal line)
        if self.slope0 == 0:
            pt2YtoUse = self.pt2Pos[1]

        # X = point's current X (vertical line)
        # Y = difference b/w mouse Y and point's Y
        elif self.slope0 is None:
            pt2XtoUse = self.pt2Pos[0]

        # X = calculated from diff b/w mouse Y and point's Y (slope b/w horizontal and 45deg)
        # Y = difference b/w mouse Y and point's Y
        elif 0 < abs(self.slope0) <= 1:
            pt2XtoUse = (pt2YtoUse - self.intercept0) / self.slope0

        # X = difference b/w mouse X and point's X
        # Y = calculated from diff b/w mouse X and point's X (slope b/w and 45deg and vert)
        else:
            pt2YtoUse = self.slope0 * pt2XtoUse + self.intercept0

        # Second BCP, same as above
        if self.slope1 == 0:
            pt3YtoUse = self.pt3Pos[1]
        elif self.slope1 is None:
            pt3XtoUse = self.pt3Pos[0]
        elif 0 < abs(self.slope1) <= 1:
            pt3XtoUse = (pt3YtoUse - self.intercept1) / self.slope1
        else:
            pt3YtoUse = self.slope1 * pt3XtoUse + self.intercept1

        self.pt2.position = (round(pt2XtoUse), round(pt2YtoUse))
        self.pt3.position = (round(pt3XtoUse), round(pt3YtoUse))

        self.glyph.changed()

    # def canSelectWithMarque(self):
    #     return False

    # def getMarqueRect(self, offset=None, previousRect=False):
    #     if not self.canMarquee:
    #         return None
    #     return super().getMarqueRect(offset, previousRect)

    def draw(self, scale):
        """
        Draw lines
        """
        self._analyzeSelection()
        self.ptsFromSelectedCtrs = self._getPointsFromSelectedContours()

        # Only draw if something has been selected
        if not self.selectedContours.values():
            return

        for cluster in self.ptsFromSelectedCtrs:
            pt0, pt1, pt2, pt3 = cluster[0].position, cluster[1].position,\
                                 cluster[2].position, cluster[3].position
            # Parallel-ish lines are green; otherwise, red
            if hf.areTheyParallel((pt0, pt1), (pt2, pt3), self.tolerance):
                dt.stroke(0, 0, 1, 1)
            else:
                dt.stroke(1, 0, 0, 1)

            dt.strokeWidth(scale)
            dt.line(pt0, pt1)

            dt.strokeWidth(scale * self.lineWeightMultiplier)
            dt.line(pt2, pt3)

    def _applyTolerance(self, info):
        """
        Redefine tolerance whenever com.ToleranceSettingChanged is triggered
        """
        self.tolerance = hf.readSetting(settingDir)

    def _analyzeSelection(self):
        """
        Look at what's selected and add appropriate segment(s) to
        the self.selectedContours dict.
        We don't explicitly check if a segment is a curve because we don't draw
        segments without offcurves in drawLines() anyway.
        """
        self.selectedContours.clear()

        # Find which segments in each contour are selected
        for contour in self.glyph:
            selectedSegments = []

            for segment in contour:
                if segment.selected:
                    selectedSegments.append(segment)

                for point in segment:
                    # Treat offcurve selection normally (only add current segment)
                    if point.selected and point.type == "offcurve":
                        selectedSegments.append(segment)

                    # If an oncurve is selected, add current and next segments
                    # so user can balance pt between 2 segments
                    elif point.selected:
                        # If any point adjacent to current point is selected, then
                        # a segment has been selected, and it's been taken care of above
                        # This prevents 2 segments from being selected when user
                        # selects a segment.
                        if hf.findPrevPt(point, contour).selected\
                        or hf.findNextPt(point, contour).selected:
                            continue

                        # If it's the last segment (no next index), add first segment
                        try:
                            selectedSegments.append(contour[segment.index + 1])
                        except IndexError:
                            selectedSegments.append(contour[0])

                        selectedSegments.append(segment)

            if selectedSegments:
                self.selectedContours[contour.index] = selectedSegments

    def _getPointsFromSelectedContours(self):
        """
        Return all selected points (oncurves & bcps)
        as a list of tuples of tuples
        [
            ((x0, y0), (x1, y1), (x2, y2), (x3, y3)),
            ((x4, y4), (x5, y5), (x6, y6), (x7, y7)),
            ...
        ]

        **Actual points are returned, not positions**
        """
        selectedPoints = []
        for index, selectedSegments in self.selectedContours.items():
            currentContour = self.glyph[index]
            for segment in selectedSegments:
                selectedOnCurves = [point for point in segment.points if point.type != "offcurve"]
                selectedOffCurves = [point for point in segment.points if point.type == "offcurve"]

                # If no selectedOffCurves, it's a straight line, so ignore
                if not selectedOffCurves:
                    continue

                pt0 = hf.findPrevPt(selectedOnCurves[0], currentContour)
                pt1 = selectedOnCurves[0]
                pt2 = selectedOffCurves[0]
                pt3 = selectedOffCurves[1]

                selectedPoints.append((pt0, pt1, pt2, pt3))
        return selectedPoints

    def _keepSegmentSelected(self):
        """
        Keep segment selected when click point is w/in
        line connecting bcps

        For now, only do this when 1 segment is selected
        """
        if not self.ptsFromSelectedCtrs:
            return
        if len(self.ptsFromSelectedCtrs) != 1:
            return

        for cluster in self.ptsFromSelectedCtrs:
            # First 2 items are oncurve positions
            pt2Pos, pt3Pos = cluster[2].position, cluster[3].position

            if not hf.isPointInLine(self.mouseDownPoint, (pt2Pos, pt3Pos)):
                continue

            self.canMarquee = False
            self.lineWeightMultiplier = 4

            for selectedSegments in self.selectedContours.values():
                for segment in selectedSegments:
                    segment.selected = True


installTool(CheckParallelTool())
