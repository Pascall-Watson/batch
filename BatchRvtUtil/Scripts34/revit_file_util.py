#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes: `except X, e:` → `as e:`.
#

import clr
import System

from System import Environment
from System.IO import Path
import path_util

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

import cloud_region_util


class CentralLockedCallback(ICentralLockedCallback):
    def __init__(self, shouldWaitForLockAvailabilityCallback):
        self.ShouldWaitForLockAvailabilityCallback = shouldWaitForLockAvailabilityCallback

    def ShouldWaitForLockAvailability(self):
        return self.ShouldWaitForLockAvailabilityCallback()


def CreateTransactWithCentralOptions(shouldWaitForLockAvailabilityCallback=None):
    transactWithCentralOptions = TransactWithCentralOptions()
    if shouldWaitForLockAvailabilityCallback is not None:
        transactWithCentralOptions.SetLockCallback(CentralLockedCallback(shouldWaitForLockAvailabilityCallback))
    return transactWithCentralOptions


def CreateSynchronizeWithCentralOptions(comment=str.Empty, compact=True, saveLocalBefore=True, saveLocalAfter=True, relinquishOptions=None):
    syncOptions = SynchronizeWithCentralOptions()
    syncOptions.Comment = comment
    syncOptions.Compact = compact
    syncOptions.SaveLocalBefore = saveLocalBefore
    syncOptions.SaveLocalAfter = saveLocalAfter
    if relinquishOptions is None:
        relinquishOptions = RelinquishOptions(relinquishEverything=True)
    syncOptions.SetRelinquishOptions(relinquishOptions)
    return syncOptions


def SynchronizeWithCentral(doc, comment=str.Empty):
    doc.SynchronizeWithCentral(CreateTransactWithCentralOptions(), CreateSynchronizeWithCentralOptions(comment=comment))


def ReloadLastest(doc):
    doc.ReloadLatest(ReloadLatestOptions())


def CopyModel(app, sourceModelPath, destinationFilePath, overwrite=True):
    app.CopyModel(ToModelPath(sourceModelPath), destinationFilePath, overwrite)


def CreateNewProjectFile(app, revitFilePath):
    newDoc = app.NewProjectDocument(app.DefaultProjectTemplate)
    saveAsOptions = SaveAsOptions()
    saveAsOptions.OverwriteExistingFile = True
    newDoc.SaveAs(revitFilePath, saveAsOptions)
    return newDoc


def OpenAndActivateBatchRvtTemporaryDocument(uiApplication):
    application = uiApplication.Application
    BATCHRVT_TEMPORARY_REVIT_FILE_PATH = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "BatchRvt",
        "TemporaryProject." + application.VersionNumber + ".rvt",
    )
    if not path_util.FileExists(BATCHRVT_TEMPORARY_REVIT_FILE_PATH):
        path_util.CreateDirectoryForFilePath(BATCHRVT_TEMPORARY_REVIT_FILE_PATH)
        newDoc = CreateNewProjectFile(application, BATCHRVT_TEMPORARY_REVIT_FILE_PATH)
        newDoc.Close(False)
    return uiApplication.OpenAndActivateDocument(BATCHRVT_TEMPORARY_REVIT_FILE_PATH)


def ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig):
    return (
        worksetConfig if worksetConfig is not None else
        WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets) if closeAllWorksets else
        WorksetConfiguration()
    )


def ToModelPath(modelPath):
    if isinstance(modelPath, str):
        modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(modelPath)
    return modelPath


def ToUserVisiblePath(modelPath):
    if isinstance(modelPath, ModelPath):
        modelPath = ModelPathUtils.ConvertModelPathToUserVisiblePath(modelPath)
    return modelPath


def ToGuid(guidOrGuidText):
    return System.Guid(guidOrGuidText) if not isinstance(guidOrGuidText, System.Guid) else guidOrGuidText


def ToCloudPath(cloudProjectId, cloudModelId):
    return ModelPathUtils.ConvertCloudGUIDsToCloudPath(ToGuid(cloudProjectId), ToGuid(cloudModelId))


def _append_unique_region_candidate(candidates, candidate):
    if candidate is None:
        return
    for existing in candidates:
        if existing == candidate:
            return
    candidates.append(candidate)


def ToCloudPath2021(cloudProjectId, cloudModelId):
    cloudProjectGuid = ToGuid(cloudProjectId)
    cloudModelGuid = ToGuid(cloudModelId)

    regionMapping = cloud_region_util.get_region_api_mapping()
    regionCandidates = []

    for regionCode in cloud_region_util.GetFallbackOrder():
        if regionCode in regionMapping:
            _append_unique_region_candidate(regionCandidates, regionMapping[regionCode])

    for regionValue in regionMapping.values():
        _append_unique_region_candidate(regionCandidates, regionValue)

    for discoveredRegion in cloud_region_util.GetDiscoveredApiRegions():
        _append_unique_region_candidate(regionCandidates, discoveredRegion)

    for regionValue in regionCandidates:
        try:
            return ModelPathUtils.ConvertCloudGUIDsToCloudPath(regionValue, cloudProjectGuid, cloudModelGuid)
        except Exception:
            continue

    return cloud_region_util.get_unrecognised_region_msg()


