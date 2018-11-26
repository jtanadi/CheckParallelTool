"""
A simple extension to help with drawing better curves.
The extension adds a guide and installs a tool.

Guides are toggled by pressing the "/" key and can be used
with any tool (EditingTool, ScalingEditTool, etc.)

Lines connecting BCPs can be directly edited with the
Edit Parallel Tool.

Inspired by the What I learned from Rod Cavazos section of
OHno Type Co's "Drawing Vectors for Type & Lettering":
https://ohnotype.co/blog/drawing-vectors
"""
import os.path

from AppKit import NSImage
import mojo.drawingTools as dt
from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView

from utils.toleranceWindow import ToleranceWindow
from utils.guideStatusView import GuideStatusView
import utils.helperFuncs as hf

# "/" key to turn guide on and off
KEYCODE = 44

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "resources", "toleranceSetting.txt")

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


class ParallelGuides:
    """
    Show parallel guides outside of the EditParallelTool
    This class adds observers that last an entire RF session
    """
    def __init__(self, delegate):
        self.delegate = delegate
        self.guideStatus = GuideStatusView()

        self.displayGuides = False

        addObserver(self, "keyDownCB", "keyDown")
        addObserver(self, "glyphWindowOpenCB", "glyphWindowDidOpen")

    def glyphWindowOpenCB(self, info):
        """
        Add guideStatus view to current glyph window
        """
        glyphWindow = info["window"]
        self.guideStatus.addViewToWindow(glyphWindow)

    def keyDownCB(self, info):
        """
        When user presses "/" with CheckParallelTool() inactive,
        toggle between drawing guides or not.

        Also set the guide status at the bottom right of the
        glyph window.
        """
        keyCode = info["event"].keyCode()
        if keyCode != KEYCODE:
            return

        self.displayGuides = not self.displayGuides

        if self.displayGuides:
            self.guideStatus.turnStatusTextOn()
            addObserver(self, "drawCB", "draw")
        else:
            self.guideStatus.turnStatusTextOff()
            removeObserver(self, "draw")

        UpdateCurrentGlyphView()

    def drawCB(self, info):
        """
        Pass on to delegate method
        """
        self.delegate.draw(info)


