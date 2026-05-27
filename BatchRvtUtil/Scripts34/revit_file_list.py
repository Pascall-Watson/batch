#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes: `except X, e:` → `as e:`.
#

import clr
import System
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
from System import ArgumentException, NotSupportedException, StringSplitOptions, Guid
from System.IO import PathTooLongException

import text_file_util
import csv_util
import console_util
import path_util
import revit_file_version
import batch_rvt_util
from batch_rvt_util import RevitVersion
import cloud_region_util


class RevitFilePathData:
    def __init__(self, revitFilePath, associatedData):
        self.RevitFilePath = revitFilePath.Trim()
        self.AssociatedData = [value.Trim() for value in associatedData]


def FirstOrDefault(items, default=None):
    for item in items:
        return item
    return default


def GetRevitFileListData(rows):
    return [
        RevitFilePathData(row[0], row[1:])
        for row in rows
        if not str.IsNullOrWhiteSpace(FirstOrDefault(row))  # Ignore rows where the first column is empty.
    ]


def FromTextFile(textFilePath):
    return GetRevitFileListData(text_file_util.GetRowsFromTextFile(textFilePath))


def FromText(text):
    return GetRevitFileListData(text_file_util.GetRowsFromText(text))


def FromLines(lines):
    return GetRevitFileListData(text_file_util.GetRowsFromLines(lines))


def FromCSVFile(csvFilePath):
    return GetRevitFileListData(csv_util.GetRowsFromCSVFile(csvFilePath))


def IsExcelInstalled():
    return System.Type.GetTypeFromProgID("Excel.Application") is not None


def HasExcelFileExtension(filePath):
    return any(path_util.HasFileExtension(filePath, extension) for extension in [".xlsx", ".xls"])


def FromExcelFile(excelFilePath):
    import excel_util
    return GetRevitFileListData(excel_util.ReadRowsTextFromWorkbook(excelFilePath))


def FromConsole():
    return FromLines(console_util.ReadLines())


# updated to include ACC region support
class RevitCloudModelInfo:
    def __init__(self, cloudModelDescriptor):
        self.cloudModelDescriptor = cloudModelDescriptor
        self.projectGuid = None
        self.modelGuid = None
        self.revitVersionText = None
        self.region = None
        self.isValid = False

        parts = self.GetCloudModelDescriptorParts(cloudModelDescriptor)
        numberOfParts = len(parts)

        if numberOfParts > 1:
            revitVersionPart = str.Empty
            if numberOfParts > 2:
                revitVersionPart = parts[0]
                otherParts = parts[1:]
            else:
                otherParts = parts

            self.projectGuid = self.SafeParseGuidText(otherParts[0])
            self.modelGuid = self.SafeParseGuidText(otherParts[1])

            if len(otherParts) > 2:
                regionPart = otherParts[2].strip()
                if cloud_region_util.ValidateRegionCode(regionPart):
                    self.region = cloud_region_util.NormalizeRegionCode(regionPart)

            if RevitVersion.IsSupportedRevitVersionNumber(revitVersionPart):
                self.revitVersionText = revitVersionPart

            self.isValid = (self.projectGuid is not None and self.modelGuid is not None)

    def IsValid(self):
        return self.isValid

    def GetProjectGuid(self):
        return self.projectGuid

    def GetModelGuid(self):
        return self.modelGuid

    def GetRevitVersionText(self):
        return self.revitVersionText

    def GetRegion(self):
        return self.region

    def GetRegionOrDefault(self, defaultRegion=None):
        if self.region is not None:
            return self.region
        if defaultRegion is not None:
            return defaultRegion
        return cloud_region_util.DEFAULT_REGION

    def GetRegionDescription(self):
        return cloud_region_util.GetRegionDescription(self.region)

    def GetRevitApiRegion(self):
        return cloud_region_util.GetRevitApiRegion(self.region)

    def IsDirectApiMapping(self):
        return cloud_region_util.IsDirectApiMapping(self.region)

    def GetCloudModelDescriptorParts(self, cloudModelDescriptor):
        return cloudModelDescriptor.Split([" "].ToArray[str](), StringSplitOptions.RemoveEmptyEntries)

    def SafeParseGuidText(self, guidText):
        parsed, guid = Guid.TryParse(guidText)
        return guid if parsed else None

    def GetCloudModelDescriptor(self):
        return self.cloudModelDescriptor

    def __str__(self):
        parts = []
        if self.revitVersionText:
            parts.append("Version: {0}".format(self.revitVersionText))
        if self.projectGuid:
            parts.append("Project: {0}".format(str(self.projectGuid)))
        if self.modelGuid:
            parts.append("Model: {0}".format(str(self.modelGuid)))
        if self.region:
            parts.append("Region: {0} ({1})".format(self.region, self.GetRegionDescription()))
        else:
            parts.append("Region: {0} (default)".format(cloud_region_util.DEFAULT_REGION))
        return "CloudModel[{0}]".format(", ".join(parts))


