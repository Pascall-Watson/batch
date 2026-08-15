using System;
using System.Runtime.InteropServices;
using Batch.Shared.Util;
using Microsoft.UI.Xaml;

namespace Batch.App.Ui;

public class App : Application
{
    private Window? _window;

    public App()
    {
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        if (!BatchUiPreflight.HasAnyInstalledBatchRvtAddin())
        {
            ShowErrorMessageBox(BatchUiPreflight.BuildMissingAddinErrorMessage());
            Exit();
            return;
        }

        _window = new MainWindow();
        _window.Activate();
    }

    private static void ShowErrorMessageBox(string message)
    {
        const uint MB_OK = 0x00000000;
        const uint MB_ICONERROR = 0x00000010;

        MessageBox(IntPtr.Zero, message, BatchUiPreflight.WindowTitle, MB_OK | MB_ICONERROR);
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(IntPtr hWnd, string lpText, string lpCaption, uint uType);
}
