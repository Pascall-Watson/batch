using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;
using Microsoft.UI;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace Batch.App.Ui;

public sealed class MainWindow : Window
{
    private const string DEFAULT_SETTINGS_FILENAME = "BatchRvtGui.Settings.json";

    private readonly StringBuilder _outputBuilder = new();

    private readonly TextBox _settingsPathTextBox = new();
    private readonly TextBox _logFolderPathTextBox = new();
    private readonly Button _startButton = new();
    private readonly Button _stopButton = new();
    private readonly TextBlock _taskScriptValueTextBlock = new();
    private readonly TextBlock _revitFileListValueTextBlock = new();
    private readonly TextBlock _processingModeValueTextBlock = new();
    private readonly TextBlock _batchRevitVersionValueTextBlock = new();
    private readonly TextBlock _revitSessionModeValueTextBlock = new();
    private readonly TextBox _settingsJsonTextBox = new();
    private readonly TextBox _outputTextBox = new();
    private readonly TextBlock _statusTextBlock = new();

    private Process? _batchRvtProcess;
    private string _settingsFilePath = GetDefaultSettingsFilePath();
    private bool _showRevitProcessErrorMessages;

    public MainWindow()
    {
        Title = "Revit Batch Processor - WinUI Shell";
        Content = BuildContent();

        Closed += MainWindow_Closed;

        _settingsPathTextBox.Text = _settingsFilePath;
        _stopButton.IsEnabled = false;

        LoadCurrentSettings();
    }

