#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes: `except X, e:` → `as e:` throughout.
#

import clr
import System
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import ModelPathUtils, WorksetConfiguration, WorksetConfigurationOption
from Autodesk.Revit.Exceptions import OperationCanceledException, CorruptModelException, InvalidOperationException, ArgumentException

import exception_util
import path_util
import revit_file_util
import revit_dialog_util
import revit_failure_handling
import batch_rvt_util
from batch_rvt_util import ScriptDataUtil, BatchRvt

OUTPUT_FUNCTION_CONTAINER = [None]

SCRIPT_DATA_FILE_PATH_CONTAINER = [None]
SCRIPT_DATA_CONTAINER = [None]

SCRIPT_DOCUMENT_CONTAINER = [None]
SCRIPT_UIAPPLICATION_CONTAINER = [None]


def SetOutputFunction(output):
    OUTPUT_FUNCTION_CONTAINER[0] = output


def SetScriptDataFilePath(scriptDataFilePath):
    SCRIPT_DATA_FILE_PATH_CONTAINER[0] = scriptDataFilePath


def SetScriptDocument(doc):
    SCRIPT_DOCUMENT_CONTAINER[0] = doc


def SetUIApplication(uiapp):
    SCRIPT_UIAPPLICATION_CONTAINER[0] = uiapp


def Output(m="", msgId=""):
    message = (("[" + str(msgId) + "]" + " ") if msgId != "" else "") + m
    OUTPUT_FUNCTION_CONTAINER[0](message)


def GetScriptDataFilePath():
    return SCRIPT_DATA_FILE_PATH_CONTAINER[0]


def LoadScriptDatas():
    scriptDataFilePath = GetScriptDataFilePath()
    if scriptDataFilePath is None:
        raise Exception("ERROR: could not retrieve script data file path from host.")
    scriptDatas = ScriptDataUtil.LoadManyFromFile(scriptDataFilePath)
    if scriptDatas is None:
        raise Exception("ERROR: could not load script data file.")
    return scriptDatas


def GetCurrentScriptData():
    return SCRIPT_DATA_CONTAINER[0]


def SetCurrentScriptData(scriptData):
    SCRIPT_DATA_CONTAINER[0] = scriptData


def IsCloudModel():
    return SCRIPT_DATA_CONTAINER[0].IsCloudModel.GetValue()


def GetCloudProjectId():
    return SCRIPT_DATA_CONTAINER[0].CloudProjectId.GetValue()


def GetCloudModelId():
    return SCRIPT_DATA_CONTAINER[0].CloudModelId.GetValue()


def GetRevitFilePath():
    return SCRIPT_DATA_CONTAINER[0].RevitFilePath.GetValue()


def GetOpenInUI():
    return SCRIPT_DATA_CONTAINER[0].OpenInUI.GetValue()


def GetProjectFolderName():
    revitFilePath = GetRevitFilePath()
    if str.IsNullOrWhiteSpace(revitFilePath):
        return None
    return path_util.GetProjectFolderNameFromRevitProjectFilePath(revitFilePath)


def GetDataExportFolderPath():
    return SCRIPT_DATA_CONTAINER[0].DataExportFolderPath.GetValue()


def GetSessionId():
    return SCRIPT_DATA_CONTAINER[0].SessionId.GetValue()


def GetTaskScriptFilePath():
    return SCRIPT_DATA_CONTAINER[0].TaskScriptFilePath.GetValue()


def GetTaskData():
    return SCRIPT_DATA_CONTAINER[0].TaskData.GetValue()


def GetSessionDataFolderPath():
    return SCRIPT_DATA_CONTAINER[0].SessionDataFolderPath.GetValue()


def GetShowMessageBoxOnTaskError():
    return SCRIPT_DATA_CONTAINER[0].ShowMessageBoxOnTaskScriptError.GetValue()


def GetEnableDataExport():
    return SCRIPT_DATA_CONTAINER[0].EnableDataExport.GetValue()


def GetRevitProcessingOption():
    return SCRIPT_DATA_CONTAINER[0].RevitProcessingOption.GetValue()


def GetCentralFileOpenOption():
    return SCRIPT_DATA_CONTAINER[0].CentralFileOpenOption.GetValue()


def GetDeleteLocalAfter():
    return SCRIPT_DATA_CONTAINER[0].DeleteLocalAfter.GetValue()


def GetDiscardWorksetsOnDetach():
    return SCRIPT_DATA_CONTAINER[0].DiscardWorksetsOnDetach.GetValue()


def GetWorksetConfigurationOption():
    return SCRIPT_DATA_CONTAINER[0].WorksetConfigurationOption.GetValue()


