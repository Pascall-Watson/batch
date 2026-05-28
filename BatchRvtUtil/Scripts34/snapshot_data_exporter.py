#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System
from System.IO import Path, File

import text_file_util
import json_util
import snapshot_data_util
import path_util
import revit_file_util
import time_util
import environment
import network_util


def GetSnapshotData(
    sessionId,
    revitFilePath,
    isCloudModel,
    cloudProjectId,
    cloudModelId,
    snapshotStartTime,
    snapshotEndTime,
    snapshotFolderPath,
    revitJournalFilePath,
    snapshotError,
):
    if isCloudModel:
        projectFolderName = None
        projectModelFolderPath = None
        modelFolder = None
        modelName = None
        modelFileLastModified = None
        modelFileSize = None
        modelRevitVersion = None
        modelRevitVersionDetails = None
    else:
        projectFolderName = path_util.GetProjectFolderNameFromRevitProjectFilePath(revitFilePath)
        projectModelFolderPath = Path.GetDirectoryName(revitFilePath)
        modelFolder = path_util.ExpandedFullNetworkPath(projectModelFolderPath)
        modelName = snapshot_data_util.GetRevitModelName(revitFilePath)
        modelFileLastModified = path_util.GetLastWriteTimeUtc(revitFilePath)
        modelFileSize = path_util.GetFileSize(revitFilePath)
        modelRevitVersion = revit_file_util.GetRevitFileVersion(revitFilePath)
        modelRevitVersionDetails = snapshot_data_util.GetRevitFileVersionDetails(revitFilePath)

    return {
        "isCloudModel": isCloudModel,
        "cloudProjectId": cloudProjectId,
        "cloudModelId": cloudModelId,
        "projectFolderName": projectFolderName,
        "modelFolder": modelFolder,
        "modelName": modelName,
        "modelFileLastModified": (
            time_util.GetTimestampObject(modelFileLastModified)
            if modelFileLastModified is not None else None
        ),
        "modelFileSize": modelFileSize,
        "modelRevitVersion": modelRevitVersion,
        "modelRevitVersionDetails": modelRevitVersionDetails,
        "snapshotStartTime": (
            time_util.GetTimestampObject(snapshotStartTime)
            if snapshotStartTime is not None else None
        ),
        "snapshotEndTime": (
            time_util.GetTimestampObject(snapshotEndTime)
            if snapshotEndTime is not None else None
        ),
        "sessionId": sessionId,
        "snapshotFolder": path_util.ExpandedFullNetworkPath(snapshotFolderPath),
        "snapshotError": snapshotError,
        "username": environment.GetUserName(),
        "machineName": environment.GetMachineName(),
        "gatewayAddresses": network_util.GetGatewayAddresses(),
        "ipAddresses": network_util.GetIPAddresses(),
        snapshot_data_util.SNAPSHOT_DATA__REVIT_JOURNAL_FILE: revitJournalFilePath,
    }


def ExportSnapshotDataInternal(
    snapshotDataFilePath, sessionId, revitProjectFilePath, isCloudModel,
    cloudProjectId, cloudModelId, snapshotStartTime, snapshotEndTime,
    dataExportFolderPath, revitJournalFilePath, snapshotError,
):
    snapshotData = GetSnapshotData(
        sessionId, revitProjectFilePath, isCloudModel,
        cloudProjectId, cloudModelId, snapshotStartTime, snapshotEndTime,
        dataExportFolderPath, revitJournalFilePath, snapshotError,
    )
    serializedSnapshotData = json_util.SerializeObject(snapshotData, True)
    text_file_util.WriteToTextFile(snapshotDataFilePath, serializedSnapshotData)
    return snapshotData


def ExportSnapshotData(
    sessionId, revitProjectFilePath, isCloudModel, cloudProjectId, cloudModelId,
    snapshotStartTime, snapshotEndTime, dataExportFolderPath,
    revitJournalFilePath, snapshotError,
):
    return ExportSnapshotDataInternal(
        snapshot_data_util.GetSnapshotDataFilePath(dataExportFolderPath),
        sessionId, revitProjectFilePath, isCloudModel,
        cloudProjectId, cloudModelId, snapshotStartTime, snapshotEndTime,
        dataExportFolderPath, revitJournalFilePath, snapshotError,
    )


def ExportTemporarySnapshotData(
    sessionId, revitProjectFilePath, isCloudModel, cloudProjectId, cloudModelId,
    snapshotStartTime, snapshotEndTime, dataExportFolderPath,
    revitJournalFilePath, snapshotError,
):
    return ExportSnapshotDataInternal(
        snapshot_data_util.GetTemporarySnapshotDataFilePath(dataExportFolderPath),
        sessionId, revitProjectFilePath, isCloudModel,
        cloudProjectId, cloudModelId, snapshotStartTime, snapshotEndTime,
        dataExportFolderPath, revitJournalFilePath, snapshotError,
    )
