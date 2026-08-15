using System;
using System.Threading;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using WinRT;

namespace Batch.App.Ui;

public static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        ComWrappersSupport.InitializeComWrappers();

        Application.Start(_ =>
        {
            var dispatcherQueue = DispatcherQueue.GetForCurrentThread();
            SynchronizationContext.SetSynchronizationContext(
                new DispatcherQueueSynchronizationContext(dispatcherQueue));

            var app = new App();
        });
    }
}
