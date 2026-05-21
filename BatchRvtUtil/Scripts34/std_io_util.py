#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System
import sys

import logging_util
import time_util

SHOW_OUTPUT = True

ORIGINAL_STDOUT = sys.stdout
ORIGINAL_STDERR = sys.stderr


def RedirectScriptOutput(output):
    sys.stdout.flush()
    sys.stderr.flush()
    sys.stdout = output
    sys.stderr = output
    return


def RestoreScriptOutput():
    sys.stderr.flush()
    sys.stdout.flush()
    sys.stderr = ORIGINAL_STDOUT
    sys.stdout = ORIGINAL_STDERR
    return


def Output(m="", msgId=""):
    timestamp = time_util.GetDateTimeNow().ToString("HH:mm:ss")
    message = ""
    for line in m.split("\n"):
        message += timestamp + " : " + (("[" + str(msgId) + "]" + " ") if msgId != "" else "") + line + "\n"
    if SHOW_OUTPUT:
        ORIGINAL_STDOUT.write(message)
    if logging_util.LOG_FILE[0] is not None:
        logging_util.LOG_FILE[0].WriteMessage({"msgId": msgId, "message": m})
    return
