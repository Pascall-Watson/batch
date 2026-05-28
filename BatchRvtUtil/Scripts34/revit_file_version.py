#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fix: `except X, e:` → `as e:`.
#

import clr

clr.AddReference("System.Core")
import System
import System.Linq
clr.ImportExtensions(System.Linq)
from System.Linq import Enumerable

import System.Reflection as Refl

import System.IO
from System.IO import IOException

from System.Reflection import TargetInvocationException

import System.Text
from System.Text import Encoding

clr.AddReference("WindowsBase")
import System.IO.Packaging as Packaging

import util

STORAGE_ROOT_TYPE_NAME = "System.IO.Packaging.StorageRoot"
STORAGE_ROOT_OPEN_METHOD_NAME = "Open"
BASIC_FILE_INFO_STREAM_NAME = "BasicFileInfo"


def GetWindowsBaseAssembly():
    return clr.GetClrType(Packaging.StorageInfo).Assembly


def GetStorageRootType():
    return GetWindowsBaseAssembly().GetType(STORAGE_ROOT_TYPE_NAME, True, False)


def InvokeStorageRootMember(storageRoot, methodName, *methodArgs):
    return GetStorageRootType().InvokeMember(
        methodName,
        Refl.BindingFlags.Static | Refl.BindingFlags.Instance |
        Refl.BindingFlags.Public | Refl.BindingFlags.NonPublic |
        Refl.BindingFlags.InvokeMethod,
        None,
        storageRoot,
        methodArgs.ToArray[object](),
    )


def GetStorageRoot(filePath):
    if str.IsNullOrWhiteSpace(filePath):
        return None
    return InvokeStorageRootMember(
        None,
        STORAGE_ROOT_OPEN_METHOD_NAME,
        filePath,
        System.IO.FileMode.Open,
        System.IO.FileAccess.Read,
        System.IO.FileShare.Read,
    )


def GetBasicFileInfoStream(storageRoot):
    return storageRoot.GetStreamInfo(BASIC_FILE_INFO_STREAM_NAME).GetStream()


def CreateByteBuffer(length):
    return Enumerable.Repeat[System.Byte](0, length).ToArray()


def ReadAllBytes(stream):
    length = int(stream.Length)
    buffer = CreateByteBuffer(length)
    readCount = stream.Read(buffer, 0, length)
    return buffer.Take(readCount).ToArray()


def GetRevitVersionText_OldMethod(revitFilePath):
    storageRoot = GetStorageRoot(revitFilePath)
    stream = GetBasicFileInfoStream(storageRoot)
    bytes_ = ReadAllBytes(stream)
    unicodeString = Encoding.Unicode.GetString(bytes_)
    start = unicodeString.IndexOf("Autodesk Revit")
    end = unicodeString.IndexOf("\x00", start)
    versionText = unicodeString.Substring(start, end - start)
    return versionText.Substring(0, versionText.LastIndexOf(")") + 1)


def GetBasicFileInfoBytes(revitFilePath):
    storageRoot = GetStorageRoot(revitFilePath)
    stream = GetBasicFileInfoStream(storageRoot)
    return ReadAllBytes(stream)


def GetRevitFileVersionInfoText(revitFilePath):
    revitVersionInfoText = str.Empty
    bytes_ = GetBasicFileInfoBytes(revitFilePath)
    asciiString = Encoding.ASCII.GetString(bytes_)
    TEXT_MARKER = '\r\n'                  # Most common delimiter around the text section.
    TEXT_MARKER_ALT = '\x04\r\x00\n\x00'  # Alternative delimiter occasionally encountered.
    textMarker = TEXT_MARKER
    textMarkerIndices = util.FindAllIndicesOf(asciiString, textMarker)
    numberOfTextMarkerIndices = len(textMarkerIndices)
    if numberOfTextMarkerIndices != 2:
        textMarker = TEXT_MARKER_ALT
        textMarkerIndices = util.FindAllIndicesOf(asciiString, textMarker)
        numberOfTextMarkerIndices = len(textMarkerIndices)
    if numberOfTextMarkerIndices == 2:
        startTextIndex = textMarkerIndices[0] + len(textMarker)
        endTextIndex = textMarkerIndices[1]
        revitVersionInfoText = Encoding.Unicode.GetString(bytes_[startTextIndex:endTextIndex])
    return revitVersionInfoText


