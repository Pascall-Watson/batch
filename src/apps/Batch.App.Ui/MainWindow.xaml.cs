using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Batch.Shared.Util;
using Microsoft.UI;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Text;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace Batch.App.Ui;

public sealed class MainWindow : Window
{
    private const uint MB_YESNOCANCEL = 0x00000003;
    private const uint MB_YESNO = 0x00000004;
    private const uint MB_ICONQUESTION = 0x00000020;
    private const uint MB_ICONASTERISK = 0x00000040;
    private const uint MB_DEFBUTTON1 = 0x00000000;
    private const uint MB_DEFBUTTON3 = 0x00000200;

    private const int IDYES = 6;
    private const int IDNO = 7;
    private const int IDCANCEL = 2;

    private enum RunUiState
    {
        Ready,
        Running,
        StopRequested,
        Completed
    }

    private readonly StringBuilder _outputBuilder = new();
    private readonly IBatchSettingsWorkflowService _settingsWorkflowService = new BatchSettingsWorkflowService();
    private readonly IBatchRunValidationService _runValidationService = new BatchRunValidationService();
    private readonly IBatchOutputPolicy _outputPolicy = new BatchOutputPolicy();
    private readonly IBatchRunService _runService = new BatchRunService();

    private readonly TextBox _settingsPathTextBox = new();
    private readonly TextBox _logFolderPathTextBox = new();
    private readonly Button _startButton = new();
    private readonly Button _stopButton = new();
    private readonly TextBlock _taskScriptValueTextBlock = new();
    private readonly TextBlock _revitFileListValueTextBlock = new();
    private readonly TextBlock _processingModeValueTextBlock = new();
    private readonly TextBlock _batchRevitVersionValueTextBlock = new();
    private readonly TextBlock _revitSessionModeValueTextBlock = new();
    private readonly TextBox _taskScriptEditorTextBox = new();
    private readonly TextBox _revitFileListEditorTextBox = new();
    private readonly ComboBox _processingModeEditorComboBox = new();
    private readonly TextBox _settingsJsonTextBox = new();
    private readonly TextBox _outputTextBox = new();
    private readonly TextBlock _statusTextBlock = new();

    private BatchRvtSettings _settings = new();
    private Process? _batchRvtProcess;
    private string _settingsFilePath = BatchRvtSettings.GetDefaultSettingsFilePath();
    private bool _skipProcessTerminationOnClose;

