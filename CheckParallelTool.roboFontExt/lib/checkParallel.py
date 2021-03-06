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

from comCheckParallelUtils.drawingDelegate import DrawingDelegate
from comCheckParallelUtils.guideStatusView import GuideStatusView
from comCheckParallelUtils.toleranceWindow import ToleranceWindow
import comCheckParallelUtils.helperFuncs as hf

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

        self.glyph.prepareUndo("Move handles")

        # Get positions of mouse & bcps and do some math
        self.mouseDownPoint = (round(point.x), round(point.y))

        # Select segment when BCP connection is clicked first,
        # and then analyze selection for the dictionary
        # otherwise, everything will be deselected when user clicks
        # outside of the contours (eg. on the BCP connection)
        # and we will have no selections to analyze.
        self._selectSegmentWhenBCPConnectionIsClicked()
        self.delegate._analyzeSelection(self.glyph)

        # Only calculate slopes & intercepts when 1 segment is selected
        if len(self.delegate._selectedSegments) != 1:
            return

        for selected in self.delegate._selectedSegments:
            pt1, segment = selected
            self.h1, self.h2, pt2 = segment

            self.h1Pos = self.h1.position
            self.h2Pos = self.h2.position

            self.slope0, self.intercept0 = hf.getSlopeAndIntercept(pt1.position, self.h1Pos)
            self.slope1, self.intercept1 = hf.getSlopeAndIntercept(pt2.position, self.h2Pos)

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
        # Only manipulate BCPs if one segment is selected
        # and if user clicks on connection line
        # (canMarquee is True if user clicks outside of connetion line)
        if len(self.delegate._selectedSegments) != 1 or\
        self.canMarquee:
            return

        bcp0X, bcp0Y = self.h1Pos
        bcp1X, bcp1y = self.h2Pos

        # New point = current point + delta (for now)
        bcp0XtoUse = bcp0X + delta.x
        bcp0YtoUse = bcp0Y + delta.y
        bcp1XtoUse = bcp1X + delta.x
        bcp1YtoUse = bcp1y + delta.y

        # First BCP
        # Horizontal line, so new y == old y
        if self.slope0 == 0:
            bcp0YtoUse = bcp0Y

        # Vertical line, so new x == old x
        elif self.slope0 is None:
            bcp0XtoUse = bcp0X

        # Angled line, use y=mx+b to find out new x & y,
        # using x, y calculated above... this seems weird.
        else:
            bcp0XtoUse = (bcp0YtoUse - self.intercept0) / self.slope0
            bcp0YtoUse = self.slope0 * bcp0XtoUse + self.intercept0

        # Second BCP, same as above
        if self.slope1 == 0:
            bcp1YtoUse = bcp1y
        elif self.slope1 is None:
            bcp1XtoUse = bcp1X
        else:
            bcp1XtoUse = (bcp1YtoUse - self.intercept1) / self.slope1
            bcp1YtoUse = self.slope1 * bcp1XtoUse + self.intercept1

        self.h1.position = (round(bcp0XtoUse), round(bcp0YtoUse))
        self.h2.position = (round(bcp1XtoUse), round(bcp1YtoUse))

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
        for selected in self.delegate._selectedSegments:
            p1, segment = selected
            h1, h2, p2 = segment
            if hf.isPointInLine(self.mouseDownPoint, (h1, h2), self.delegate.scale):
                self.canMarquee = False
                self.lineWeightMultiplier = 4
                segment.selected = True


if __name__ == "__main__":
    dwgDelegate = DrawingDelegate()
    parallelGuides = ParallelGuides(dwgDelegate)
    parallelTool = EditConnectionLineTool(dwgDelegate)

    installTool(parallelTool)
