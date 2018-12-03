"""
Use this window to set tolerance level.
Read and write to resources/toleranceSetting.txt for persistance.

When a level has been set, save value and post event.
The CheckParallel tool has an observer
to notify it to read the setting whenever it changes.
"""

import utils.helperFuncs as hf
from mojo.UI import ShowHideWindow
from vanilla import FloatingWindow, Slider, Button, TextBox
from mojo.events import postEvent
import os.path

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "..", "resources", "toleranceSetting.txt")

class ToleranceWindow:
    def __init__(self):
        """
        Use "accuracy" in UI because it's easier to understand,
        but convert to "tolerance" because it's easier to use
        in parallel slope math later.
        """
        self.maxValue = 5
        self.w = ShowHideWindow((150, 60), "Set Accuracy")
        self.w.accuracySlider = Slider((10, 9, -10, 23),
                                       minValue=0,
                                       maxValue=self.maxValue,
                                       value=self.maxValue - hf.readSetting(settingDir),
                                       sizeStyle="small",
                                       callback=self.accuracySliderCB)
        self.w.lessText = TextBox((10, 30, -10, 12),
                                  text="Less",
                                  sizeStyle="small")
        self.w.moreText = TextBox((10, 30, -10, 12),
                                  text="More",
                                  alignment="right",
                                  sizeStyle="small")

        self.w.center()
        self.w.makeKey()

    def accuracySliderCB(self, sender):
        """
        When slider changes, write setting and post event.
        Reverse slider value by subtracting from maxValue
        because we're tracking tolerance
        """
        toleranceValue = round(self.maxValue - sender.get(), 2)
        hf.writeSetting(settingDir, toleranceValue)
        postEvent("com.ToleranceSettingChanged")


if __name__ == "__main__":
    toleranceWindow = ToleranceWindow()
    toleranceWindow.w.open()