    private UIElement BuildContent()
    {
        var rootGrid = new Grid
        {
            Padding = new Thickness(16),
            RowSpacing = 12
        };

        rootGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        rootGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        rootGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        rootGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        rootGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

        var headerTextBlock = new TextBlock
        {
            Text = "Revit Batch Processor (WinUI Shell)",
            FontSize = 22,
            FontWeight = FontWeights.SemiBold
        };
        rootGrid.Children.Add(headerTextBlock);

        var settingsRowGrid = new Grid
        {
            ColumnSpacing = 8
        };
        settingsRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(150) });
        settingsRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        settingsRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        settingsRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        settingsRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        settingsRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        Grid.SetRow(settingsRowGrid, 1);

        var settingsLabel = new TextBlock
        {
            Text = "Settings file",
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(settingsLabel, 0);
        settingsRowGrid.Children.Add(settingsLabel);

        _settingsPathTextBox.PlaceholderText = "Path to BatchRvt settings JSON";
        Grid.SetColumn(_settingsPathTextBox, 1);
        settingsRowGrid.Children.Add(_settingsPathTextBox);

        var browseSettingsButton = new Button { Content = "Browse", Margin = new Thickness(8, 0, 0, 0) };
        browseSettingsButton.Click += BrowseSettingsFileButton_Click;
        Grid.SetColumn(browseSettingsButton, 2);
        settingsRowGrid.Children.Add(browseSettingsButton);

        var loadSettingsButton = new Button { Content = "Load", Margin = new Thickness(8, 0, 0, 0) };
        loadSettingsButton.Click += LoadSettingsButton_Click;
        Grid.SetColumn(loadSettingsButton, 3);
        settingsRowGrid.Children.Add(loadSettingsButton);

        var saveSettingsButton = new Button { Content = "Save", Margin = new Thickness(8, 0, 0, 0) };
        saveSettingsButton.Click += SaveSettingsButton_Click;
        Grid.SetColumn(saveSettingsButton, 4);
        settingsRowGrid.Children.Add(saveSettingsButton);

        var saveSettingsAsButton = new Button { Content = "Save As", Margin = new Thickness(8, 0, 0, 0) };
        saveSettingsAsButton.Click += SaveSettingsAsButton_Click;
        Grid.SetColumn(saveSettingsAsButton, 5);
        settingsRowGrid.Children.Add(saveSettingsAsButton);

        rootGrid.Children.Add(settingsRowGrid);

        var logRowGrid = new Grid
        {
            ColumnSpacing = 8
        };
        logRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(150) });
        logRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        logRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        logRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        logRowGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        Grid.SetRow(logRowGrid, 2);

        var logLabel = new TextBlock
        {
            Text = "Log folder",
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(logLabel, 0);
        logRowGrid.Children.Add(logLabel);

        _logFolderPathTextBox.PlaceholderText = "Optional log folder path";
        Grid.SetColumn(_logFolderPathTextBox, 1);
        logRowGrid.Children.Add(_logFolderPathTextBox);

        var browseLogButton = new Button { Content = "Browse", Margin = new Thickness(8, 0, 0, 0) };
        browseLogButton.Click += BrowseLogFolderButton_Click;
        Grid.SetColumn(browseLogButton, 2);
        logRowGrid.Children.Add(browseLogButton);

        _startButton.Content = "Start";
        _startButton.Margin = new Thickness(8, 0, 0, 0);
        _startButton.Click += StartButton_Click;
        Grid.SetColumn(_startButton, 3);
        logRowGrid.Children.Add(_startButton);

        _stopButton.Content = "Stop";
        _stopButton.Margin = new Thickness(8, 0, 0, 0);
        _stopButton.Click += StopButton_Click;
        Grid.SetColumn(_stopButton, 4);
        logRowGrid.Children.Add(_stopButton);

        rootGrid.Children.Add(logRowGrid);

        var contentGrid = new Grid
        {
            ColumnSpacing = 12
        };
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(420) });
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        Grid.SetRow(contentGrid, 3);

        var summaryBorder = new Border
        {
            Padding = new Thickness(12),
            BorderThickness = new Thickness(1),
            BorderBrush = new SolidColorBrush(Colors.Gray),
            CornerRadius = new CornerRadius(8)
        };
        Grid.SetColumn(summaryBorder, 0);

        var summaryStack = new StackPanel
        {
            Spacing = 8
        };

        summaryStack.Children.Add(new TextBlock { Text = "Loaded Settings Summary", FontSize = 16, FontWeight = FontWeights.SemiBold });
        summaryStack.Children.Add(new TextBlock { Text = "Task script", FontWeight = FontWeights.SemiBold });
        _taskScriptValueTextBlock.TextWrapping = TextWrapping.WrapWholeWords;
        summaryStack.Children.Add(_taskScriptValueTextBlock);

        summaryStack.Children.Add(new TextBlock { Text = "Revit file list", FontWeight = FontWeights.SemiBold });
        _revitFileListValueTextBlock.TextWrapping = TextWrapping.WrapWholeWords;
        summaryStack.Children.Add(_revitFileListValueTextBlock);

        summaryStack.Children.Add(new TextBlock { Text = "Processing mode", FontWeight = FontWeights.SemiBold });
        summaryStack.Children.Add(_processingModeValueTextBlock);

        summaryStack.Children.Add(new TextBlock { Text = "Batch Revit version", FontWeight = FontWeights.SemiBold });
        summaryStack.Children.Add(_batchRevitVersionValueTextBlock);

        summaryStack.Children.Add(new TextBlock { Text = "Revit session mode", FontWeight = FontWeights.SemiBold });
        summaryStack.Children.Add(_revitSessionModeValueTextBlock);

        summaryStack.Children.Add(new TextBlock { Text = "Settings JSON", FontWeight = FontWeights.SemiBold });
        _settingsJsonTextBox.AcceptsReturn = true;
        _settingsJsonTextBox.TextWrapping = TextWrapping.NoWrap;
        ScrollViewer.SetVerticalScrollBarVisibility(_settingsJsonTextBox, ScrollBarVisibility.Auto);
        ScrollViewer.SetHorizontalScrollBarVisibility(_settingsJsonTextBox, ScrollBarVisibility.Auto);
        _settingsJsonTextBox.FontFamily = new FontFamily("Consolas");
        _settingsJsonTextBox.Height = 300;
        summaryStack.Children.Add(_settingsJsonTextBox);

        summaryBorder.Child = summaryStack;
        contentGrid.Children.Add(summaryBorder);

        var outputBorder = new Border
        {
            Padding = new Thickness(12),
            BorderThickness = new Thickness(1),
            BorderBrush = new SolidColorBrush(Colors.Gray),
            CornerRadius = new CornerRadius(8)
        };
        Grid.SetColumn(outputBorder, 1);

        var outputGrid = new Grid
        {
            RowSpacing = 8
        };
        outputGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        outputGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

        outputGrid.Children.Add(new TextBlock { Text = "Batch Output", FontSize = 16, FontWeight = FontWeights.SemiBold });

        _outputTextBox.IsReadOnly = true;
        _outputTextBox.AcceptsReturn = true;
        _outputTextBox.TextWrapping = TextWrapping.NoWrap;
        ScrollViewer.SetVerticalScrollBarVisibility(_outputTextBox, ScrollBarVisibility.Auto);
        ScrollViewer.SetHorizontalScrollBarVisibility(_outputTextBox, ScrollBarVisibility.Auto);
        _outputTextBox.FontFamily = new FontFamily("Consolas");
        Grid.SetRow(_outputTextBox, 1);
        outputGrid.Children.Add(_outputTextBox);

        outputBorder.Child = outputGrid;
        contentGrid.Children.Add(outputBorder);

        rootGrid.Children.Add(contentGrid);

        _statusTextBlock.TextWrapping = TextWrapping.WrapWholeWords;
        Grid.SetRow(_statusTextBlock, 4);
        rootGrid.Children.Add(_statusTextBlock);

        return rootGrid;
    }

    private static string GetDefaultSettingsFilePath()
    {
        return Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "BatchRvt",
            DEFAULT_SETTINGS_FILENAME);
    }

    private void MainWindow_Closed(object sender, WindowEventArgs args)
    {
        StopRunningProcess(silent: true);
    }

    private async void BrowseSettingsFileButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = InitializePickerWithWindow(new FileOpenPicker());
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add(".json");

        var selectedFile = await picker.PickSingleFileAsync();
        if (selectedFile == null)
            return;

        _settingsPathTextBox.Text = selectedFile.Path;
        SetStatus("Selected settings file path.");
    }

    private async void BrowseLogFolderButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = InitializePickerWithWindow(new FolderPicker());
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add("*");

        var selectedFolder = await picker.PickSingleFolderAsync();
        if (selectedFolder == null)
            return;

        _logFolderPathTextBox.Text = selectedFolder.Path;
        SetStatus("Selected log folder path.");
    }

    private void LoadSettingsButton_Click(object sender, RoutedEventArgs e)
    {
        if (!TryApplySettingsPath())
            return;

        LoadCurrentSettings();
    }

    private void SaveSettingsButton_Click(object sender, RoutedEventArgs e)
    {
        if (!TryApplySettingsPath())
            return;

        SaveCurrentSettings();
    }

    private async void SaveSettingsAsButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = InitializePickerWithWindow(new FileSavePicker());
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.SuggestedFileName = string.IsNullOrWhiteSpace(_settingsFilePath)
            ? DEFAULT_SETTINGS_FILENAME
            : Path.GetFileName(_settingsFilePath);
        picker.FileTypeChoices.Add("JSON files", new List<string> { ".json" });

        var selectedFile = await picker.PickSaveFileAsync();
        if (selectedFile == null)
            return;

        _settingsFilePath = selectedFile.Path;
        _settingsPathTextBox.Text = _settingsFilePath;

        SaveCurrentSettings();
    }

    private void StartButton_Click(object sender, RoutedEventArgs e)
    {
        if (_batchRvtProcess is { HasExited: false })
            return;

        if (!TryApplySettingsPath())
            return;

        if (!File.Exists(_settingsFilePath))
        {
            SetStatus("Cannot start batch run. Settings file does not exist.");
            return;
        }

        var logFolderPath = NormalizePathOrEmpty(_logFolderPathTextBox.Text);
        if (!string.IsNullOrWhiteSpace(logFolderPath))
            Directory.CreateDirectory(logFolderPath);

        var executablePath = ResolveBatchExecutablePath(out var checkedPaths);
        if (string.IsNullOrWhiteSpace(executablePath))
        {
            AppendOutputLine("[ERROR] Could not find Batch launcher executable.");
            foreach (var checkedPath in checkedPaths)
                AppendOutputLine("Checked: " + checkedPath);
            SetStatus("Batch launcher executable was not found.");
            return;
        }

        var arguments = new StringBuilder();
        arguments.Append("--settings_file ").Append(QuoteArgument(_settingsFilePath));
        if (!string.IsNullOrWhiteSpace(logFolderPath))
            arguments.Append(" --log_folder ").Append(QuoteArgument(logFolderPath));

        try
        {
            var psi = new ProcessStartInfo(executablePath)
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                RedirectStandardInput = false,
                CreateNoWindow = true,
                Arguments = arguments.ToString(),
                WorkingDirectory = Path.GetDirectoryName(executablePath) ?? AppContext.BaseDirectory
            };

            _batchRvtProcess = Process.Start(psi);
            if (_batchRvtProcess == null)
                throw new InvalidOperationException("Process start returned null.");
        }
        catch (Exception ex)
        {
            AppendOutputLine("[ERROR] Failed to start batch process.");
            AppendOutputLine(ex.Message);
            SetStatus("Failed to start batch process.");
            return;
        }

        _batchRvtProcess.EnableRaisingEvents = true;
        _batchRvtProcess.Exited += BatchRvtProcess_Exited;
        _batchRvtProcess.OutputDataReceived += BatchRvtProcess_OutputDataReceived;
        _batchRvtProcess.ErrorDataReceived += BatchRvtProcess_ErrorDataReceived;
        _batchRvtProcess.BeginOutputReadLine();
        _batchRvtProcess.BeginErrorReadLine();

        _startButton.IsEnabled = false;
        _stopButton.IsEnabled = true;

        SetStatus("Batch process started.");
    }

    private void StopButton_Click(object sender, RoutedEventArgs e)
    {
        StopRunningProcess(silent: false);
    }

    private void BatchRvtProcess_OutputDataReceived(object sender, DataReceivedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(e.Data))
            return;

        var line = e.Data;
        if (IsBatchRvtLine(line))
        {
            AppendOutputLine(line);
            return;
        }

        var stampedLine = DateTime.Now.ToString("HH:mm:ss") + " : [ REVIT MESSAGE ] : " + line;
        AppendOutputLine(stampedLine);
    }

    private void BatchRvtProcess_ErrorDataReceived(object sender, DataReceivedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(e.Data))
            return;

        if (e.Data.StartsWith("log4cplus:", StringComparison.OrdinalIgnoreCase))
            return;

        if (!_showRevitProcessErrorMessages)
            return;

        AppendOutputLine("[ REVIT ERROR MESSAGE ] : " + e.Data);
    }

    private void BatchRvtProcess_Exited(object? sender, EventArgs e)
    {
        DispatcherQueue.TryEnqueue(() =>
        {
            _startButton.IsEnabled = true;
            _stopButton.IsEnabled = false;
            _batchRvtProcess = null;
            SetStatus("Batch process exited.");
        });
    }

    private void StopRunningProcess(bool silent)
    {
        if (_batchRvtProcess is null)
            return;

        try
        {
            if (!_batchRvtProcess.HasExited)
                _batchRvtProcess.Kill(true);
        }
        catch (Exception ex)
        {
            if (!silent)
                AppendOutputLine("[ERROR] Failed to stop batch process: " + ex.Message);
        }
        finally
        {
            _startButton.IsEnabled = true;
            _stopButton.IsEnabled = false;
        }

        if (!silent)
            SetStatus("Batch process stop requested.");
    }

    private bool TryApplySettingsPath()
    {
        var normalizedPath = NormalizePathOrEmpty(_settingsPathTextBox.Text);
        if (string.IsNullOrWhiteSpace(normalizedPath))
        {
            SetStatus("Settings file path is required.");
            return false;
        }

        _settingsFilePath = normalizedPath;
        _settingsPathTextBox.Text = _settingsFilePath;

        return true;
    }

    private void LoadCurrentSettings()
    {
        if (!File.Exists(_settingsFilePath))
        {
            _settingsJsonTextBox.Text = "{}";
            UpdateSummaryFromJson(_settingsJsonTextBox.Text);
            SetStatus("Settings file was not found. Loaded an empty JSON document.");
            return;
        }

        try
        {
            var settingsJson = File.ReadAllText(_settingsFilePath);
            _settingsJsonTextBox.Text = settingsJson;
            UpdateSummaryFromJson(settingsJson);
            SetStatus("Settings loaded.");
        }
        catch (Exception ex)
        {
            AppendOutputLine("[ERROR] Failed to load settings: " + ex.Message);
            SetStatus("Settings load failed.");
        }
    }

    private void SaveCurrentSettings()
    {
        var settingsJson = _settingsJsonTextBox.Text;
        if (string.IsNullOrWhiteSpace(settingsJson))
            settingsJson = "{}";

        try
        {
            using var _ = JsonDocument.Parse(settingsJson);

            var directoryPath = Path.GetDirectoryName(_settingsFilePath);
            if (!string.IsNullOrWhiteSpace(directoryPath))
                Directory.CreateDirectory(directoryPath);

            File.WriteAllText(_settingsFilePath, settingsJson);
            UpdateSummaryFromJson(settingsJson);
            SetStatus("Settings saved.");
        }
        catch (Exception ex)
        {
            AppendOutputLine("[ERROR] Failed to save settings: " + ex.Message);
            SetStatus("Settings save failed.");
        }
    }

    private void UpdateSummaryFromJson(string settingsJson)
    {
        try
        {
            using var document = JsonDocument.Parse(settingsJson);
            var root = document.RootElement;

            _taskScriptValueTextBlock.Text = DisplayValueOrDefault(ReadJsonString(root, "taskScriptFilePath"));
            _revitFileListValueTextBlock.Text = DisplayValueOrDefault(ReadJsonString(root, "revitFileListFilePath"));
            _processingModeValueTextBlock.Text = DisplayValueOrDefault(ReadJsonString(root, "revitProcessingOption"));
            _batchRevitVersionValueTextBlock.Text = DisplayValueOrDefault(ReadJsonString(root, "batchRevitTaskRevitVersion"));
            _revitSessionModeValueTextBlock.Text = DisplayValueOrDefault(ReadJsonString(root, "revitSessionOption"));

            _showRevitProcessErrorMessages = ReadJsonBoolean(root, "showRevitProcessErrorMessages");
        }
        catch
        {
            _taskScriptValueTextBlock.Text = "(invalid json)";
            _revitFileListValueTextBlock.Text = "(invalid json)";
            _processingModeValueTextBlock.Text = "(invalid json)";
            _batchRevitVersionValueTextBlock.Text = "(invalid json)";
            _revitSessionModeValueTextBlock.Text = "(invalid json)";
            _showRevitProcessErrorMessages = false;
        }
    }

    private static string ReadJsonString(JsonElement root, string propertyName)
    {
        if (root.ValueKind != JsonValueKind.Object)
            return string.Empty;

        if (!root.TryGetProperty(propertyName, out var value))
            return string.Empty;

        if (value.ValueKind == JsonValueKind.String)
            return value.GetString() ?? string.Empty;

        if (value.ValueKind == JsonValueKind.Null)
            return string.Empty;

        return value.ToString();
    }

    private static bool ReadJsonBoolean(JsonElement root, string propertyName)
    {
        if (root.ValueKind != JsonValueKind.Object)
            return false;

        if (!root.TryGetProperty(propertyName, out var value))
            return false;

        if (value.ValueKind == JsonValueKind.True)
            return true;

        if (value.ValueKind == JsonValueKind.False)
            return false;

        if (value.ValueKind == JsonValueKind.String && bool.TryParse(value.GetString(), out var parsed))
            return parsed;

        return false;
    }

    private void AppendOutputLine(string line)
    {
        DispatcherQueue.TryEnqueue(DispatcherQueuePriority.Low, () =>
        {
            _outputBuilder.AppendLine(line);
            _outputTextBox.Text = _outputBuilder.ToString();
            _outputTextBox.SelectionStart = _outputTextBox.Text.Length;
        });
    }

    private static string DisplayValueOrDefault(string? value)
    {
        return string.IsNullOrWhiteSpace(value) ? "(not set)" : value;
    }

    private void SetStatus(string message)
    {
        _statusTextBlock.Text = DateTime.Now.ToString("HH:mm:ss") + "  " + message;
    }

    private static string NormalizePathOrEmpty(string? path)
    {
        if (string.IsNullOrWhiteSpace(path))
            return string.Empty;

        var expandedPath = Environment.ExpandEnvironmentVariables(path.Trim());

        try
        {
            return Path.GetFullPath(expandedPath);
        }
        catch
        {
            return expandedPath;
        }
    }

    private static string QuoteArgument(string argument)
    {
        return "\"" + argument.Replace("\"", "\\\"") + "\"";
    }

    private static bool IsBatchRvtLine(string line)
    {
        if (string.IsNullOrWhiteSpace(line))
            return false;

        var parts = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length == 0)
            return false;

        return TimeSpan.TryParseExact(parts[0], @"hh\:mm\:ss", CultureInfo.InvariantCulture, out _);
    }

    private static string ResolveBatchExecutablePath(out string[] checkedPaths)
    {
        var baseDirectory = AppContext.BaseDirectory;
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);

        checkedPaths = new[]
        {
            Path.Combine(baseDirectory, "Batch.App.Cli.exe"),
            Path.Combine(baseDirectory, "BatchRvt.exe"),
            Path.Combine(localAppData, "RevitBatchProcessor", "Batch.App.Cli.exe"),
            Path.Combine(localAppData, "RevitBatchProcessor", "BatchRvt.exe")
        };

        foreach (var checkedPath in checkedPaths)
            if (File.Exists(checkedPath))
                return checkedPath;

        return string.Empty;
    }

    private TPicker InitializePickerWithWindow<TPicker>(TPicker picker)
        where TPicker : class
    {
        var windowHandle = WindowNative.GetWindowHandle(this);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, windowHandle);
        return picker;
    }
}
