using System;
using System.IO;

namespace Batch.Shared.Util;

public interface IBatchSettingsWorkflowService
{
    BatchSettingsLoadResult Load(string settingsFilePath = null);
    BatchSettingsSaveResult SaveSettingsJson(string settingsJson, string settingsFilePath = null);
    BatchSettingsSaveResult SaveSettings(BatchRvtSettings settings, string settingsFilePath = null);
    BatchSettingsSummary CreateSummary(BatchRvtSettings settings);
}

public sealed class BatchSettingsWorkflowService : IBatchSettingsWorkflowService
{
    public BatchSettingsLoadResult Load(string settingsFilePath = null)
    {
        var effectivePath = string.IsNullOrWhiteSpace(settingsFilePath)
            ? BatchRvtSettings.GetDefaultSettingsFilePath()
            : settingsFilePath;

        if (!File.Exists(effectivePath))
            return BatchSettingsLoadResult.MissingFile(effectivePath);

        string settingsJson;
        try
        {
            settingsJson = File.ReadAllText(effectivePath);
        }
        catch (Exception ex)
        {
            return BatchSettingsLoadResult.Error(effectivePath, "Failed to read settings file.", ex);
        }

        var settings = new BatchRvtSettings();
        if (!settings.LoadFromFile(effectivePath))
        {
            var message = settings.LastLoadException?.Message ?? "Could not parse settings file.";
            return BatchSettingsLoadResult.Error(effectivePath, message, settings.LastLoadException);
        }

        return BatchSettingsLoadResult.Success(effectivePath, settingsJson, settings, CreateSummary(settings));
    }

    public BatchSettingsSaveResult SaveSettingsJson(string settingsJson, string settingsFilePath = null)
    {
        var effectivePath = string.IsNullOrWhiteSpace(settingsFilePath)
            ? BatchRvtSettings.GetDefaultSettingsFilePath()
            : settingsFilePath;

        var normalizedJson = string.IsNullOrWhiteSpace(settingsJson)
            ? "{}"
            : settingsJson;

        try
        {
            JsonUtil.DeserializeFromJson(normalizedJson);

            var directoryPath = Path.GetDirectoryName(effectivePath);
            if (!string.IsNullOrWhiteSpace(directoryPath))
                Directory.CreateDirectory(directoryPath);

            File.WriteAllText(effectivePath, normalizedJson);
        }
        catch (Exception ex)
        {
            return BatchSettingsSaveResult.Error(effectivePath, "Failed to save settings file.", ex);
        }

        var loadResult = Load(effectivePath);
        if (!loadResult.Succeeded)
        {
            return BatchSettingsSaveResult.Error(
                effectivePath,
                loadResult.ErrorMessage ?? "Settings were saved but could not be loaded.",
                loadResult.Exception
            );
        }

        return BatchSettingsSaveResult.Success(effectivePath, normalizedJson, loadResult.Settings, loadResult.Summary);
    }

    public BatchSettingsSaveResult SaveSettings(BatchRvtSettings settings, string settingsFilePath = null)
    {
        if (settings == null)
            throw new ArgumentNullException(nameof(settings));

        var effectivePath = string.IsNullOrWhiteSpace(settingsFilePath)
            ? BatchRvtSettings.GetDefaultSettingsFilePath()
            : settingsFilePath;

        if (!settings.SaveToFile(effectivePath))
            return BatchSettingsSaveResult.Error(effectivePath, "Failed to save settings file.", null);

        var loadResult = Load(effectivePath);
        if (!loadResult.Succeeded)
        {
            return BatchSettingsSaveResult.Error(
                effectivePath,
                loadResult.ErrorMessage ?? "Settings were saved but could not be loaded.",
                loadResult.Exception
            );
        }

        return BatchSettingsSaveResult.Success(
            effectivePath,
            loadResult.SettingsJson ?? "{}",
            loadResult.Settings,
            loadResult.Summary
        );
    }

