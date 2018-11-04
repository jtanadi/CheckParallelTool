"""
Use this window to set tolerance level.
Read and write to resources/toleranceSetting.txt for persistance.

When a level has been set, save value and post event.
The CheckParallel tool has an observer
to notify it to read the setting whenever it changes.
"""

import helperFuncs as hf
from vanilla import FloatingWindow, Slider, Button, TextBox
from mojo.events import postEvent
from defconAppKit.windows.baseWindow import BaseWindowController
import os.path

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "resources", "toleranceSetting.txt")

class ToleranceWindow(BaseWindowController):
    def __init__(self):
        """
        Use "accuracy" in UI because it's easier to understand,
        but convert to "tolerance" because it's easier to use
        in parallel slope math later.
        """
        self.maxValue = 0.05
        self.w = FloatingWindow((150, 60), "Set Accuracy")
        self.w.accuracySlider = Slider((10, 9, -10, 23),
                                        minValue=0,
                                        maxValue=self.maxValue,
                                        value=hf.readSetting(settingDir),
                                        sizeStyle="small",
                                        callback=self.accuracySliderCB)
        self.w.lessText = TextBox((10, 30, -10, 12),
                                  text="Less",
                                  sizeStyle="small")
        self.w.moreText = TextBox((10, 30, -10, 12),
                                  text="More",
                                  alignment="right",
                                  sizeStyle="small")
        self.setUpBaseWindowBehavior()
        # Post this event so CheckParallel() can't open 2 ToleranceWindow()
        postEvent("comToleranceWindowOpened")
        self.w.open()

    def accuracySliderCB(self, sender):
        """
        When slider changes, write setting and post event.
        Reverse slider value by subtracting from maxValue
        because we're tracking tolerance
        """
        toleranceValue = abs(round(self.maxValue - sender.get(), 3))
        print(toleranceValue)
        self.writeSetting(toleranceValue)
        postEvent("comToleranceSettingChanged")

    def writeSetting(self, value):
        """
        Write setting to file or make new file if
        setting file doesn't exist.
        """
        settingFile = open(settingDir, "w+")
        settingFile.write(str(value))
        settingFile.close()

    def windowCloseCallback(self, sender):
        """
        Let CheckParallel() know that ToleranceWindow() has been closed,
        so CP() will let user open a TW() again.
        """
        postEvent("comToleranceWindowClosed")
        super(ToleranceWindow, self).windowCloseCallback(sender)

if __name__ == "__main__":
    ToleranceWindow()
