"""
A simple extension to help with drawing better curves.
Use the extension to check if the line connecting BCPs and oncurves
are parallel, as well as edit BCPs by manipulating connection lines.

The extension adds observers to draw guides and installs a tool.

Guides are toggled by pressing the "/" key and can be used
with any tool (EditingTool, ScalingEditTool, etc.)

Lines connecting BCPs can be directly edited with the
Edit Parallel Tool (still WIP).

Inspired by the "What I learned from Rod Cavazos" section
of OHno Type Co's "Drawing Vectors for Type & Lettering":
https://ohnotype.co/blog/drawing-vectors
"""
import os.path

from AppKit import NSImage
from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView

from utils.drawingDelegate import DrawingDelegate
from utils.guideStatusView import GuideStatusView
from utils.toleranceWindow import ToleranceWindow
import utils.helperFuncs as hf

# "/" key to turn guide on and off
KEYCODE = 44

currentDir = os.path.dirname(__file__)

class ParallelGuides:
    """
    Show parallel guides outside of the EditConnectionLineTool
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


class EditConnectionLineTool(EditingTool):
    """
    Tool to edit line connecting BCPs
    Works kind of like Tunni tools, but still needs work
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
        return "Edit Connection Line Tool"

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
        self.delegate.analyzeAndGetPoints(self.glyph)

        print(self.delegate.ptsFromSelectedCtrs)
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

                # In case some segments don't have BCPs
                # (eg. spine of an S)
                if not offCurves:
                    continue

                pt0Pos = offCurves[0].position
                pt1Pos = offCurves[1].position

                if not hf.isPointInLine(self.mouseDownPoint, (pt0Pos, pt1Pos)):
                    continue

                self.canMarquee = False
                self.lineWeightMultiplier = 4
                segment.selected = True


if __name__ == "__main__":
    dwgDelegate = DrawingDelegate()
    parallelGuides = ParallelGuides(dwgDelegate)
    parallelTool = EditConnectionLineTool(dwgDelegate)

    installTool(parallelTool)
