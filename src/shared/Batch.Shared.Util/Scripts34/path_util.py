#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes: `except X, e:` → `as e:` across the file.
#

import clr
import System
from System import Environment, ArgumentException, StringComparison, Char
import System.IO
from System.IO import Path, File, Directory, FileInfo, DirectoryInfo, PathTooLongException

import win32_mpr

import sys


def AddSearchPath(searchPath):
    # TODO: only add the path if it's not already added.
    sys.path.append(searchPath)
    return


def GetUserDesktopFolderPath():
    return Environment.GetFolderPath(Environment.SpecialFolder.Desktop)


def GetLocalAppDataFolderPath():
    return Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData)


def GetFileExtension(filePath):
    return Path.GetExtension(filePath)


def HasFileExtension(filePath, extension):
    return GetFileExtension(filePath).ToLower() == extension.ToLower()


def FileExists(filePath):
    return File.Exists(filePath)


def GetFullPath(path):
    return Path.GetFullPath(path)


def DirectoryExists(folderPath):
    return Directory.Exists(folderPath)


def CreateDirectory(folderPath):
    directoryInfo = Directory.CreateDirectory(folderPath)
    return directoryInfo


def CreateDirectoryForFilePath(filePath):
    directoryInfo = CreateDirectory(Path.GetDirectoryName(filePath))
    return directoryInfo


def GetFileSize(filePath):
    fileSize = None
    try:
        fileSize = FileInfo(filePath).Length
    except Exception:
        pass
    return fileSize


def GetLastWriteTimeUtc(filePath):
    lastWriteTime = None
    try:
        lastWriteTime = File.GetLastWriteTimeUtc(filePath)
    except Exception:
        pass
    return lastWriteTime


def GetDriveLetter(path):
    driveLetter = Path.GetPathRoot(path).Split(":")[0]
    return driveLetter.ToUpper() if len(driveLetter) == 1 else None


def GetDriveRemoteName(path):
    driveRemoteName = None
    driveLetter = GetDriveLetter(path)
    if driveLetter is not None:
        driveRemoteName = win32_mpr.WNetGetConnection(driveLetter + ":")
    return driveRemoteName


def GetFullNetworkPath(path):
    fullNetworkPath = None
    try:
        if not Path.IsPathRooted(path):
            raise ArgumentException("A full file path must be specified.", "path")
        pathRoot = Path.GetPathRoot(path)
        driveRemoteName = GetDriveRemoteName(pathRoot)
        if driveRemoteName is not None:
            pathWithoutRoot = path.Substring(pathRoot.Length)
            fullNetworkPath = Path.Combine(driveRemoteName, pathWithoutRoot)
    except PathTooLongException:
        fullNetworkPath = None
    return fullNetworkPath


def ExpandedFullNetworkPath(path):
    expandedPath = GetFullNetworkPath(path)
    if expandedPath is None:
        expandedPath = path
    return expandedPath


def DirectoryHasName(directoryInfo, name):
    return str.Equals(directoryInfo.Name, name, StringComparison.OrdinalIgnoreCase)


def GetDirectoryParts(folderPath):
    parts = []
    current = DirectoryInfo(folderPath)
    while current is not None:
        parts.insert(0, current.Name)
        current = current.Parent
    return parts


def IsProjectYearFolderName(folderName):
    return (
        len(folderName) == 2
        and Char.IsDigit(folderName[0])
        and Char.IsDigit(folderName[1])
    )


def GetProjectFolderNameFromRevitProjectFilePath(revitProjectFilePath):
    projectFolderName = None
    # Path.GetDirectoryName() before expanding (rather than after) to reduce the
    # risk of hitting .NET's path length limit.
    folderPath = ExpandedFullNetworkPath(Path.GetDirectoryName(revitProjectFilePath))
    parts = GetDirectoryParts(folderPath)
    numberOfParts = len(parts)
    if numberOfParts > 2:
        if IsProjectYearFolderName(parts[1]):
            projectFolderName = parts[2]
    return projectFolderName
