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
#   2. The PyRevit-fallback path resolves `Batch.Shared.Util.dll` from the
#      loaded `Batch.Shared.ScriptHost` assembly location.
#

import clr
import System
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
from System import AppDomain
from System.IO import IOException, Path

BATCH_RVT_UTIL_ASSEMBLY_NAME = "Batch.Shared.Util"
BATCH_RVT_UTIL_ASSEMBLY_FILE_NAME = BATCH_RVT_UTIL_ASSEMBLY_NAME + ".dll"
BATCH_RVT_SCRIPT_HOST_ASSEMBLY_NAME = "Batch.Shared.ScriptHost"


def GetExistingLoadedAssembly(assemblyName):
    return (
        AppDomain.CurrentDomain.GetAssemblies()
        .FirstOrDefault(lambda assembly: assembly.GetName().Name == assemblyName)
    )


def AddBatchSharedUtilAssemblyReference():
    try:
        clr.AddReference(BATCH_RVT_UTIL_ASSEMBLY_NAME)
    except IOException as e:
        # PyRevit-installed fallback.
        batchSharedScriptHostAssembly = GetExistingLoadedAssembly(BATCH_RVT_SCRIPT_HOST_ASSEMBLY_NAME)
        if batchSharedScriptHostAssembly is None:
            raise
        scriptHostFolderPath = Path.GetDirectoryName(batchSharedScriptHostAssembly.Location)
        clr.AddReferenceToFileAndPath(Path.Combine(scriptHostFolderPath, BATCH_RVT_UTIL_ASSEMBLY_FILE_NAME))
    return


AddBatchSharedUtilAssemblyReference()

import Batch.Shared.Util
from Batch.Shared.Util import *
