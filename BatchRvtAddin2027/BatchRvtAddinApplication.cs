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
            SetupBatchScriptHost(uiApplication.ControlledApplication);
            return Result.Succeeded;
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
            try
            {
                ScriptHostUtil.ExecuteBatchScriptHost(pluginFolderPath_, uiApp, "Scripts34");
            }
            catch (Exception e)
            {
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