    public BatchSettingsSummary CreateSummary(BatchRvtSettings settings)
    {
        if (settings == null)
            throw new ArgumentNullException(nameof(settings));

        return new BatchSettingsSummary(
            settings.TaskScriptFilePath.GetValue(),
            settings.RevitFileListFilePath.GetValue(),
            settings.RevitProcessingOption.GetValue().ToString(),
            settings.BatchRevitTaskRevitVersion.GetValue().ToString(),
            settings.RevitSessionOption.GetValue().ToString()
        );
    }
}

public sealed class BatchSettingsSummary
{
    public BatchSettingsSummary(
        string taskScriptFilePath,
        string revitFileListFilePath,
        string processingMode,
        string batchRevitVersion,
        string revitSessionMode)
    {
        TaskScriptFilePath = taskScriptFilePath;
        RevitFileListFilePath = revitFileListFilePath;
        ProcessingMode = processingMode;
        BatchRevitVersion = batchRevitVersion;
        RevitSessionMode = revitSessionMode;
    }

    public string TaskScriptFilePath { get; }
    public string RevitFileListFilePath { get; }
    public string ProcessingMode { get; }
    public string BatchRevitVersion { get; }
    public string RevitSessionMode { get; }
}

public sealed class BatchSettingsLoadResult
{
    private BatchSettingsLoadResult()
    {
    }

    public bool Succeeded { get; private set; }
    public bool FileMissing { get; private set; }
    public string SettingsFilePath { get; private set; }
    public string SettingsJson { get; private set; }
    public BatchRvtSettings Settings { get; private set; }
    public BatchSettingsSummary Summary { get; private set; }
    public string ErrorMessage { get; private set; }
    public Exception Exception { get; private set; }

    public static BatchSettingsLoadResult Success(
        string settingsFilePath,
        string settingsJson,
        BatchRvtSettings settings,
        BatchSettingsSummary summary)
    {
        return new BatchSettingsLoadResult
        {
            Succeeded = true,
            FileMissing = false,
            SettingsFilePath = settingsFilePath,
            SettingsJson = settingsJson,
            Settings = settings,
            Summary = summary
        };
    }

    public static BatchSettingsLoadResult MissingFile(string settingsFilePath)
    {
        return new BatchSettingsLoadResult
        {
            Succeeded = false,
            FileMissing = true,
            SettingsFilePath = settingsFilePath,
            ErrorMessage = "Settings file was not found."
        };
    }

    public static BatchSettingsLoadResult Error(string settingsFilePath, string errorMessage, Exception exception)
    {
        return new BatchSettingsLoadResult
        {
            Succeeded = false,
            FileMissing = false,
            SettingsFilePath = settingsFilePath,
            ErrorMessage = errorMessage,
            Exception = exception
        };
    }
}

public sealed class BatchSettingsSaveResult
{
    private BatchSettingsSaveResult()
    {
    }

    public bool Succeeded { get; private set; }
    public string SettingsFilePath { get; private set; }
    public string SettingsJson { get; private set; }
    public BatchRvtSettings Settings { get; private set; }
    public BatchSettingsSummary Summary { get; private set; }
    public string ErrorMessage { get; private set; }
    public Exception Exception { get; private set; }

    public static BatchSettingsSaveResult Success(
        string settingsFilePath,
        string settingsJson,
        BatchRvtSettings settings,
        BatchSettingsSummary summary)
    {
        return new BatchSettingsSaveResult
        {
            Succeeded = true,
            SettingsFilePath = settingsFilePath,
            SettingsJson = settingsJson,
            Settings = settings,
            Summary = summary
        };
    }

    public static BatchSettingsSaveResult Error(string settingsFilePath, string errorMessage, Exception exception)
    {
        return new BatchSettingsSaveResult
        {
            Succeeded = false,
            SettingsFilePath = settingsFilePath,
            ErrorMessage = errorMessage,
            Exception = exception
        };
    }
}
