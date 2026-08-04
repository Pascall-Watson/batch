#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

try:
    clr.AddReference("System.Diagnostics.Process")
except:
    pass

import batch_rvt_util
from batch_rvt_util import RevitVersion


def StartRevitProcess(revitVersion, initEnvironmentVariables):
    revitExecutableFilePath = RevitVersion.GetRevitExecutableFilePath(revitVersion)
    psi = System.Diagnostics.ProcessStartInfo(revitExecutableFilePath)
    psi.UseShellExecute = False
    psi.RedirectStandardError = True
    psi.RedirectStandardOutput = True
    psi.WorkingDirectory = RevitVersion.GetRevitExecutableFolderPath(revitVersion)
    initEnvironmentVariables(psi.EnvironmentVariables)
    psi.EnvironmentVariables["RVT_ORIGIN"] = "RBP"
    return System.Diagnostics.Process.Start(psi)
