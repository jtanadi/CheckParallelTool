"""
A simple tool to check & visualize if the line connecting handles
and the line connecting on-curve points are parallel.

Inspired by the What I learned from Rod Cavazos section of
OHno Type Co's "Drawing Vectors for Type & Lettering":
https://ohnotype.co/blog/drawing-vectors

When active, this tool adds an observer to keep an eye on
the tolerance setting posted by ToleranceWindow.
"""

import os.path
from AppKit import NSImage

import mojo.drawingTools as dt
from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView

import utils.helperFuncs as hf
from toleranceWindow import ToleranceWindow

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

        self.mouseDownPoint = None
        self.scaleForScale = 1

        # Set a switch to prevent user from opening 2 ToleranceWindow()
        self.canOpenSetting = True

        # Use a dict so we can keep track of what each selectedSegment belongs to
        self.selectedContours = {}

        addObserver(self, "applyTolerance", "comToleranceSettingChanged")
        addObserver(self, "toggleOpenSwitch", "comToleranceWindowOpened")
        addObserver(self, "toggleOpenSwitch", "comToleranceWindowClosed")

    def getToolbarIcon(self):
        return toolbarIcon

    def getToolbarTip(self):
        return "Check Parallel Tool"

    def becomeInactive(self):
        removeObserver(self, "comToleranceSettingChanged")
        removeObserver(self, "comToleranceWindowOpened")
        removeObserver(self, "comToleranceWindowClosed")

    def toggleOpenSwitch(self, info):
        """
        A switch that's run everytime the tool is notified
        when the ToleranceWindow() is opened or closed
        """
        self.canOpenSetting = not self.canOpenSetting


    def applyTolerance(self, info):
        """
        Redefine tolerance whenever comToleranceSettingChanged is triggered
        """
        self.tolerance = hf.readSetting(settingDir)

    def analyzeSelection(self):
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

    def getSelectedPointsPos(self):
        """
        Get positions of selected points
        """
        self.selectedPointPosList = []
        for index, selectedSegments in self.selectedContours.items():
            currentContour = self.glyph[index]
            for segment in selectedSegments:
                selectedOnCurves = [point for point in segment.points if point.type != "offcurve"]
                selectedOffCurves = [point for point in segment.points if point.type == "offcurve"]

                # If no selectedOffCurves, it's a straight line, so ignore
                if not selectedOffCurves:
                    continue

                pt0 = hf.findPrevPt(selectedOnCurves[0], currentContour).position
                pt1 = selectedOnCurves[0].position
                pt2 = selectedOffCurves[0].position
                pt3 = selectedOffCurves[1].position

                self.selectedPointPosList.append((pt0, pt1, pt2, pt3))

    def keepSegmentSelected(self):
        """
        Keep segment selected when click point is w/in
        line connecting bcps
        """
        if not self.selectedPointPosList:
            return

        for cluster in self.selectedPointPosList:
            # First 2 items are oncurve positions
            pt2, pt3 = cluster[2], cluster[3]

            if not hf.isPointInLine(self.mouseDownPoint, (pt2, pt3)):
                continue

            self.scaleForScale = 4
            for selectedSegments in self.selectedContours.values():
                for segment in selectedSegments:
                    segment.selected = True

    def mouseDown(self, point, clickCount):
        """
        Double-click to open ToleranceWindow() if it hasn't been opened
        """
        if clickCount == 2 and self.canOpenSetting:
            ToleranceWindow()
        self.scaleForScale = 1
        # self.analyzeSelection()
        self.getSelectedPointsPos()
        self.mouseDownPoint = point

        for index, selectedSegments in self.selectedContours.items():
            currentContour = self.glyph[index]
            for segment in selectedSegments:
                selectedOnCurves = [point for point in segment.points if point.type != "offcurve"]
                selectedOffCurves = [point for point in segment.points if point.type == "offcurve"]

                # If no selectedOffCurves, it's a straight line, so ignore
                if not selectedOffCurves:
                    continue

                self.pt0 = hf.findPrevPt(selectedOnCurves[0], currentContour).position
                self.pt1 = selectedOnCurves[0].position
                self.pt2 = selectedOffCurves[0].position
                self.pt3 = selectedOffCurves[1].position

                self.slope0, self.intercept0 = hf.getSlopeAndIntercept(self.pt0, self.pt2)
                self.slope1, self.intercept1 = hf.getSlopeAndIntercept(self.pt1, self.pt3)

                # print("slope0", self.slope0)
                # print("slope1", self.slope1)

        self.keepSegmentSelected()

    def mouseUp(self, point):
        self.keepSegmentSelected()
        self.mouseDownPoint = None
        # self.glyph.performUndo()

    def mouseDragged(self, point, delta):
        self.glyph.prepareUndo("Move handles")

        for index, selectedSegments in self.selectedContours.items():
            currentContour = self.glyph[index]
            for segment in selectedSegments:
                selectedOffCurves = [point for point in segment.points if point.type == "offcurve"]

                # If no selectedOffCurves, it's a straight line, so ignore
                if not selectedOffCurves:
                    continue

                # if not hf.isPointInLine(self.mouseDownPoint, (pt2, pt3)):
                #     continue

                # print(pt0, pt2, slope0)
                # print(pt1, pt3, slope1)

                # Differences b/w mousedown point and bcp points
                pt2DiffX = self.mouseDownPoint.x - self.pt2[0]
                pt2DiffY = self.mouseDownPoint.y - self.pt2[1]
                pt3DiffX = self.mouseDownPoint.x - self.pt3[0]
                pt3DiffY = self.mouseDownPoint.y - self.pt3[1]

                pt2XtoUse = point.x - pt2DiffX
                pt2YtoUse = point.y - pt2DiffY
                pt3XtoUse = point.x - pt3DiffX
                pt3YtoUse = point.y - pt3DiffY

                # Horizontal line
                if self.slope0 == 0:
                    pt2YtoUse = self.pt2[1]
                
                # Vertical line
                elif self.slope0 is None:
                    pt2XtoUse = self.pt2[0]
                
                # Slope between horizontal and 45deg
                elif 0 < self.slope0 <= 1:
                    pt2YtoUse = self.slope0 * self.pt2[0] + self.intercept0
                    print('hey')

                elif self.slope0 > 1:
                    pt2XtoUse = (self.pt2[1] - self.intercept0) / self.slope0


                if self.slope1 == 0:
                    pt3YtoUse = self.pt3[1]
                elif self.slope1 is None:
                    pt3YtoUse = self.pt3[0]
                elif 0 < self.slope1 <= 1:
                    pt3YtoUse = self.slope1 * self.pt3[0] + self.intercept1
                elif self.slope1 > 1:
                    pt3XtoUse = (self.pt3[1] - self.intercept1) / self.slope1

                selectedOffCurves[0].position = (round(pt2XtoUse), round(pt2YtoUse))
                selectedOffCurves[1].position = (round(pt3XtoUse), round(pt3YtoUse))

        self.glyph.changed()
        self.keepSegmentSelected()

    def draw(self, scale):
        """
        Draw lines
        """
        self.analyzeSelection()
        self.getSelectedPointsPos()

        # Only draw if something has been selected
        if not self.selectedContours.values():
            return

        for cluster in self.selectedPointPosList:
            pt0, pt1, pt2, pt3 = cluster[0], cluster[1], cluster[2], cluster[3]
            # Parallel-ish lines are green; otherwise, red
            if hf.areTheyParallel((pt0, pt1), (pt2, pt3), self.tolerance):
                dt.stroke(0, 0, 1, 1)
            else:
                dt.stroke(1, 0, 0, 1)

            dt.strokeWidth(scale)
            dt.line(pt0, pt1)

            dt.strokeWidth(scale * self.scaleForScale)
            dt.line(pt2, pt3)



installTool(CheckParallelTool())
