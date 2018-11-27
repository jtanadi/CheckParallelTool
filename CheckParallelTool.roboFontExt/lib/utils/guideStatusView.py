from vanilla import Group, TextBox

class GuideStatusView:
    """
    A view object with text that shows
    whether parallel guides are on or not
    """
    def __init__(self):
        self.view = Group((0, 0, -0, -0))
        self.view.statusText = TextBox((-120, -30, 100, 22),
                                       text="⚪️ Parallel Guides",
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
        self.view.statusText.set("🔵 Parallel Guides")

    def turnStatusTextOff(self):
        """
        Turn view off
        """
        self.view.statusText.set("⚪️ Parallel Guides")


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
