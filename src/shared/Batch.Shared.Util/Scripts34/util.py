#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System
from System.IO import StringReader


def Try(f):
    result = None
    try:
        result = f()
    except:
        result = None
    return result


def FindAllIndicesOf(text, value):
    indices = []
    index = text.IndexOf(value)
    while index != -1:
        indices.append(index)
        index = text.IndexOf(value, index + 1)
    return indices


def ReadLinesFromText(text):
    lines = []
    with StringReader(text) as reader:
        line = reader.ReadLine()
        while line is not None:
            lines.append(line)
            line = reader.ReadLine()
    return lines
