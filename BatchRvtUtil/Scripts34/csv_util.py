#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

from System.Text import Encoding
from System.IO import File
import path_util

CSV_FILE_EXTENSION = ".csv"


def ReadAllLines(filePath):
    lines = File.ReadAllLines(filePath)
    if len(lines) > 0:
        # Workaround for a potential lack of detection of Unicode txt files.
        if lines[0].Contains("\x00"):
            lines = File.ReadAllLines(filePath, Encoding.Unicode)
    return lines


def GetRowsFromLines(lines):
    return [line.split(',') for line in lines]


def WriteToCSVFile(rows, csvFilePath, delimiter, encoding):
    lines = [str.Join(delimiter, [str(value) for value in row]) for row in rows]
    File.WriteAllLines(csvFilePath, lines, encoding)
    return


def WriteToTabDelimitedTxtFile(rows, txtFilePath, encoding=Encoding.UTF8):
    WriteToCSVFile(rows, txtFilePath, "\t", encoding)
    return


def HasCSVFileExtension(filePath):
    return path_util.HasFileExtension(filePath, CSV_FILE_EXTENSION)


def GetRowsFromCSVFile(csvFilePath):
    lines = ReadAllLines(csvFilePath)
    return GetRowsFromLines(lines)