class RevitFileInfo:
    def __init__(self, revitFilePath):
        self.cloudModelInfo = RevitCloudModelInfo(revitFilePath)
        pathException = None
        try:
            revitFilePath = path_util.GetFullPath(revitFilePath)
        except ArgumentException as e:           # 'Illegal characters in path.'
            pathException = e
        except NotSupportedException as e:       # 'The given path's format is not supported.'
            pathException = e
        except PathTooLongException as e:        # 'The specified path, file name, or both are too long.'
            pathException = e
        self.revitFilePath = revitFilePath
        self.pathException = pathException

    def IsCloudModel(self):
        return self.GetRevitCloudModelInfo().IsValid()

    def GetRevitCloudModelInfo(self):
        return self.cloudModelInfo

    def IsValidFilePath(self):
        return self.pathException is None

    def IsFilePathTooLong(self):
        return isinstance(self.pathException, PathTooLongException)

    def GetFullPath(self):
        if not self.IsCloudModel():
            return self.revitFilePath
        return self.GetRevitCloudModelInfo().GetCloudModelDescriptor()

    def GetFileSize(self):
        return path_util.GetFileSize(self.revitFilePath)

    def TryGetRevitVersionText(self):
        try:
            return revit_file_version.GetRevitVersionText(self.revitFilePath)
        except Exception:
            return None

    def Exists(self):
        return path_util.FileExists(self.revitFilePath)


def FromFile(settingsFilePath):
    if text_file_util.HasTextFileExtension(settingsFilePath):
        return FromTextFile(settingsFilePath)
    if csv_util.HasCSVFileExtension(settingsFilePath):
        return FromCSVFile(settingsFilePath)
    if HasExcelFileExtension(settingsFilePath):
        return FromExcelFile(settingsFilePath)
    return None


class SupportedRevitFileInfo:
    def __init__(self, revitFilePathData):
        self.revitFileInfo = RevitFileInfo(revitFilePathData.RevitFilePath)
        self.revitFilePathData = revitFilePathData
        revitVersionText = None
        revitVersionNumber = None
        if self.revitFileInfo.IsCloudModel():
            revitVersionText = self.revitFileInfo.GetRevitCloudModelInfo().GetRevitVersionText()
            if not str.IsNullOrWhiteSpace(revitVersionText):
                if RevitVersion.IsSupportedRevitVersionNumber(revitVersionText):
                    revitVersionNumber = RevitVersion.GetSupportedRevitVersion(revitVersionText)
        else:
            revitVersionText = self.revitFileInfo.TryGetRevitVersionText()
            # TODO VERSION UPDATE - Add conditional for new Revit version
            if not str.IsNullOrWhiteSpace(revitVersionText):
                VERSION_PREFIX_MAP = [
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2015, RevitVersion.SupportedRevitVersion.Revit2015),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2016, RevitVersion.SupportedRevitVersion.Revit2016),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2017, RevitVersion.SupportedRevitVersion.Revit2017),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2018, RevitVersion.SupportedRevitVersion.Revit2018),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2019, RevitVersion.SupportedRevitVersion.Revit2019),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2020, RevitVersion.SupportedRevitVersion.Revit2020),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2021, RevitVersion.SupportedRevitVersion.Revit2021),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2022, RevitVersion.SupportedRevitVersion.Revit2022),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2023, RevitVersion.SupportedRevitVersion.Revit2023),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2024, RevitVersion.SupportedRevitVersion.Revit2024),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2025, RevitVersion.SupportedRevitVersion.Revit2025),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2026, RevitVersion.SupportedRevitVersion.Revit2026),
                    (revit_file_version.REVIT_VERSION_TEXT_PREFIXES_2027, RevitVersion.SupportedRevitVersion.Revit2027),
                ]
                for prefixes, version in VERSION_PREFIX_MAP:
                    if any(revitVersionText.StartsWith(prefix) for prefix in prefixes):
                        revitVersionNumber = version
                        break
        self.revitVersionText = revitVersionText
        self.revitVersionNumber = revitVersionNumber

    def TryGetRevitVersionNumber(self):
        return self.revitVersionNumber

    def TryGetRevitVersionText(self):
        return self.revitVersionText

    def GetRevitFileInfo(self):
        return self.revitFileInfo

    def GetRevitFilePathData(self):
        return self.revitFilePathData

    def IsCloudModel(self):
        return self.GetRevitFileInfo().IsCloudModel()

    def GetRevitCloudModelInfo(self):
        return self.GetRevitFileInfo().GetRevitCloudModelInfo()
