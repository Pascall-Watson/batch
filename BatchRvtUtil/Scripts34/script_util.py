#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Substantive fix vs 2.7:
#   - `execfile(scriptFilePath, scriptGlobals)` (removed in Py3) → read file +
#     `compile()` + `exec()`. Source file path is preserved in the compiled
#     code object so tracebacks still point at the user's script.
#

import clr
import System
from System.IO import Path

import std_io_util
from std_io_util import Output
import path_util
from path_util import GetProjectFolderNameFromRevitProjectFilePath  # Might come in handy for pre/post-processing scripts.

PYTHON_SCRIPT_FILE_EXTENSION = ".py"
DYNAMO_SCRIPT_FILE_EXTENSION = ".dyn"

SESSION_ID_CONTAINER = [None]
TASK_DATA_CONTAINER = [None]
EXPORT_FOLDER_PATH_CONTAINER = [None]
SESSION_DATA_FOLDER_PATH_CONTAINER = [None]
REVIT_FILE_LIST_FILE_PATH_CONTAINER = [None]


def SetSessionId(batchRvtConfig):
    SESSION_ID_CONTAINER[0] = batchRvtConfig.SessionId


def SetTaskData(batchRvtConfig):
    TASK_DATA_CONTAINER[0] = batchRvtConfig.TaskData


def SetExportFolderPath(batchRvtConfig):
    EXPORT_FOLDER_PATH_CONTAINER[0] = batchRvtConfig.DataExportFolderPath


def SetSessionDataFolderPath(batchRvtConfig):
    SESSION_DATA_FOLDER_PATH_CONTAINER[0] = batchRvtConfig.SessionDataFolderPath


def SetRevitFileListFilePath(batchRvtConfig):
    REVIT_FILE_LIST_FILE_PATH_CONTAINER[0] = batchRvtConfig.RevitFileListFilePath


def GetSessionId():
    return SESSION_ID_CONTAINER[0]


def GetTaskData():
    return TASK_DATA_CONTAINER[0]


def GetExportFolderPath():
    return EXPORT_FOLDER_PATH_CONTAINER[0]


def GetSessionDataFolderPath():
    return SESSION_DATA_FOLDER_PATH_CONTAINER[0]


def GetRevitFileListFilePath():
    return REVIT_FILE_LIST_FILE_PATH_CONTAINER[0]


def ExecuteScript(scriptFilePath):
    path_util.AddSearchPath(Path.GetDirectoryName(scriptFilePath))
    with open(scriptFilePath, "r", encoding="utf-8") as f:
        source = f.read()
    scriptGlobals = {"__name__": "__main__", "__file__": scriptFilePath}
    exec(compile(source, scriptFilePath, "exec"), scriptGlobals)
