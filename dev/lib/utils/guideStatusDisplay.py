from vanilla import TextBox

class GuideStatusDisplay:
    """
    Helper object to show whether
    the parallel guides are on or not
    """
    def __init__(self):
        self.statusText = TextBox((-120, -30, 100, 22),
                                  text="",
                                  alignment="right",
                                  sizeStyle="mini")

    def setStatusText(self, view, textToSet):
        """
        Set text in TextBox and set TextBox into frame
        """
        self.statusText.set(textToSet)
        superview = view.enclosingScrollView().superview()
        view = self.statusText.getNSTextField()
        frame = superview.frame()
        self.statusText._setFrame(frame)
        superview.addSubview_(view)
