#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fix: `except IOException, e:` → `as e:`.
#

import clr
import System
from System.IO import IOException

import revit_dynamo_error


def IsDynamoRevitModuleLoaded():
    try:
        clr.AddReference("DynamoRevitDS")
        return True
    except IOException:
        return False


def ExecuteDynamoScript(uiapp, dynamoScriptFilePath, showUI=False):
    import revit_dynamo_util
    return revit_dynamo_util.ExecuteDynamoScript(uiapp, dynamoScriptFilePath, showUI)
