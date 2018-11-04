"""
Use this window to set tolerance level.
Read and write to resources/toleranceSetting.txt for persistance.

When a level has been set, save value and post event.
The CheckParallel tool has an observer
to notify it to read the setting whenever it changes.
"""

import helperFuncs as hf
from vanilla import FloatingWindow, Slider, Button
from mojo.events import postEvent
from defconAppKit.windows.baseWindow import BaseWindowController
import os.path

currentDir = os.path.dirname(__file__)
settingDir = os.path.join(currentDir, "..", "resources", "toleranceSetting.txt")

class ToleranceWindow(BaseWindowController):
    def __init__(self):
        self.w = FloatingWindow((150, 45),
                                "Set tolerance")
        self.w.toleranceSlider = Slider((10, 10, -10, 23),
                                        minValue=0,
                                        maxValue=0.050,
                                        value=hf.readSetting(settingDir),
                                        sizeStyle="small",
                                        callback=self.toleranceSliderCB)
        self.setUpBaseWindowBehavior()
        postEvent("comToleranceWindowOpened")
        self.w.open()

    def toleranceSliderCB(self, sender):
        toleranceValue = round(sender.get(), 3)
        self.writeSetting(toleranceValue)
        postEvent("comToleranceSettingChanged")

    def writeSetting(self, value):
        settingFile = open(settingDir, "w")
        settingFile.write(str(value))
        settingFile.close()

    def windowCloseCallback(self, sender):
        postEvent("comToleranceWindowClosed")
        super(ToleranceWindow, self).windowCloseCallback(sender)

if __name__ == "__main__":
    ToleranceWindow()
