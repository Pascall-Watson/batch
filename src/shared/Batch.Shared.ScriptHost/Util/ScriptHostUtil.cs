//
// Revit Batch Processor
//
// Copyright (c) 2020  Daniel Rumery, BVN
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//

using System;
using System.Collections.Generic;
using System.IO;

namespace BatchRvt.ScriptHost;

public static class ScriptHostUtil
{
    // NOTE: must be the same as BATCH_RVT_ERROR_WINDOW_TITLE defined in script_host_error.py.
    public const string BATCH_RVT_ERROR_WINDOW_TITLE = "BatchRvt Script Error";

    private const string BatchScriptHostFilename = "revit_script_host.py";

    // Presence of this env var (set by the outer BatchRvt orchestrator) indicates that
    // this addin load is part of a batch session. Without it, we early-exit so a plain
    // Revit startup doesn't spin up the IronPython engine for nothing.
    private const string ORCHESTRATION_MARKER_ENV_VAR = "BATCHRVT__SCRIPT_FILE_PATH";

    public static void ExecuteBatchScriptHost(
        string pluginFolderPath,
        object uiApplicationObject,
        string scriptsFolderName
    )
    {
        if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable(ORCHESTRATION_MARKER_ENV_VAR)))
            return;

        var pluginFullFolderPath = Path.GetFullPath(pluginFolderPath);
        var batchRvtScriptsFolderPath = Path.Combine(pluginFullFolderPath, scriptsFolderName);
        var scriptHostFilePath = Path.Combine(batchRvtScriptsFolderPath, BatchScriptHostFilename);

        var engine = ScriptUtil.CreatePythonEngine();

        ScriptUtil.AddBuiltinVariables(
            engine,
            new Dictionary<string, object>
            {
                { "__revit__", uiApplicationObject },
            });

        var mainModuleScope = ScriptUtil.CreateMainModule(engine);

        ScriptUtil.AddSearchPaths(engine, new[]
        {
            batchRvtScriptsFolderPath,
            pluginFullFolderPath
        });

        ScriptUtil.AddPythonStandardLibrary(mainModuleScope);

        var scriptSource = ScriptUtil.CreateScriptSourceFromFile(engine, scriptHostFilePath);

        scriptSource.Execute(mainModuleScope);
    }
}
