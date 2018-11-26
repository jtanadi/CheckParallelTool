from vanilla import TextBox
from mojo.canvas import CanvasGroup

class GuideStatusDisplay:
    """
    Helper object to show whether
    the parallel guides are on or not
    """
    def __init__(self):
        self.view = CanvasGroup((0, 0, -0, -0), delegate=self)
        self.view.statusText = TextBox((-120, -30, 100, 22),
                                       text="Parallel guide on",
                                       alignment="right",
                                       sizeStyle="mini")

    def addViewToWindow(self, window):
        window.addGlyphEditorSubview(self.view)

    def turnStatusTextOn(self):
        if not self.view:
            return
        self.view.show(True)

    def turnStatusTextOff(self):
        if not self.view:
            return
        self.view.show(False)

    def shouldDrawBackground(self):
        return False

    def acceptsFirstResponder(self):
        return False
