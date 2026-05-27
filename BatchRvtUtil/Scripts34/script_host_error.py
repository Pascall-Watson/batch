#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fix: `except Exception, e:` → `as e:`.
#

import clr
import System
from System import AppDomain
from System.Text import StringBuilder
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import MessageBox

import winforms_util
import exception_util

# Must match BATCH_RVT_ERROR_WINDOW_TITLE in ScriptHostUtil.cs (BatchRvtScriptHost project).
BATCH_RVT_ERROR_WINDOW_TITLE = "BatchRvt Script Error"

SCRIPT_HOST_ERROR_DATA_VARIABLE = "revit_script_host"


def SetDataInCurrentDomain(name, data):
    AppDomain.CurrentDomain.SetData(name, data)


def ShowScriptErrorMessageBox(errorMessage):
    mainWindowHandle = winforms_util.WindowHandleWrapper.GetMainWindowHandle()
    MessageBox.Show(mainWindowHandle, errorMessage, BATCH_RVT_ERROR_WINDOW_TITLE)


def WithErrorHandling(action, errorMessage, output=None, showErrorMessageBox=False):
    try:
        return action()
    except Exception as e:
        if output is not None:
            output()
            output(errorMessage)
            exception_util.LogOutputErrorDetails(e, output)

        if showErrorMessageBox:
            fullErrorMessage = StringBuilder()
            fullErrorMessage.AppendLine(errorMessage)
            fullErrorMessage.AppendLine()
            fullErrorMessage.AppendLine(exception_util.GetExceptionDetails(e))
            ShowScriptErrorMessageBox(fullErrorMessage.ToString())

        SetDataInCurrentDomain(SCRIPT_HOST_ERROR_DATA_VARIABLE, e)
    return None
