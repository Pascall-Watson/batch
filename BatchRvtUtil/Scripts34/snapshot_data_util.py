#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes: `except Exception, e:` → `as e:`.
#

import clr
import System
from System import Guid
from System.IO import Path, DirectoryInfo, File

import path_util
import revit_file_list
import text_file_util
import json_util
import exception_util

SNAPSHOT_FOLDER_NAME_FORMAT = "yyyyMMdd_HHmmss_fff"
PROJECT_BIM_FOLDER_NAME = "BIM"
PROJECT_FILES_FOLDER_NAME = "1.0 Project Files"

SNAPSHOT_DATA_FILENAME = "snapshot.json"
TEMP_SNAPSHOT_DATA_FILENAME = "temp_snapshot.json"
SNAPSHOT_DATA__REVIT_JOURNAL_FILE = "revitJournalFile"


def GetUnknownProjectUniqueFolderName():
    return Path.GetRandomFileName().Replace(".", str.Empty).ToUpper()


def GetSnapshotFolderName(timestamp):
    return timestamp.ToString(SNAPSHOT_FOLDER_NAME_FORMAT)


def GetRevitModelName(revitFilePath):
    return Path.GetFileNameWithoutExtension(revitFilePath)


def GetRevitFileVersionDetails(revitFilePath):
    revitFileInfo = revit_file_list.RevitFileInfo(revitFilePath)
    return revitFileInfo.TryGetRevitVersionText()


def GetSnapshotFolderPath(dataExportFolderPath, revitFilePath, isCloudModel, cloudProjectId, cloudModelId, timestamp):
    snapshotFolderName = GetSnapshotFolderName(timestamp.ToLocalTime())
    if isCloudModel:
        return Path.Combine(dataExportFolderPath, cloudProjectId, cloudModelId, snapshotFolderName)
    projectFolderName = path_util.GetProjectFolderNameFromRevitProjectFilePath(revitFilePath)
    if projectFolderName is None:
        projectFolderName = GetUnknownProjectUniqueFolderName()
    modelName = GetRevitModelName(revitFilePath)
    return Path.Combine(dataExportFolderPath, projectFolderName, modelName, snapshotFolderName)


def GetSnapshotDataFilePath(snapshotDataFolderPath):
    return Path.Combine(snapshotDataFolderPath, SNAPSHOT_DATA_FILENAME)


def GetTemporarySnapshotDataFilePath(snapshotDataFolderPath):
    return Path.Combine(snapshotDataFolderPath, TEMP_SNAPSHOT_DATA_FILENAME)


def ReadSnapshotDataRevitJournalFilePath(snapshotDataFilePath):
    text = text_file_util.ReadFromTextFile(snapshotDataFilePath)
    jobjectSnapshotData = json_util.DeserializeToJObject(text)
    return jobjectSnapshotData[SNAPSHOT_DATA__REVIT_JOURNAL_FILE].ToObject[str]()


def CopySnapshotRevitJournalFile(snapshotDataFolderPath, output):
    revitJournalFilePath = None
    try:
        snapshotDataFilePath = GetSnapshotDataFilePath(snapshotDataFolderPath)
        revitJournalFilePath = ReadSnapshotDataRevitJournalFilePath(snapshotDataFilePath)
    except Exception as e:
        output()
        output("WARNING: failed to read journal file path from snapshot data file.")
        exception_util.LogOutputErrorDetails(e, output)
        output()
        output("Attempting to read journal file path from temporary snapshot data file instead.")
        snapshotDataFilePath = GetTemporarySnapshotDataFilePath(snapshotDataFolderPath)
        revitJournalFilePath = ReadSnapshotDataRevitJournalFilePath(snapshotDataFilePath)
    revitJournalFileName = Path.GetFileName(revitJournalFilePath)
    snapshotRevitJournalFilePath = Path.Combine(snapshotDataFolderPath, revitJournalFileName)
    File.Copy(revitJournalFilePath, snapshotRevitJournalFilePath)


def ConsolidateSnapshotData(dataExportFolderPath, output):
    try:
        snapshotDataFilePath = GetSnapshotDataFilePath(dataExportFolderPath)
        temporarySnapshotDataFilePath = GetTemporarySnapshotDataFilePath(dataExportFolderPath)
        if File.Exists(snapshotDataFilePath):
            if File.Exists(temporarySnapshotDataFilePath):
                File.Delete(temporarySnapshotDataFilePath)
        elif File.Exists(temporarySnapshotDataFilePath):
            File.Move(temporarySnapshotDataFilePath, snapshotDataFilePath)
        else:
            output()
            output("WARNING: could not find snapshot data file in snapshot data folder:")
            output()
            output("\t" + dataExportFolderPath)
    except Exception as e:
        output()
        output("WARNING: failed to properly consolidate the snapshot data in folder:")
        output()
        output("\t" + dataExportFolderPath)
        exception_util.LogOutputErrorDetails(e, output)
