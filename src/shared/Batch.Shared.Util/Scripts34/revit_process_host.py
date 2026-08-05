#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fix: `except Exception, e:` → `as e:`.
#

import clr
import System
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

try:
    clr.AddReference("System.Diagnostics.Process")
except:
    pass

import revit_process
import script_environment
import time_util


PROCESS_UNIQUE_ID_DELIMITER = "|"


def GetUniqueIdForProcess(process):
    return str.Join(
        PROCESS_UNIQUE_ID_DELIMITER,
        process.Id.ToString(),
        time_util.GetISO8601FormattedUtcDate(process.StartTime),
    )


def IsBatchRvtProcessRunning(batchRvtProcessUniqueId):
    def IsBatchRvtProcess(process):
        try:
            return GetUniqueIdForProcess(process) == batchRvtProcessUniqueId
        except Exception:
            return False
    return System.Diagnostics.Process.GetProcesses().FirstOrDefault(IsBatchRvtProcess) is not None


def StartHostRevitProcess(
    revitVersion,
    batchRvtScriptsFolderPath,
    scriptFilePath,
    scriptDataFilePath,
    progressNumber,
    scriptOutputPipeHandleString,
    testModeFolderPath,
):
    batchRvtProcessUniqueId = GetUniqueIdForProcess(System.Diagnostics.Process.GetCurrentProcess())

    def initEnvironmentVariables(environmentVariables):
        script_environment.InitEnvironmentVariables(
            environmentVariables,
            batchRvtScriptsFolderPath,
            scriptFilePath,
            scriptDataFilePath,
            progressNumber,
            scriptOutputPipeHandleString,
            batchRvtProcessUniqueId,
            testModeFolderPath,
        )

    return revit_process.StartRevitProcess(revitVersion, initEnvironmentVariables)
