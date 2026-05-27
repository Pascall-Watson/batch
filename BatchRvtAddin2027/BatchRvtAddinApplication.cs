//
// Revit Batch Processor
//
// Copyright (c) 2027  BVN
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
using System.ComponentModel;
using System.IO;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.UI;
using BatchRvt.ScriptHost;
using WinForms = System.Windows.Forms;

namespace BatchRvt.Addin.Revit2027
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    [DisplayName("BatchRvtAddin")]
    [Description("BatchRvtAddin")]
    public class BatchRvtAddinApplication : IExternalApplication
    {
        // Static keeps the handler alive for the addin's lifetime — without this, .NET 10's GC
        // can reclaim the local before Revit's UI thread pumps the queued ExternalEvent.
        private static BatchRvtExternalEventHandler externalEventHandler_;

        public Result OnStartup(UIControlledApplication uiApplication)
        {
            DiagLog("OnStartup begin");
            try
            {
                SetupBatchScriptHost(uiApplication.ControlledApplication);
                DiagLog("OnStartup: SetupBatchScriptHost returned");
            }
            catch (Exception ex)
            {
                DiagLog($"OnStartup THREW: {ex}");
                throw;
            }
            return Result.Succeeded;
        }

        private static void DiagLog(string msg) => DiagLogPublic(msg);

        internal static void DiagLogPublic(string msg)
        {
            // Try multiple paths — Path.GetTempPath() can return unexpected things in addin context.
            var line = $"[{DateTime.Now:O}] {msg}\n";
            string addinDir = null;
            try { addinDir = Path.GetDirectoryName(typeof(BatchRvtAddinApplication).Assembly.Location); }
            catch { /* */ }

            var candidates = new[]
            {
                addinDir != null ? Path.Combine(addinDir, "batchrvt_addin_diag.log") : null,
                Path.Combine(Path.GetTempPath(), "batchrvt_addin_diag.log"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "batchrvt_addin_diag.log"),
                @"C:\Users\Public\batchrvt_addin_diag.log",
            };
            foreach (var path in candidates)
            {
                if (path == null) continue;
                try { File.AppendAllText(path, line); }
                catch { /* try next */ }
            }
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            return Result.Succeeded;
        }

        private static void SetupBatchScriptHost(ControlledApplication controlledApplication)
        {
            var pluginFolderPath = Path.GetDirectoryName(typeof(BatchRvtAddinApplication).Assembly.Location);
            externalEventHandler_ = new BatchRvtExternalEventHandler(pluginFolderPath);
            externalEventHandler_.Raise();
        }
    }

    public class BatchRvtExternalEventHandler : IExternalEventHandler
    {
        private readonly ExternalEvent externalEvent_;
        private readonly string pluginFolderPath_;

        public BatchRvtExternalEventHandler(string pluginFolderPath)
        {
            externalEvent_ = ExternalEvent.Create(this);
            pluginFolderPath_ = pluginFolderPath;
        }

        public void Execute(UIApplication uiApp)
        {
            BatchRvtAddinApplication.DiagLogPublic("ExternalEventHandler.Execute fired");
            try
            {
                ScriptHostUtil.ExecuteBatchScriptHost(pluginFolderPath_, uiApp, "Scripts34");
            }
            catch (Exception e)
            {
                BatchRvtAddinApplication.DiagLogPublic($"Execute THREW: {e}");
                WinForms.MessageBox.Show(e.ToString(), ScriptHostUtil.BATCH_RVT_ERROR_WINDOW_TITLE);
            }
        }

        public string GetName()
        {
            return "BatchRvt_ExternalEventHandler";
        }

        public ExternalEventRequest Raise()
        {
            return externalEvent_.Raise();
        }
    }
}