    public MainWindow()
    {
        Title = "Revit Batch Processor - WinUI Shell";
        Content = BuildContent();

        Closed += MainWindow_Closed;
        AppWindow.Closing += AppWindow_Closing;

        _settingsPathTextBox.Text = _settingsFilePath;
        SetRunUiState(RunUiState.Ready);

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

        summaryStack.Children.Add(new TextBlock
        {
            Text = "Primary Workflow Fields",
            FontSize = 16,
            FontWeight = FontWeights.SemiBold,
            Margin = new Thickness(0, 8, 0, 0)
        });

        var taskScriptEditorGrid = new Grid { ColumnSpacing = 8 };
        taskScriptEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(95) });
        taskScriptEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        taskScriptEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var taskScriptEditorLabel = new TextBlock
        {
            Text = "Task script",
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(taskScriptEditorLabel, 0);
        taskScriptEditorGrid.Children.Add(taskScriptEditorLabel);

        _taskScriptEditorTextBox.PlaceholderText = "Task script path";
        Grid.SetColumn(_taskScriptEditorTextBox, 1);
        taskScriptEditorGrid.Children.Add(_taskScriptEditorTextBox);

        var browseTaskScriptButton = new Button
        {
            Content = "Browse",
            Margin = new Thickness(8, 0, 0, 0)
        };
        browseTaskScriptButton.Click += BrowseTaskScriptButton_Click;
        Grid.SetColumn(browseTaskScriptButton, 2);
        taskScriptEditorGrid.Children.Add(browseTaskScriptButton);

        summaryStack.Children.Add(taskScriptEditorGrid);

        var revitFileListEditorGrid = new Grid { ColumnSpacing = 8 };
        revitFileListEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(95) });
        revitFileListEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        revitFileListEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var revitFileListEditorLabel = new TextBlock
        {
            Text = "Revit list",
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(revitFileListEditorLabel, 0);
        revitFileListEditorGrid.Children.Add(revitFileListEditorLabel);

        _revitFileListEditorTextBox.PlaceholderText = "Revit file list path";
        Grid.SetColumn(_revitFileListEditorTextBox, 1);
        revitFileListEditorGrid.Children.Add(_revitFileListEditorTextBox);

        var browseRevitListButton = new Button
        {
            Content = "Browse",
            Margin = new Thickness(8, 0, 0, 0)
        };
        browseRevitListButton.Click += BrowseRevitFileListButton_Click;
        Grid.SetColumn(browseRevitListButton, 2);
        revitFileListEditorGrid.Children.Add(browseRevitListButton);

        summaryStack.Children.Add(revitFileListEditorGrid);

        var processingModeEditorGrid = new Grid { ColumnSpacing = 8 };
        processingModeEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(95) });
        processingModeEditorGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        var processingModeEditorLabel = new TextBlock
        {
            Text = "Mode",
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(processingModeEditorLabel, 0);
        processingModeEditorGrid.Children.Add(processingModeEditorLabel);

        _processingModeEditorComboBox.Items.Add(BatchRvt.RevitProcessingOption.BatchRevitFileProcessing);
        _processingModeEditorComboBox.Items.Add(BatchRvt.RevitProcessingOption.SingleRevitTaskProcessing);
        Grid.SetColumn(_processingModeEditorComboBox, 1);
        processingModeEditorGrid.Children.Add(_processingModeEditorComboBox);

        summaryStack.Children.Add(processingModeEditorGrid);

        var applyPrimaryFieldsButton = new Button
        {
            Content = "Apply Fields to JSON",
            HorizontalAlignment = HorizontalAlignment.Left,
            Margin = new Thickness(0, 2, 0, 0)
        };
        applyPrimaryFieldsButton.Click += ApplyPrimaryFieldsButton_Click;
        summaryStack.Children.Add(applyPrimaryFieldsButton);

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

    private void AppWindow_Closing(AppWindow sender, AppWindowClosingEventArgs args)
    {
        if (_batchRvtProcess is null || _batchRvtProcess.HasExited)
            return;

        var closeMessage = "Do you want to terminate the currently running task?";
        var closeResponse = ShowMessageBox(closeMessage, MB_YESNOCANCEL | MB_ICONASTERISK | MB_DEFBUTTON3);

        if (closeResponse == IDCANCEL)
        {
            args.Cancel = true;
            return;
        }

        if (closeResponse == IDYES)
        {
            StopRunningProcess(silent: false, killProcessTree: false);
        }
        else if (closeResponse == IDNO)
        {
            _skipProcessTerminationOnClose = true;
        }

        var saveMessage = "Do you want to save the current settings as default?";
        var saveResponse = ShowMessageBox(saveMessage, MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON1);

        if (saveResponse == IDYES)
            SaveCurrentSettings();
    }

    private void MainWindow_Closed(object sender, WindowEventArgs args)
    {
        if (_skipProcessTerminationOnClose)
            return;

        StopRunningProcess(silent: true, killProcessTree: false);
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

    private async void BrowseTaskScriptButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = InitializePickerWithWindow(new FileOpenPicker());
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add(".py");
        picker.FileTypeFilter.Add(".dyn");
        picker.FileTypeFilter.Add("*");

        var selectedFile = await picker.PickSingleFileAsync();
        if (selectedFile == null)
            return;

        _taskScriptEditorTextBox.Text = selectedFile.Path;
        SetStatus("Selected task script file path.");
    }

    private async void BrowseRevitFileListButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = InitializePickerWithWindow(new FileOpenPicker());
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add(".txt");
        picker.FileTypeFilter.Add(".csv");
        picker.FileTypeFilter.Add(".xls");
        picker.FileTypeFilter.Add(".xlsx");
        picker.FileTypeFilter.Add("*");

        var selectedFile = await picker.PickSingleFileAsync();
        if (selectedFile == null)
            return;

        _revitFileListEditorTextBox.Text = selectedFile.Path;
        SetStatus("Selected Revit file list path.");
    }

    private void ApplyPrimaryFieldsButton_Click(object sender, RoutedEventArgs e)
    {
        if (!TryApplyPrimaryWorkflowFieldsToSettingsJson(out var errorMessage))
        {
            AppendOutputLine("[ERROR] Failed to apply primary workflow fields: " + errorMessage);
            SetStatus("Failed to apply primary workflow fields.");
            return;
        }

        SetStatus("Primary workflow fields applied to settings JSON.");
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
            ? BatchRvtSettings.BATCHRVT_SETTINGS_FILENAME
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

        // Persist editor changes before validating and launching, mirroring WinForms save-then-run flow.
        if (!SaveCurrentSettings())
            return;

        var validationResult = _runValidationService.Validate(_settings);
        if (!validationResult.IsValid)
        {
            var validationMessage = validationResult.FirstError ?? "Settings validation failed.";
            AppendOutputLine(validationMessage);
            SetStatus("Cannot start batch run. Settings validation failed.");
            return;
        }

        var logFolderPath = NormalizePathOrEmpty(_logFolderPathTextBox.Text);
        if (!string.IsNullOrWhiteSpace(logFolderPath))
            Directory.CreateDirectory(logFolderPath);

        var startResult = _runService.Start(
            _settingsFilePath,
            string.IsNullOrWhiteSpace(logFolderPath) ? null : logFolderPath
        );

        if (!startResult.Succeeded || startResult.Process == null)
        {
            AppendOutputLine("[ERROR] Failed to start batch process.");
            if (!string.IsNullOrWhiteSpace(startResult.Exception?.Message))
                AppendOutputLine(startResult.Exception.Message);
            SetStatus("Failed to start batch process.");
            return;
        }

        _batchRvtProcess = startResult.Process;

        _batchRvtProcess.EnableRaisingEvents = true;
        _batchRvtProcess.Exited += BatchRvtProcess_Exited;
        _batchRvtProcess.OutputDataReceived += BatchRvtProcess_OutputDataReceived;
        _batchRvtProcess.ErrorDataReceived += BatchRvtProcess_ErrorDataReceived;
        _batchRvtProcess.BeginOutputReadLine();
        _batchRvtProcess.BeginErrorReadLine();

        SetRunUiState(RunUiState.Running);

        SetStatus("Batch process started.");
    }

    private void StopButton_Click(object sender, RoutedEventArgs e)
    {
        StopRunningProcess(silent: false);
    }

    private void BatchRvtProcess_OutputDataReceived(object sender, DataReceivedEventArgs e)
    {
        if (!_outputPolicy.TryFormatStandardOutput(e.Data, out var formattedLine))
            return;

        AppendOutputLine(formattedLine);
    }

    private void BatchRvtProcess_ErrorDataReceived(object sender, DataReceivedEventArgs e)
    {
        if (!_outputPolicy.TryFormatStandardError(
                e.Data,
                _settings.ShowRevitProcessErrorMessages.GetValue(),
                out var formattedLine))
        {
            return;
        }

        AppendOutputLine(formattedLine);
    }

    private void BatchRvtProcess_Exited(object? sender, EventArgs e)
    {
        DispatcherQueue.TryEnqueue(() =>
        {
            SetRunUiState(RunUiState.Completed);
            _startButton.IsEnabled = true;
            _batchRvtProcess = null;
            SetStatus("Batch process exited.");
        });
    }

    private void StopRunningProcess(bool silent, bool killProcessTree = true)
    {
        if (_batchRvtProcess is null)
            return;

        var stopResult = _runService.Stop(_batchRvtProcess, killProcessTree: killProcessTree);
        if (!stopResult.Succeeded && !silent)
        {
            AppendOutputLine("[ERROR] Failed to stop batch process: " + stopResult.Exception?.Message);
        }

        if (stopResult.Succeeded)
            SetRunUiState(RunUiState.StopRequested);

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
        var loadResult = _settingsWorkflowService.Load(_settingsFilePath);

        if (loadResult.FileMissing)
        {
            _settings = new BatchRvtSettings();
            _settingsJsonTextBox.Text = "{}";
            UpdateSummaryFromSettings();
            SetStatus("Settings file was not found. Loaded an empty JSON document.");
            return;
        }

        if (!loadResult.Succeeded)
        {
            var errorMessage = loadResult.ErrorMessage ?? "Could not parse settings file.";
            AppendOutputLine("[ERROR] Failed to load settings: " + errorMessage);
            SetSummaryInvalid("(invalid settings)");
            SetStatus("Settings load failed.");
            return;
        }

        _settingsJsonTextBox.Text = loadResult.SettingsJson;
        _settings = loadResult.Settings;
        UpdateSummaryFromSettings();
        SetStatus("Settings loaded.");
    }

    private bool SaveCurrentSettings()
    {
        if (!TryApplyPrimaryWorkflowFieldsToSettingsJson(out var applyErrorMessage))
        {
            AppendOutputLine("[ERROR] Failed to apply primary workflow fields: " + applyErrorMessage);
            SetStatus("Settings save failed.");
            return false;
        }

        var saveResult = _settingsWorkflowService.SaveSettingsJson(_settingsJsonTextBox.Text, _settingsFilePath);
        if (!saveResult.Succeeded)
        {
            var errorMessage = saveResult.ErrorMessage ?? "Failed to save settings.";
            AppendOutputLine("[ERROR] Failed to save settings: " + errorMessage);
            SetSummaryInvalid("(invalid settings)");
            SetStatus("Settings save failed.");
            return false;
        }

        _settings = saveResult.Settings;
        UpdateSummaryFromSettings();
        SetStatus("Settings saved.");
        return true;
    }

    private void UpdateSummaryFromSettings()
    {
        _taskScriptValueTextBlock.Text = DisplayValueOrDefault(_settings.TaskScriptFilePath.GetValue());
        _revitFileListValueTextBlock.Text = DisplayValueOrDefault(_settings.RevitFileListFilePath.GetValue());
        _processingModeValueTextBlock.Text = _settings.RevitProcessingOption.GetValue().ToString();
        _batchRevitVersionValueTextBlock.Text = _settings.BatchRevitTaskRevitVersion.GetValue().ToString();
        _revitSessionModeValueTextBlock.Text = _settings.RevitSessionOption.GetValue().ToString();
        UpdatePrimaryWorkflowEditors();
    }

    private void SetSummaryInvalid(string value)
    {
        _taskScriptValueTextBlock.Text = value;
        _revitFileListValueTextBlock.Text = value;
        _processingModeValueTextBlock.Text = value;
        _batchRevitVersionValueTextBlock.Text = value;
        _revitSessionModeValueTextBlock.Text = value;
    }

    private void UpdatePrimaryWorkflowEditors()
    {
        _taskScriptEditorTextBox.Text = _settings.TaskScriptFilePath.GetValue() ?? string.Empty;
        _revitFileListEditorTextBox.Text = _settings.RevitFileListFilePath.GetValue() ?? string.Empty;
        _processingModeEditorComboBox.SelectedItem = _settings.RevitProcessingOption.GetValue();
    }

    private bool TryApplyPrimaryWorkflowFieldsToSettingsJson(out string errorMessage)
    {
        errorMessage = string.Empty;
        var tempSettingsFilePath = Path.GetTempFileName();

        try
        {
            var loadFromJsonResult = _settingsWorkflowService.SaveSettingsJson(_settingsJsonTextBox.Text, tempSettingsFilePath);
            if (!loadFromJsonResult.Succeeded || loadFromJsonResult.Settings == null)
            {
                errorMessage = loadFromJsonResult.ErrorMessage ?? "Could not parse settings JSON.";
                return false;
            }

            var settings = loadFromJsonResult.Settings;

            settings.TaskScriptFilePath.SetValue(NormalizePathOrEmpty(_taskScriptEditorTextBox.Text));
            settings.RevitFileListFilePath.SetValue(NormalizePathOrEmpty(_revitFileListEditorTextBox.Text));

            if (_processingModeEditorComboBox.SelectedItem is BatchRvt.RevitProcessingOption processingOption)
                settings.RevitProcessingOption.SetValue(processingOption);

            var mergedSaveResult = _settingsWorkflowService.SaveSettings(settings, tempSettingsFilePath);
            if (!mergedSaveResult.Succeeded || mergedSaveResult.Settings == null)
            {
                errorMessage = mergedSaveResult.ErrorMessage ?? "Failed to merge primary workflow fields into settings JSON.";
                return false;
            }

            _settingsJsonTextBox.Text = mergedSaveResult.SettingsJson ?? "{}";
            _settings = mergedSaveResult.Settings;
            UpdateSummaryFromSettings();
            return true;
        }
        catch (Exception ex)
        {
            errorMessage = ex.Message;
            return false;
        }
        finally
        {
            try
            {
                if (File.Exists(tempSettingsFilePath))
                    File.Delete(tempSettingsFilePath);
            }
            catch
            {
                // Best-effort cleanup only.
            }
        }
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

    private void SetRunUiState(RunUiState state)
    {
        switch (state)
        {
            case RunUiState.Ready:
                _startButton.Content = "Start";
                _startButton.IsEnabled = true;
                _stopButton.IsEnabled = false;
                break;

            case RunUiState.Running:
                _startButton.Content = "Running...";
                _startButton.IsEnabled = false;
                _stopButton.IsEnabled = true;
                break;

            case RunUiState.StopRequested:
                _startButton.Content = "Running...";
                _startButton.IsEnabled = false;
                _stopButton.IsEnabled = false;
                break;

            case RunUiState.Completed:
                _startButton.Content = "Done!";
                _startButton.IsEnabled = true;
                _stopButton.IsEnabled = false;
                break;
        }
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

    private TPicker InitializePickerWithWindow<TPicker>(TPicker picker)
        where TPicker : class
    {
        var windowHandle = WindowNative.GetWindowHandle(this);
        InitializeWithWindow.Initialize(picker, windowHandle);
        return picker;
    }

    private int ShowMessageBox(string message, uint options)
    {
        var windowHandle = WindowNative.GetWindowHandle(this);
        return MessageBox(windowHandle, message, BatchUiPreflight.WindowTitle, options);
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(IntPtr hWnd, string lpText, string lpCaption, uint uType);
}
