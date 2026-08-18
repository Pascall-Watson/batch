using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Batch.Shared.Util;
using Microsoft.UI.Xaml;

namespace Batch.App.Ui;

public sealed partial class App : Application
{
    private const string WINUI_SHELL_LOG_FILENAME = "WinUiShell.log";

    private Window? _window;

    public App()
    {
        InitializeComponent();
        RequestedTheme = ApplicationTheme.Light;
        UnhandledException += App_UnhandledException;
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        try
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
        catch (Exception ex)
        {
            LogShellFailure("OnLaunched", ex.ToString());
            ShowErrorMessageBox(
                "ERROR: The WinUI shell failed to start. See WinUiShell.log for details."
                + Environment.NewLine + Environment.NewLine
                + ex.Message
            );
            Exit();
        }
    }

    private void App_UnhandledException(object sender, Microsoft.UI.Xaml.UnhandledExceptionEventArgs e)
    {
        var errorMessage = e.Exception?.ToString() ?? e.Message;
        LogShellFailure("UnhandledException", errorMessage);

        ShowErrorMessageBox(
            "ERROR: An unexpected WinUI shell error occurred. See WinUiShell.log for details."
            + Environment.NewLine + Environment.NewLine
            + e.Message
        );

        e.Handled = true;
        Exit();
    }

    private static void LogShellFailure(string source, string details)
    {
        try
        {
            var logFolderPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "BatchRvt");
            Directory.CreateDirectory(logFolderPath);

            var logFilePath = Path.Combine(logFolderPath, WINUI_SHELL_LOG_FILENAME);
            var content = new StringBuilder();
            content.AppendLine("=== WinUI shell failure ===");
            content.AppendLine("Time: " + DateTime.Now.ToString("O"));
            content.AppendLine("Source: " + source);
            content.AppendLine("Details:");
            content.AppendLine(details);
            content.AppendLine();

            File.AppendAllText(logFilePath, content.ToString());
        }
        catch
        {
            // Avoid throwing from exception logging paths.
        }
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
