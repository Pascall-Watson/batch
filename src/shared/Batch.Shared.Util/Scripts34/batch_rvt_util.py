#
# Revit Batch Processor
#
# Copyright (c) 2020  Dan Rumery, BVN
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# IronPython 3.4 port (Phase 2a). Two changes vs 2.7:
#   1. `except IOException, e:` → `as e:`.
#   2. The PyRevit-fallback path calls `ScriptHostUtil.GetEnvironmentVariables`
#      and `GetBatchRvtFolderPath`, which were removed from the modern
#      `BatchRvtScriptHost` (Phase 1 refactor). Inside the addin's host process
#      we never take that branch — but if PyRevit support is ever revived for
#      .NET 10, those C# methods must be restored.
#

import clr
import System
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
from System import AppDomain
from System.IO import IOException, Path

BATCH_RVT_UTIL_ASSEMBLY_NAME = "BatchRvtUtil"
BATCH_RVT_SCRIPT_HOST_ASSEMBLY_NAME = "BatchRvtScriptHost"


def GetExistingLoadedAssembly(assemblyName):
    return (
        AppDomain.CurrentDomain.GetAssemblies()
        .FirstOrDefault(lambda assembly: assembly.GetName().Name == assemblyName)
    )


def AddBatchRvtUtilAssemblyReference():
    try:
        clr.AddReference(BATCH_RVT_UTIL_ASSEMBLY_NAME)
    except IOException as e:
        # PyRevit-installed fallback. Not exercised on .NET 10 (the modern
        # BatchRvtScriptHost no longer exposes GetEnvironmentVariables /
        # GetBatchRvtFolderPath). Kept here as a reminder for if/when that
        # fallback is wanted again.
        batchRvtScriptHostAssembly = GetExistingLoadedAssembly(BATCH_RVT_SCRIPT_HOST_ASSEMBLY_NAME)
        clr.AddReference(batchRvtScriptHostAssembly)
        from BatchRvt.ScriptHost import ScriptHostUtil
        environmentVariables = ScriptHostUtil.GetEnvironmentVariables()
        batchRvtFolderPath = ScriptHostUtil.GetBatchRvtFolderPath(environmentVariables)
        clr.AddReferenceToFileAndPath(Path.Combine(batchRvtFolderPath, BATCH_RVT_UTIL_ASSEMBLY_NAME))
    return


AddBatchRvtUtilAssemblyReference()

import BatchRvtUtil
from BatchRvtUtil import *
