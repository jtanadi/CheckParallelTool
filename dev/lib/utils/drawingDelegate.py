"""
Delegate object for drawing
"""

import os.path
import mojo.drawingTools as dt
import utils.helperFuncs as hf

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "..", "resources", "toleranceSetting.txt")

class DrawingDelegate:
    """
    A delegate object used by both ParallelGuides()
    and EditParallelTool() to analyze segments and draw lines
    """
    def __init__(self):
        self.tolerance = hf.readSetting(settingDir)
        self.selectedContours = {}
        self.ptsFromSelectedCtrs = []

    def analyzeAndGetPoints(self, glyph=None):
        """
        Analyze selection and get points
        This method just calls 2 protected methods for easy access
        """
        if glyph is None:
            return

        self._analyzeSelection(glyph)
        self._getPointsFromSelectedContours(glyph)

    def draw(self, infoOrScale, glyph=None, lineWeightMultiplier=1):
        """
        Draw lines.

        This method is called by both the observer watching
        "draw" (turned on when "/" is pressed) and by the tool,
        when it's active.

        When used by the observer, it returns "info", a dict
        from which we need to grab scale. When used by the tool,
        it returns scale, so we can use it right away.
        """
        # This is just for naming...
        scale = infoOrScale
        if isinstance(infoOrScale, dict) and glyph is None:
            scale = infoOrScale["scale"]
            glyph = infoOrScale["glyph"]

        # Just in case...
        if glyph is None:
            return

        # Also do this here in case mouseDown isn't fired
        # (eg. user uses keyboard to select segments)
        self.analyzeAndGetPoints(glyph)

        # Only draw if something has been selected
        if not self.ptsFromSelectedCtrs:
            return

        for cluster in self.ptsFromSelectedCtrs:
            # Don't draw if there are overlapping points
            # The set comprehension will remove duplicate points
            # (ie. tuple & set won't have same lengths)
            clusterPosSet = {point.position for point in cluster}
            if len(cluster) != len(clusterPosSet):
                continue

            pt0, pt1, pt2, pt3 = cluster[0].position, cluster[1].position,\
                                 cluster[2].position, cluster[3].position

            # Parallel-ish lines are green; otherwise, red
            if hf.areTheyParallel((pt0, pt1), (pt2, pt3), self.tolerance):
                dt.stroke(0, 1, 0, 1)
            else:
                dt.stroke(1, 0, 0, 1)

            dt.strokeWidth(scale)
            dt.line(pt0, pt1)

            dt.strokeWidth(scale * lineWeightMultiplier)
            dt.line(pt2, pt3)

    def readToleranceSetting(self):
        """
        Read tolerance setting from file
        """
        self.tolerance = hf.readSetting(settingDir)

    def _analyzeSelection(self, glyph):
        """
        Look at what's selected and add appropriate segment(s)
        to the self.selectedContours dict.

        We don't explicitly check if a segment is a curve because
        we don't draw segments without offcurves in draw() anyway.
        """
        self.selectedContours.clear()

        # Find which segments in each contour are selected
        for contour in glyph:
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

    def _getPointsFromSelectedContours(self, glyph):
        """
        Append all selected points (oncurves & bcps)
        as a list of tuples of tuples in self.ptsFromSelectedCtrs
        [
            ((x0, y0), (x1, y1), (x2, y2), (x3, y3)),
            ((x4, y4), (x5, y5), (x6, y6), (x7, y7)),
            ...
        ]

        **Actual points are appended, not positions**
        """
        self.ptsFromSelectedCtrs.clear()

        for index, selectedSegments in self.selectedContours.items():
            currentContour = glyph[index]
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

                self.ptsFromSelectedCtrs.append((pt0, pt1, pt2, pt3))