def OpenNewLocal(application, modelPath, localModelPath, closeAllWorksets=False, worksetConfig=None, audit=False):
    modelPath = ToModelPath(modelPath)
    localModelPath = ToModelPath(localModelPath)
    openOptions = OpenOptions()
    openOptions.DetachFromCentralOption = DetachFromCentralOption.DoNotDetach
    worksetConfig = ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig)
    openOptions.SetOpenWorksetsConfiguration(worksetConfig)
    WorksharingUtils.CreateNewLocal(modelPath, localModelPath)
    if audit:
        openOptions.Audit = True
    return application.OpenDocumentFile(localModelPath, openOptions)


def OpenAndActivateNewLocal(uiApplication, modelPath, localModelPath, closeAllWorksets=False, worksetConfig=None, audit=False):
    modelPath = ToModelPath(modelPath)
    localModelPath = ToModelPath(localModelPath)
    openOptions = OpenOptions()
    openOptions.DetachFromCentralOption = DetachFromCentralOption.DoNotDetach
    worksetConfig = ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig)
    openOptions.SetOpenWorksetsConfiguration(worksetConfig)
    WorksharingUtils.CreateNewLocal(modelPath, localModelPath)
    if audit:
        openOptions.Audit = True
    return uiApplication.OpenAndActivateDocument(localModelPath, openOptions, False)


def OpenDetachAndPreserveWorksets(application, modelPath, closeAllWorksets=False, worksetConfig=None, audit=False):
    modelPath = ToModelPath(modelPath)
    openOptions = OpenOptions()
    openOptions.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
    worksetConfig = ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig)
    openOptions.SetOpenWorksetsConfiguration(worksetConfig)
    if audit:
        openOptions.Audit = True
    return application.OpenDocumentFile(modelPath, openOptions)


def OpenAndActivateDetachAndPreserveWorksets(uiApplication, modelPath, closeAllWorksets=False, worksetConfig=None, audit=False):
    modelPath = ToModelPath(modelPath)
    openOptions = OpenOptions()
    openOptions.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
    worksetConfig = ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig)
    openOptions.SetOpenWorksetsConfiguration(worksetConfig)
    if audit:
        openOptions.Audit = True
    return uiApplication.OpenAndActivateDocument(modelPath, openOptions, False)


def IsRvt2021_OrNewer(application):
    try:
        return int(application.VersionNumber) > 2020
    except:
        return False


def OpenCloudDocument(application, cloudProjectId, cloudModelId, closeAllWorksets=False, worksetConfig=None, audit=False):
    cloudPath = ToCloudPath2021(cloudProjectId, cloudModelId) if IsRvt2021_OrNewer(application) else ToCloudPath(cloudProjectId, cloudModelId)
    openOptions = OpenOptions()
    openOptions.SetOpenWorksetsConfiguration(ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig))
    if audit:
        openOptions.Audit = True
    if isinstance(cloudPath, str) and cloudPath == cloud_region_util.get_unrecognised_region_msg():
        return cloudPath
    return application.OpenDocumentFile(cloudPath, openOptions)


def OpenAndActivateCloudDocument(uiApplication, cloudProjectId, cloudModelId, closeAllWorksets=False, worksetConfig=None, audit=False):
    cloudPath = ToCloudPath2021(cloudProjectId, cloudModelId) if IsRvt2021_OrNewer(uiApplication.Application) else ToCloudPath(cloudProjectId, cloudModelId)
    openOptions = OpenOptions()
    openOptions.SetOpenWorksetsConfiguration(ParseWorksetConfigurationOption(closeAllWorksets, worksetConfig))
    if audit:
        openOptions.Audit = True
    if isinstance(cloudPath, str) and cloudPath == cloud_region_util.get_unrecognised_region_msg():
        return cloudPath
    return uiApplication.OpenAndActivateDocument(cloudPath, openOptions, False)


def OpenDetachAndDiscardWorksets(application, modelPath, audit=False):
    modelPath = ToModelPath(modelPath)
    openOptions = OpenOptions()
    openOptions.DetachFromCentralOption = DetachFromCentralOption.DetachAndDiscardWorksets
    if audit:
        openOptions.Audit = True
    return application.OpenDocumentFile(modelPath, openOptions)


def OpenAndActivateDetachAndDiscardWorksets(uiApplication, modelPath, audit=False):
    modelPath = ToModelPath(modelPath)
    openOptions = OpenOptions()
    openOptions.DetachFromCentralOption = DetachFromCentralOption.DetachAndDiscardWorksets
    if audit:
        openOptions.Audit = True
    return uiApplication.OpenAndActivateDocument(modelPath, openOptions, False)


def OpenDocumentFile(application, modelPath, audit=False):
    if audit:
        openOptions = OpenOptions()
        openOptions.Audit = True
        modelPath = ToModelPath(modelPath)
        return application.OpenDocumentFile(modelPath, openOptions)
    return application.OpenDocumentFile(ToUserVisiblePath(modelPath))