def GetAuditOnOpening():
    return SCRIPT_DATA_CONTAINER[0].AuditOnOpening.GetValue()


def GetProgressNumber():
    return SCRIPT_DATA_CONTAINER[0].ProgressNumber.GetValue()


def GetProgressMax():
    return SCRIPT_DATA_CONTAINER[0].ProgressMax.GetValue()


def GetAssociatedData():
    return SCRIPT_DATA_CONTAINER[0].AssociatedData.GetValue()


def GetScriptDocument():
    return SCRIPT_DOCUMENT_CONTAINER[0]


def GetUIApplication():
    return SCRIPT_UIAPPLICATION_CONTAINER[0]


def WithExceptionLogging(action, output):
    try:
        return action()
    except Exception as e:
        exception_util.LogOutputErrorDetails(e, output)
        raise


def CreateWorksetConfiguration(batchRvtWorksetConfigurationOption):
    worksetConfigurationOption = (
        WorksetConfigurationOption.CloseAllWorksets if batchRvtWorksetConfigurationOption == BatchRvt.WorksetConfigurationOption.CloseAllWorksets
        else WorksetConfigurationOption.OpenAllWorksets if batchRvtWorksetConfigurationOption == BatchRvt.WorksetConfigurationOption.OpenAllWorksets
        else WorksetConfigurationOption.OpenLastViewed
    )
    return WorksetConfiguration(worksetConfigurationOption)


def GetWorksharingCentralModelPath(doc):
    try:
        return doc.GetWorksharingCentralModelPath()
    except InvalidOperationException:
        return None


def GetCentralModelFilePath(doc):
    modelPath = GetWorksharingCentralModelPath(doc)
    if modelPath is None:
        return str.Empty
    return ModelPathUtils.ConvertModelPathToUserVisiblePath(modelPath)


def GetActiveDocument(uiapp):
    uidoc = uiapp.ActiveUIDocument
    return uidoc.Document if uidoc is not None else None


def SafeCloseWithoutSave(doc, isOpenedInUI, closedMessage, output):
    app = doc.Application
    try:
        if not isOpenedInUI:
            revit_file_util.CloseWithoutSave(doc)
            output()
            output(closedMessage)
    except InvalidOperationException as e:
        output()
        output("WARNING: Couldn't close the document!")
        output()
        output(str(e.Message))
    except Exception as e:
        output()
        output("WARNING: Couldn't close the document!")
        exception_util.LogOutputErrorDetails(e, output, False)
    app.PurgeReleasedAPIObjects()


def WithOpenedDetachedDocument(uiapp, openInUI, centralFilePath, discardWorksets, worksetConfig, audit, documentAction, output):
    app = uiapp.Application
    output()
    output("Opening detached instance of central file: " + centralFilePath)
    closeAllWorksets = worksetConfig is None
    if openInUI:
        if discardWorksets:
            uidoc = revit_file_util.OpenAndActivateDetachAndDiscardWorksets(uiapp, centralFilePath, audit)
        else:
            uidoc = revit_file_util.OpenAndActivateDetachAndPreserveWorksets(uiapp, centralFilePath, closeAllWorksets, worksetConfig, audit)
        doc = uidoc.Document
    else:
        if discardWorksets:
            doc = revit_file_util.OpenDetachAndDiscardWorksets(app, centralFilePath, audit)
        else:
            doc = revit_file_util.OpenDetachAndPreserveWorksets(app, centralFilePath, closeAllWorksets, worksetConfig, audit)
    try:
        return documentAction(doc)
    finally:
        SafeCloseWithoutSave(doc, openInUI, "Closed detached instance of central file: " + centralFilePath, output)


def WithOpenedNewLocalDocument(uiapp, openInUI, centralFilePath, localFilePath, worksetConfig, audit, documentAction, output):
    result = None
    try:
        app = uiapp.Application
        output()
        output("Opening local instance of central file: " + centralFilePath)
        output()
        output("New local file: " + localFilePath)
        closeAllWorksets = worksetConfig is None
        if openInUI:
            uidoc = revit_file_util.OpenAndActivateNewLocal(uiapp, centralFilePath, localFilePath, closeAllWorksets, worksetConfig, audit)
            doc = uidoc.Document
        else:
            doc = revit_file_util.OpenNewLocal(app, centralFilePath, localFilePath, closeAllWorksets, worksetConfig, audit)
        try:
            result = documentAction(doc)
        finally:
            SafeCloseWithoutSave(doc, openInUI, "Closed local file: " + localFilePath, output)
    except ArgumentException as e:
        if e.Message == "The model is a local file.\r\nParameter name: sourcePath":
            output()
            output("ERROR: The model is a local file. Cannot create another local file from it!")
        else:
            raise
    return result


