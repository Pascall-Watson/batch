#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

try:
    clr.AddReference("System.Console")
except:
    pass


def WaitForSpaceBarKeyPress():
    while True:
        keyInfo = System.Console.ReadKey(True)
        if keyInfo.Key == System.ConsoleKey.Spacebar:
            break
    return


def IsInputRedirected():
    return System.Console.IsInputRedirected


def ReadLine():
    return System.Console.ReadLine()


def ReadLines():
    lines = []
    line = System.Console.ReadLine()
    while line is not None:
        lines.append(line)
        line = System.Console.ReadLine()
    return lines
