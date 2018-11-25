"""
Toggle parallel viz
"""
import os.path

import mojo.drawingTools as dt
from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from vanilla import FloatingWindow, CheckBox

from utils import helperFuncs as hf

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "resources", "toleranceSetting.txt")
toggleDir = os.path.join(currentDir, "..", "resources", "vizSetting.txt")

class ParallelGuideViz:
    def __init__(self):
        self.w = FloatingWindow((120, 40))
        self.w.checkBox = CheckBox((10, 10, -10, 20), "A CheckBox",
                                   callback=self.checkBoxCB, value=False)

        self.selectedContours = {}
        self.glyph = CurrentGlyph()
        self.tolerance = hf.readSetting(settingDir)
        self.lineWeightMultiplier = 1
        self.shouldDraw = False
        
        self.w.bind("close", self.closeCB)
        self.w.open()
        addObserver(self, "drawCB", "draw")

    def checkBoxCB(self, sender):
        if sender.get() == 1:
            self.shouldDraw = True
        else:
            self.shouldDraw = False
        UpdateCurrentGlyphView()

    def drawCB(self, info):
        if not self.shouldDraw:
            return
        self.drawLines(info["scale"])

    def drawLines(self, scale):
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

    def closeCB(self, sender):
        removeObserver(self, "draw")
        UpdateCurrentGlyphView()

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

if __name__ == "__main__":
    ParallelGuideViz()
    
