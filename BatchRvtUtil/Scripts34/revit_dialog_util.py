#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes:
#   - `except Exception, e:` → `as e:`
#   - `e.message` (Py2-only) → `str(e)` since Py3 exceptions lack `.message`.
#

import clr
import System

from System import EventHandler
from System.Text import StringBuilder

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI.Events import DialogBoxShowingEventArgs, TaskDialogShowingEventArgs, MessageBoxShowingEventArgs

import exception_util

IDOK = 1
IDCANCEL = 2
IDYES = 6
IDNO = 7
IDCLOSE = 8


def Try(action):
    try:
        return action()
    except:
        return None


def DialogShowingEventHandler(sender, eventArgs, output):
    try:
        dialogResult = IDOK
        msg = StringBuilder()
        msg.AppendLine()
        msg.AppendLine("Dialog box shown:")
        msg.AppendLine()
        if isinstance(eventArgs, TaskDialogShowingEventArgs):
            msg.AppendLine("\tMessage: " + str(eventArgs.Message))
            if eventArgs.DialogId == "TaskDialog_Missing_Third_Party_Updater":
                dialogResult = 1001  # Continue working with the file.
            elif eventArgs.DialogId == "TaskDialog_Location_Position_Changed":
                dialogResult = 1002  # Do not save.
        elif isinstance(eventArgs, MessageBoxShowingEventArgs):
            msg.AppendLine("\tMessage: " + str(eventArgs.Message))
            msg.AppendLine("\tDialogType: " + str(eventArgs.DialogType))
        dialogId = Try(lambda: eventArgs.DialogId)  # Available on DialogBoxShowingEventArgs in Revit 2017+.
        if dialogId is not None:
            msg.AppendLine("\tDialogId: " + str(dialogId))
        helpId = Try(lambda: eventArgs.HelpId)  # No longer available in Revit 2018+.
        if helpId is not None:
            msg.AppendLine("\tHelpId: " + str(helpId))
        output(msg.ToString())
        eventArgs.OverrideResult(dialogResult)
    except Exception as e:
        errorMsg = StringBuilder()
        errorMsg.AppendLine()
        errorMsg.AppendLine("Caught exception in dialog event handler!")
        errorMsg.AppendLine("Exception message: " + str(e))
        output(errorMsg.ToString())
        exception_util.LogOutputErrorDetails(e, output)
    return


def WithDialogBoxShowingHandler(uiapp, action, output):
    result = None
    dialogShowingEventHandler = EventHandler[DialogBoxShowingEventArgs](
        lambda sender, eventArgs: DialogShowingEventHandler(sender, eventArgs, output)
    )
    uiapp.DialogBoxShowing += dialogShowingEventHandler
    try:
        result = action()
    finally:
        uiapp.DialogBoxShowing -= dialogShowingEventHandler
    return result
