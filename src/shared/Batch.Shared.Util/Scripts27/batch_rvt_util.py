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
    except IOException, e: # Can occur if PyRevit is installed. Need to use AddReferenceToFileAndPath() in this case.
        # Resolve the utility assembly by file path from the loaded script-host assembly location.
        batchSharedScriptHostAssembly = GetExistingLoadedAssembly(BATCH_RVT_SCRIPT_HOST_ASSEMBLY_NAME)
        if batchSharedScriptHostAssembly is None:
            raise
        scriptHostFolderPath = Path.GetDirectoryName(batchSharedScriptHostAssembly.Location)
        clr.AddReferenceToFileAndPath(Path.Combine(scriptHostFolderPath, BATCH_RVT_UTIL_ASSEMBLY_FILE_NAME))
    return

AddBatchSharedUtilAssemblyReference()

import Batch.Shared.Util
from Batch.Shared.Util import *

