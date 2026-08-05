#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

import test_mode_util

GLOBAL_TEST_MODE = [None]


def GetGlobalTestMode():
    return GLOBAL_TEST_MODE[0]


def IsGlobalTestMode():
    return GetGlobalTestMode() is not None


def InitializeGlobalTestMode(testModeFolderPath):
    if IsGlobalTestMode():
        raise Exception("ERROR: Global test mode is already initialized!")
    if not str.IsNullOrWhiteSpace(testModeFolderPath):
        globalTestMode = test_mode_util.TestMode(testModeFolderPath)
        globalTestMode.CreateTestModeFolder()
        GLOBAL_TEST_MODE[0] = globalTestMode
    return


def ExportSessionId(sessionId):
    if IsGlobalTestMode():
        GetGlobalTestMode().ExportSessionId(sessionId)
    return


def ExportRevitProcessId(revitProcessId):
    if IsGlobalTestMode():
        GetGlobalTestMode().ExportRevitProcessId(revitProcessId)
    return


def PrefixedOutputForGlobalTestMode(output_, prefixForTestMode):
    if IsGlobalTestMode():
        def output(m=""):
            output_(prefixForTestMode + " " + m)
        return output
    return output_