class EditParallelTool(EditingTool):
    """
    Tool to edit line connecting BCPs.
    Works kind of like Tunni tools.
    """
    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate
        self.toleranceWindow = ToleranceWindow()

        self.glyph = None

        # Use a dict so we can keep track of
        # what each selectedSegment belongs to
        self.lineWeightMultiplier = 1
        self.mouseDownPoint = None

        self.canMarquee = True

    def getToolbarIcon(self):
        """
        Get icon PDF and return to tool
        """
        iconFileDir = os.path.join(currentDir, "..", "resources", "checkParallelIcon.pdf")
        toolbarIcon = NSImage.alloc().initWithContentsOfFile_(iconFileDir)
        return toolbarIcon

    def getToolbarTip(self):
        """
        Return text that shows up on tool hover
        """
        return "Check Parallel Tool"

    def setup(self):
        """
        Set up some defaults and watch for
        event posted by ToleranceWindow()
        """
        self.glyph = CurrentGlyph()
        addObserver(self, "_applyTolerance", "com.ToleranceSettingChanged")

    def becomeInactive(self):
        """
        Tool becomes inactive
        """
        self.toolIsActive = False
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
        # Get positions of mouse & bcps and do some math
        self.mouseDownPoint = point

        # Select segment when BCP connection is clicked first,
        # and then analyze selection for the dictionary
        # otherwise, everything will be deselected when user clicks
        # outside of the contours (eg. on the BCP connection)
        # and we will have no selections to analyze.
        self._selectSegmentWhenBCPConnectionIsClicked()
        self.delegate.analyzeAndGetPoints()

        if not self.delegate.ptsFromSelectedCtrs:
            return

        # Not all pts are necessary, but here for consistency
        for cluster in self.delegate.ptsFromSelectedCtrs:
            self.pt0, self.pt1, self.pt2, self.pt3 = cluster[0], cluster[1],\
                                                     cluster[2], cluster[3]

        self.pt0Pos, self.pt1Pos = self.pt0.position, self.pt1.position
        self.pt2Pos, self.pt3Pos = self.pt2.position, self.pt3.position

        self.slope0, self.intercept0 = hf.getSlopeAndIntercept(self.pt0Pos,
                                                               self.pt2Pos)
        self.slope1, self.intercept1 = hf.getSlopeAndIntercept(self.pt1Pos,
                                                               self.pt3Pos)

    def mouseUp(self, point):
        """
        Reset some values
        """
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
        if len(self.delegate.ptsFromSelectedCtrs) != 1:
            return
        if self.mouseDownPoint is None:
            return

        selectedPt2X, selectedPt2Y = self.pt2Pos
        selectedPt3X, selectedPt3Y = self.pt3Pos

        # Differences b/w mousedown point and bcp points
        pt2DiffX = self.mouseDownPoint.x - selectedPt2X
        pt2DiffY = self.mouseDownPoint.y - selectedPt2Y
        pt3DiffX = self.mouseDownPoint.x - selectedPt3X
        pt3DiffY = self.mouseDownPoint.y - selectedPt3Y

        # Calculate now, but some will be overidden below
        pt2XtoUse = point.x - pt2DiffX
        pt2YtoUse = point.y - pt2DiffY
        pt3XtoUse = point.x - pt3DiffX
        pt3YtoUse = point.y - pt3DiffY

        # First BCP
        # X = difference b/w mouse X and point's X
        # Y =  point's current Y (horizontal line)
        if self.slope0 == 0:
            pt2YtoUse = selectedPt2Y

        # X = point's current X (vertical line)
        # Y = difference b/w mouse Y and point's Y
        elif self.slope0 is None:
            pt2XtoUse = selectedPt2X

        # X = calculated from diff b/w mouse Y and point's Y (slope b/w horizontal and 45deg)
        # Y = calculated from diff b/w mouse X and point's X (slope b/w and 45deg and vert)
        else:
            pt2XtoUse = (pt2YtoUse - self.intercept0) / self.slope0
            pt2YtoUse = self.slope0 * pt2XtoUse + self.intercept0

        # Second BCP, same as above
        if self.slope1 == 0:
            pt3YtoUse = selectedPt3Y
        elif self.slope1 is None:
            pt3XtoUse = selectedPt3X
        else:
            pt3XtoUse = (pt3YtoUse - self.intercept1) / self.slope1
            pt3YtoUse = self.slope1 * pt3XtoUse + self.intercept1

        self.pt2.position = (round(pt2XtoUse), round(pt2YtoUse))
        self.pt3.position = (round(pt3XtoUse), round(pt3YtoUse))

        self.glyph.changed()

    def getMarqueRect(self, offset=None, previousRect=False):
        """
        Return no marquee rectangle when user
        clicks and drags on the line connecting BCPs
        """
        if not self.canMarquee:
            return None
        return super().getMarqueRect(offset, previousRect)

    def dragSelection(self, point, delta):
        """
        Don't drag selection when user clicks
        and drags on the line connecting BCPs
        """
        if not self.canMarquee:
            return
        super().dragSelection(point, delta)       

    def draw(self, scale):
        """
        Pass drawing to delegate object's method
        """
        self.delegate.draw(scale, self.glyph, self.lineWeightMultiplier)

    def _applyTolerance(self, info):
        """
        Pass to delegate object's method:
        Redefine tolerance whenever com.ToleranceSettingChanged is triggered
        """
        self.delegate.readToleranceSetting()

    def _selectSegmentWhenBCPConnectionIsClicked(self):
        """
        Keep segment selected when click point is w/in
        line connecting bcps

        If multiple segments are selected, only one
        segment will remain selected
        """
        for selectedSegments in self.delegate.selectedContours.values():
            for segment in selectedSegments:
                offCurves = [point for point in segment if point.type == "offcurve"]
                pt0Pos = offCurves[0].position
                pt1Pos = offCurves[1].position

                if not hf.isPointInLine(self.mouseDownPoint, (pt0Pos, pt1Pos)):
                    continue

                self.canMarquee = False
                self.lineWeightMultiplier = 4
                segment.selected = True


dwgDelegate = DrawingDelegate()
parallelGuides = ParallelGuides(dwgDelegate)
parallelTool = EditParallelTool(dwgDelegate)

installTool(parallelTool)