def OpenAndActivateDocumentFile(uiApplication, modelPath, audit=False):
    if audit:
        openOptions = OpenOptions()
        openOptions.Audit = True
        modelPath = ToModelPath(modelPath)
        return uiApplication.OpenAndActivateDocument(modelPath, openOptions, False)
    return uiApplication.OpenAndActivateDocument(ToUserVisiblePath(modelPath))


def RelinquishAll(doc, shouldWaitForLockAvailabilityCallback=None):
    return WorksharingUtils.RelinquishOwnership(
        doc,
        RelinquishOptions(True),
        CreateTransactWithCentralOptions(shouldWaitForLockAvailabilityCallback),
    )


def SaveAsNewCentral(doc, modelPath, overwrite=True, clearTransmitted=False):
    saveAsOptions = SaveAsOptions()
    saveAsOptions.Compact = True
    saveAsOptions.OverwriteExistingFile = overwrite
    saveAsOptions.MaximumBackups = 1  # Can't set this to 0, unfortunately.
    worksharingSaveAsOptions = WorksharingSaveAsOptions()
    worksharingSaveAsOptions.SaveAsCentral = True
    worksharingSaveAsOptions.ClearTransmitted = clearTransmitted
    saveAsOptions.SetWorksharingOptions(worksharingSaveAsOptions)
    doc.SaveAs(modelPath, saveAsOptions)


def CloseWithSave(doc):
    doc.Close(True)


def CloseWithoutSave(doc):
    doc.Close(False)


def Save(doc, compact=False, previewViewId=None):
    saveOptions = SaveOptions()
    saveOptions.Compact = compact
    if previewViewId is not None:
        saveOptions.PreviewViewId = previewViewId
    doc.Save(saveOptions)


def SaveAs(doc, modelPath, overwriteExisting=False, compact=False, previewViewId=None, worksharingSaveAsOptions=None, maximumBackups=None):
    modelPath = ToModelPath(modelPath)
    saveAsOptions = SaveAsOptions()
    saveAsOptions.Compact = compact
    saveAsOptions.OverwriteExistingFile = overwriteExisting
    if previewViewId is not None:
        saveAsOptions.PreviewViewId = previewViewId
    if worksharingSaveAsOptions is not None:
        saveAsOptions.SetWorksharingOptions(worksharingSaveAsOptions)
    if maximumBackups is not None:
        saveAsOptions.MaximumBackups = maximumBackups
    doc.SaveAs(modelPath, saveAsOptions)


def CreateWorksharingSaveAsOptions(saveAsCentral=False, openWorksetsDefault=SimpleWorksetConfiguration.AskUserToSpecify, clearTransmitted=False):
    worksharingSaveAsOptions = WorksharingSaveAsOptions()
    worksharingSaveAsOptions.OpenWorksetsDefault = openWorksetsDefault
    worksharingSaveAsOptions.ClearTransmitted = clearTransmitted
    worksharingSaveAsOptions.SaveAsCentral = saveAsCentral
    return worksharingSaveAsOptions


def DetachAndSaveModel(app, centralModelFilePath, detachedModelFilePath, audit=False):
    centralModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(centralModelFilePath)
    CopyModel(app, centralModelPath, detachedModelFilePath)
    detachedModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(detachedModelFilePath)
    doc = OpenDetachAndPreserveWorksets(app, detachedModelPath, audit=audit)
    SaveAsNewCentral(doc, detachedModelPath)
    RelinquishAll(doc)
    return doc


def TryGetBasicFileInfo(revitFilePath):
    try:
        return BasicFileInfo.Extract(revitFilePath)
    except Exception:
        return None


def GetSavedInVersion(basicFileInfo):
    try:
        # <= Revit 2019
        return basicFileInfo.SavedInVersion
    except System.MissingMemberException:
        # Revit 2020+
        return basicFileInfo.Format


def GetRevitFileVersion(revitFilePath):
    basicFileInfo = TryGetBasicFileInfo(revitFilePath)
    return GetSavedInVersion(basicFileInfo) if basicFileInfo is not None else None


def IsLocalModel(revitFilePath):
    basicFileInfo = TryGetBasicFileInfo(revitFilePath)
    if basicFileInfo is not None and basicFileInfo.IsWorkshared:
        # https://forums.autodesk.com/t5/revit-api-forum/basicfileinfo-iscreatedlocal-property-outputting-unexpected/td-p/7111503
        return basicFileInfo.IsCreatedLocal or basicFileInfo.IsLocal
    return False


def IsCentralModel(revitFilePath):
    basicFileInfo = TryGetBasicFileInfo(revitFilePath)
    if basicFileInfo is not None and basicFileInfo.IsWorkshared:
        return basicFileInfo.IsCentral
    return False


def IsWorkshared(revitFilePath):
    basicFileInfo = TryGetBasicFileInfo(revitFilePath)
    return basicFileInfo.IsWorkshared if basicFileInfo is not None else False
