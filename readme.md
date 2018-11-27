# Check Parallel Tool
A tool to check if the line connecting BCPs & oncurves are parallel, as well as edit BCPs by manipulating connection lines.

The extension draws guidelines and installs its own editing tool.

![animated demo](https://github.com/jtanadi/CheckParallelTool/blob/master/z-misc/demo4_181127.gif "animated demo")

## How to use
Guides are toggled on/off by pressing the "/" key and can be used with any tool (EditingTool, ScalingEditTool, etc.). Guide visibility is shown at the bottom right corner of the glyph window.
![guides demo](https://github.com/jtanadi/CheckParallelTool/blob/master/z-misc/demo5_181127.gif "animated demo")

Similar to other Tunni tools, the Edit Connection Line Tool allows users to edit BCPs by manipulating the line between them.
![guides demo](https://github.com/jtanadi/CheckParallelTool/blob/master/z-misc/demo7_181127.gif "animated demo")

With the tool on, double-click on the canvas to set tool accuracy. This tool reads and writes a text file for data persistence.
![menu demo](https://github.com/jtanadi/CheckParallelTool/blob/master/z-misc/demo2_181104.gif "menu demo")

## 📣
Inspired by the **What I learned from Rod Cavazos** section of OHno Type Co's ["Drawing Vectors for Type & Lettering"](https://ohnotype.co/blog/drawing-vectors).

H/t to [Stephen Nixon](http://stephennixon.com/) for the "guides-only" idea. 
As always, thanks to [Frederik Berlaen](http://typemytype.com/) and [Gustavo Ferreira](http://www.gustavoferreira.com/) for all the Robohelp!

### To do / other ideas
- Some sort of gradated color scheme, so it's less "right" vs. "wrong"
- Compare multiple segments (ie. see if parallel segments are really parallel)