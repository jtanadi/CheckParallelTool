"""
A simple tool to check & visualize if the line connecting handles
and the line connecting on-curve points are parallel.

Inspired by the What I learned from Rod Cavazos section of
OHno Type Co's "Drawing Vectors for Type & Lettering":
https://ohnotype.co/blog/drawing-vectors

When active, this tool adds an observer to keep an eye on
the tolerance setting posted by ToleranceWindow.
"""

import helperFuncs as hf
from toleranceWindow import ToleranceWindow
import mojo.drawingTools as dt
from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from AppKit import NSImage
import os.path

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

    def mouseDown(self, point, clickCount):
        """
        Double-click to open ToleranceWindow() if it hasn't been opened
        """
        if clickCount == 2 and self.canOpenSetting:
            ToleranceWindow()

    def applyTolerance(self, info):
        """
        Redefine tolerance whenever comToleranceSettingChanged is triggered
        """
        self.tolerance = hf.readSetting(settingDir)


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

            self.selectedContours[contour.index] = selectedSegments

    def drawLines(self, lineThickness):
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

                # if lines are parallel, lines are green; otherwise, red
                if hf.areTheyParallel((pt0, pt1), (pt2, pt3), self.tolerance):
                    dt.stroke(0, 1, 0, 1)
                else:
                    dt.stroke(1, 0, 0, 1)

                dt.strokeWidth(lineThickness)
                dt.line(pt0, pt1)
                dt.line(pt2, pt3)

installTool(CheckParallelTool())
