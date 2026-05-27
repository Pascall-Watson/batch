#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System
from System import Environment


def GetMachineName():
    return Environment.MachineName


def GetUserName():
    return Environment.UserName
