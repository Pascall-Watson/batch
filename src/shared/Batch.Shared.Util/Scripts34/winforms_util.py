#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

try:
    clr.AddReference("System.Diagnostics.Process")
except:
    pass

clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import MessageBox, IWin32Window, Cursor

clr.AddReference("System.Drawing")
from System.Drawing import Point


class WindowHandleWrapper(IWin32Window):
    def __init__(self, hwnd):
        self.hwnd = hwnd

    def get_Handle(self):
        return self.hwnd

    @staticmethod
    def GetMainWindowHandle():
        return WindowHandleWrapper(System.Diagnostics.Process.GetCurrentProcess().MainWindowHandle)


def SetMousePosition(x, y):
    Cursor.Position = Point(x, y)
    return