def WithOpenedCloudDocument(uiapp, openInUI, cloudProjectId, cloudModelId, worksetConfig, audit, documentAction, output):
    app = uiapp.Application
    output()
    output("Opening cloud model.")
    closeAllWorksets = worksetConfig is None
    if openInUI:
        uidoc = revit_file_util.OpenAndActivateCloudDocument(uiapp, cloudProjectId, cloudModelId, closeAllWorksets, worksetConfig, audit)
        doc = uidoc.Document
    else:
        doc = revit_file_util.OpenCloudDocument(app, cloudProjectId, cloudModelId, closeAllWorksets, worksetConfig, audit)

    if isinstance(doc, str):
        output()
        output(doc)
        return None

    try:
        cloudModelPathText = ModelPathUtils.ConvertModelPathToUserVisiblePath(doc.GetCloudModelPath())
        output()
        output("Cloud model path is: " + cloudModelPathText)
        return documentAction(doc)
    finally:
        SafeCloseWithoutSave(doc, openInUI, "Closed cloud model.", output)


def WithOpenedDocument(uiapp, openInUI, revitFilePath, audit, documentAction, output):
    app = uiapp.Application
    output()
    output("Opening file: " + revitFilePath)
    if openInUI:
        uidoc = revit_file_util.OpenAndActivateDocumentFile(uiapp, revitFilePath, audit)
        doc = uidoc.Document
    else:
        doc = revit_file_util.OpenDocumentFile(app, revitFilePath, audit)
    try:
        return documentAction(doc)
    finally:
        SafeCloseWithoutSave(doc, openInUI, "Closed file: " + revitFilePath, output)


def RunDetachedDocumentAction(uiapp, openInUI, centralFilePath, discardWorksets, batchRvtWorksetConfigurationOption, auditOnOpening, documentAction, output):
    def revitAction():
        return WithOpenedDetachedDocument(
            uiapp, openInUI, centralFilePath, discardWorksets,
            CreateWorksetConfiguration(batchRvtWorksetConfigurationOption),
            auditOnOpening, documentAction, output,
        )
    return WithErrorReportingAndHandling(uiapp, revitAction, output)


def RunNewLocalDocumentAction(uiapp, openInUI, centralFilePath, localFilePath, batchRvtWorksetConfigurationOption, auditOnOpening, documentAction, output):
    def revitAction():
        return WithOpenedNewLocalDocument(
            uiapp, openInUI, centralFilePath, localFilePath,
            CreateWorksetConfiguration(batchRvtWorksetConfigurationOption),
            auditOnOpening, documentAction, output,
        )
    return WithErrorReportingAndHandling(uiapp, revitAction, output)


def RunCloudDocumentAction(uiapp, openInUI, cloudProjectId, cloudModelId, batchRvtWorksetConfigurationOption, auditOnOpening, documentAction, output):
    def revitAction():
        return WithOpenedCloudDocument(
            uiapp, openInUI, cloudProjectId, cloudModelId,
            CreateWorksetConfiguration(batchRvtWorksetConfigurationOption),
            auditOnOpening, documentAction, output,
        )
    return WithErrorReportingAndHandling(uiapp, revitAction, output)


def RunDocumentAction(uiapp, openInUI, revitFilePath, auditOnOpening, documentAction, output):
    def revitAction():
        return WithOpenedDocument(uiapp, openInUI, revitFilePath, auditOnOpening, documentAction, output)
    return WithErrorReportingAndHandling(uiapp, revitAction, output)


def WithErrorReportingAndHandling(uiapp, revitAction, output):
    def action():
        return WithDocumentOpeningErrorReporting(revitAction, output)
    return WithAutomatedErrorHandling(uiapp, action, output)


def WithDocumentOpeningErrorReporting(documentOpeningAction, output):
    try:
        return documentOpeningAction()
    except OperationCanceledException as e:
        output()
        output("ERROR: The operation was canceled: " + e.Message)
        raise
    except CorruptModelException as e:
        output()
        output("ERROR: Model is corrupt: " + e.Message)
        raise


def WithAutomatedErrorHandling(uiapp, revitAction, output):
    def action():
        def inner():
            return revit_dialog_util.WithDialogBoxShowingHandler(uiapp, revitAction, output)
        return revit_failure_handling.WithFailuresProcessingHandler(uiapp.Application, inner, output)
    return WithExceptionLogging(action, output)
