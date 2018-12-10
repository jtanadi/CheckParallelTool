"""
Delegate object for drawing
"""

import os.path
import mojo.drawingTools as dt
import comCheckParallelUtils.helperFuncs as hf

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "..", "resources", "toleranceSetting.txt")

class DrawingDelegate:
    """
    A delegate object used by both ParallelGuides()
    and EditParallelTool() to analyze segments and draw lines
    """
    def __init__(self):
        self.tolerance = hf.readSetting(settingDir)
        self.scale = None
        self._selectedSegments = []

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
        self.scale = infoOrScale
        if isinstance(infoOrScale, dict) and glyph is None:
            self.scale = infoOrScale["scale"]
            glyph = infoOrScale["glyph"]

        # Just in case...
        if self.scale is None or glyph is None:
            return

        # Also do this here in case mouseDown isn't fired
        # (eg. user uses keyboard to select segments)
        self._analyzeSelection(glyph)

        for selected in self._selectedSegments:
            p1, segment = selected
            h1, h2, p2 = segment
            if hf.areTheyParallel((p1, p2,), (h1, h2), self.tolerance):
                dt.stroke(0, 0, 1, 1)
            else:
                dt.stroke(1, 0, 0, 1)
            dt.strokeWidth(self.scale)
            dt.line((p1.x, p1.y), (p2.x, p2.y))
            dt.strokeWidth(self.scale * lineWeightMultiplier)
            dt.line((h1.x, h1.y), (h2.x, h2.y))


    def readToleranceSetting(self):
        """
        Read tolerance setting from file
        """
        self.tolerance = hf.readSetting(settingDir)

    def _analyzeSelection(self, glyph):
        """
        Look at what's selected and add appropriate segment(s)
        to the self._selectedSegments list.

        self._selectedSegments is a list of tuples:
        [(prevPt, segment), (prevPt, segment), (prevPt, segment)]

        segment is an object that contains 2 bcps and an oncurve pt
        """
        # Find which segments in each contour are selected
        selection = []
        for contour in glyph:
            segments = contour.segments
            for i, segment in enumerate(segments):
                # Look for selected segments
                if segment.selected and segment.type in ["curve", "qcurve"]:
                    prevPt = segments[i - 1].onCurve
                    selection.append((prevPt, segment))

                # No selected segments, look for selected points
                else:
                    for point in segment:
                        prevPt = segments[i - 1].onCurve

                        # If bcp is selected, add current segment
                        if point.selected and point.type == "offcurve":
                            selection.append((prevPt, segment))

                        # If oncurve pt is selected, add current and NEXT segment
                        elif point.selected:
                            # If any point adjacent to current point is selected, then
                            # a segment has been selected, and it's been taken care of above
                            # This prevents 2 segments from being selected when user
                            # selects a segment.
                            if prevPt.selected or hf.findNextPt(point, contour).selected:
                                continue

                            if segment.type in ["curve", "qcurve"]:
                                selection.append((prevPt, segment))

                            try:
                                nextSegment = segments[i + 1]
                                if nextSegment.type in ["curve", "qcurve"]:
                                    selection.append((point, segments[i + 1]))
                            except IndexError:
                                nextSegment = segments[0]
                                if nextSegment.type in ["curve", "qcurve"]:
                                    selection.append((point, segments[0]))

        if selection != self._selectedSegments:
            self._selectedSegments = selection