def TryGetRevitFileVersionInfoText(revitFilePath):
    try:
        return GetRevitFileVersionInfoText(revitFilePath)
    except TargetInvocationException:
        return str.Empty
    except IOException:
        return str.Empty


def ExtractRevitVersionInfoFromText(revitVersionInfoText):
    REVIT_BUILD_PROPERTY = "Revit Build:"
    FORMAT_PROPERTY = "Format:"
    BUILD_PROPERTY = "Build:"
    revitVersionDescription = str.Empty
    lines = util.ReadLinesFromText(revitVersionInfoText)
    indexedLines = [[index, line] for index, line in enumerate(lines)]
    # Revit 2019 (and onwards?) has 'Build' and 'Format' properties instead of 'Revit Build'.
    formatLine = indexedLines.SingleOrDefault(lambda l: l[1].StartsWith(FORMAT_PROPERTY))
    buildLine = indexedLines.SingleOrDefault(lambda l: l[1].StartsWith(BUILD_PROPERTY))
    if buildLine is not None:
        buildLineText = buildLine[1][len(BUILD_PROPERTY):]
        formatLineText = str.Empty
        if formatLine is not None:
            formatLineText = formatLine[1][len(FORMAT_PROPERTY):]
            revitVersionDescription = "Autodesk Revit " + formatLineText.Trim() + " (Build: " + buildLineText.Trim() + ")"
    else:
        revitBuildLine = indexedLines.SingleOrDefault(lambda l: l[1].StartsWith(REVIT_BUILD_PROPERTY))
        revitBuildLineText = str.Empty
        if revitBuildLine is None:
            # Rare case: Revit Build *value* on the next line, followed immediately (no spaces) by 'Last Save Path:'.
            revitBuildLine = indexedLines.SingleOrDefault(lambda l: l[1].Contains(REVIT_BUILD_PROPERTY))
            if revitBuildLine is not None:
                lineNumber = revitBuildLine[0]
                revitBuildLine = indexedLines[lineNumber + 1]
                revitBuildLineText = revitBuildLine[1]
                indexOfLastSavePath = revitBuildLineText.IndexOf("Last Save Path:")
                revitBuildLineText = revitBuildLineText[:indexOfLastSavePath] if indexOfLastSavePath != -1 else revitBuildLineText
        else:
            revitBuildLineText = revitBuildLine[1][len(REVIT_BUILD_PROPERTY):]
        revitVersionDescription = revitBuildLineText.Trim()
    return revitVersionDescription


def GetRevitVersionText(revitFilePath):
    return ExtractRevitVersionInfoFromText(TryGetRevitFileVersionInfoText(revitFilePath))


def GenerateRevitVersionTextPrefixes(revitVersionNumberText, includeDisciplineVersions=False):
    REVIT_VERSION_TEXT_PREFIXES = [
        "Autodesk Revit",
        "Autodesk Revit LT",
        "Revit",
        "Revit LT",
    ]
    if includeDisciplineVersions:
        REVIT_VERSION_TEXT_PREFIXES.extend([
            "Autodesk Revit Architecture",
            "Autodesk Revit MEP",
            "Autodesk Revit Structure",
            "Revit Architecture",
            "Revit MEP",
            "Revit Structure",
        ])
    return [str.Join(" ", prefix, revitVersionNumberText) for prefix in REVIT_VERSION_TEXT_PREFIXES]


