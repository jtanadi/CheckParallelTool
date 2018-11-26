from vanilla import TextBox
from mojo.canvas import CanvasGroup

class GuideStatusView:
    """
    A view object with text that shows
    whether parallel guides are on or not
    """
    def __init__(self):
        self.view = CanvasGroup((0, 0, -0, -0), delegate=self)
        self.view.statusText = TextBox((-120, -30, 100, 22),
                                       text="Parallel guide on",
                                       alignment="right",
                                       sizeStyle="mini")
    def addViewToWindow(self, glyphWindow):
        """
        Add this view to the glyph window passed in
        """
        glyphWindow.addGlyphEditorSubview(self.view)

    def turnStatusTextOn(self):
        """
        Turn view on
        """
        if not self.view:
            return
        self.view.show(True)

    def turnStatusTextOff(self):
        """
        Turn view off
        """
        if not self.view:
            return
        self.view.show(False)

    def shouldDrawBackground(self):
        """
        Don't draw CanvasGroup background
        """
        return False

    def acceptsFirstResponder(self):
        """
        Make CanvasGroup not interactable
        """
        return False


if __name__ == "__main__":
    #Test the view
    from vanilla import FloatingWindow
    from mojo.events import addObserver, removeObserver

    class TesterWindow:
        def __init__(self):
            self.w = FloatingWindow((100, 100), "Tester")
            self.w.bind("close", self.closeCB)

            self.guideView = None

            addObserver(self, "glyphWindowOpenCB", "glyphWindowDidOpen")

        def glyphWindowOpenCB(self, info):
            glyphWindow = info["window"]
            self.guideView = GuideStatusView()
            self.guideView.view.statusText.set("TEST")
            self.guideView.addViewToWindow(glyphWindow)
            self.guideView.turnStatusTextOn()

        def closeCB(self, sender):
            removeObserver(self, "glyphWindowDidOpen")

    testerWindow = TesterWindow()
    testerWindow.w.open()
