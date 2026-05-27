#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fix: `except Exception, e:` → `as e:`.
#

import clr
import System
from System.IO import Path, File

import batch_rvt_util
from batch_rvt_util import LogFile

LOG_FILE = [None]  # List so it can be captured by reference in closures.


def InitializeLogging(logName, logFolderPath):
    LOG_FILE[0] = LogFile(logName, logFolderPath, False)
    return


def GetLogFilePath():
    logFile = LOG_FILE[0]
    return logFile.GetLogFilePath() if logFile is not None else str.Empty


def DumpPlainTextLogFile():
    plainTextLogFilePath = None
    logFilePath = GetLogFilePath()
    if not str.IsNullOrWhiteSpace(logFilePath):
        plainTextLogFilePath = Path.Combine(
            Path.GetDirectoryName(logFilePath),
            Path.GetFileNameWithoutExtension(logFilePath) + ".txt",
        )
        try:
            File.WriteAllLines(
                plainTextLogFilePath,
                LogFile.ReadLinesAsPlainText(logFilePath),
            )
        except Exception:
            plainTextLogFilePath = None
    return plainTextLogFilePath