# TODO VERSION UPDATE: Add new version prefixes here as needed.
REVIT_VERSION_TEXT_PREFIXES_2010 = GenerateRevitVersionTextPrefixes("2010", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2011 = GenerateRevitVersionTextPrefixes("2011", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2012 = GenerateRevitVersionTextPrefixes("2012", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2013 = GenerateRevitVersionTextPrefixes("2013", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2014 = GenerateRevitVersionTextPrefixes("2014", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2015 = GenerateRevitVersionTextPrefixes("2015", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2016 = GenerateRevitVersionTextPrefixes("2016", includeDisciplineVersions=True)
REVIT_VERSION_TEXT_PREFIXES_2017 = GenerateRevitVersionTextPrefixes("2017")
REVIT_VERSION_TEXT_PREFIXES_2018 = GenerateRevitVersionTextPrefixes("2018")
REVIT_VERSION_TEXT_PREFIXES_2019 = GenerateRevitVersionTextPrefixes("2019")
REVIT_VERSION_TEXT_PREFIXES_2020 = GenerateRevitVersionTextPrefixes("2020")
REVIT_VERSION_TEXT_PREFIXES_2021 = GenerateRevitVersionTextPrefixes("2021")
REVIT_VERSION_TEXT_PREFIXES_2022 = GenerateRevitVersionTextPrefixes("2022")
REVIT_VERSION_TEXT_PREFIXES_2023 = GenerateRevitVersionTextPrefixes("2023")
REVIT_VERSION_TEXT_PREFIXES_2024 = GenerateRevitVersionTextPrefixes("2024")
REVIT_VERSION_TEXT_PREFIXES_2025 = GenerateRevitVersionTextPrefixes("2025")
REVIT_VERSION_TEXT_PREFIXES_2026 = GenerateRevitVersionTextPrefixes("2026")
REVIT_VERSION_TEXT_PREFIXES_2027 = GenerateRevitVersionTextPrefixes("2027")


# TODO VERSION UPDATE: Add new version checks here as needed.
def GetRevitVersionNumberTextFromRevitVersionText(revitVersionText):
    if str.IsNullOrWhiteSpace(revitVersionText):
        return None

    def StartsWithOneOfPrefixes(text, prefixes):
        return any(text.StartsWith(prefix) for prefix in prefixes)

    VERSION_MAP = [
        ("2010", REVIT_VERSION_TEXT_PREFIXES_2010),
        ("2011", REVIT_VERSION_TEXT_PREFIXES_2011),
        ("2012", REVIT_VERSION_TEXT_PREFIXES_2012),
        ("2013", REVIT_VERSION_TEXT_PREFIXES_2013),
        ("2014", REVIT_VERSION_TEXT_PREFIXES_2014),
        ("2015", REVIT_VERSION_TEXT_PREFIXES_2015),
        ("2016", REVIT_VERSION_TEXT_PREFIXES_2016),
        ("2017", REVIT_VERSION_TEXT_PREFIXES_2017),
        ("2018", REVIT_VERSION_TEXT_PREFIXES_2018),
        ("2019", REVIT_VERSION_TEXT_PREFIXES_2019),
        ("2020", REVIT_VERSION_TEXT_PREFIXES_2020),
        ("2021", REVIT_VERSION_TEXT_PREFIXES_2021),
        ("2022", REVIT_VERSION_TEXT_PREFIXES_2022),
        ("2023", REVIT_VERSION_TEXT_PREFIXES_2023),
        ("2024", REVIT_VERSION_TEXT_PREFIXES_2024),
        ("2025", REVIT_VERSION_TEXT_PREFIXES_2025),
        ("2026", REVIT_VERSION_TEXT_PREFIXES_2026),
        ("2027", REVIT_VERSION_TEXT_PREFIXES_2027),
    ]
    for versionNumber, prefixes in VERSION_MAP:
        if StartsWithOneOfPrefixes(revitVersionText, prefixes):
            return versionNumber
    return None
