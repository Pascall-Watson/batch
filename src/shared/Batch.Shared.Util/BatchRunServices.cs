using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

namespace Batch.Shared.Util;

public interface IBatchRunValidationService
{
    BatchRunValidationResult Validate(BatchRvtSettings settings);
}

public sealed class BatchRunValidationService : IBatchRunValidationService
{
    public BatchRunValidationResult Validate(BatchRvtSettings settings)
    {
        if (settings == null)
            throw new ArgumentNullException(nameof(settings));

        var errors = new List<string>();

        if (!File.Exists(settings.TaskScriptFilePath.GetValue()))
            errors.Add("ERROR: You must select an existing Task script!");

        if (settings.RevitProcessingOption.GetValue() == BatchRvt.RevitProcessingOption.BatchRevitFileProcessing
            && !File.Exists(settings.RevitFileListFilePath.GetValue()))
        {
            errors.Add("ERROR: You must select an existing Revit File List!");
        }

        if (settings.EnableDataExport.GetValue() && !Directory.Exists(settings.DataExportFolderPath.GetValue()))
            errors.Add("ERROR: You must select an existing Data Export folder!");

        if (settings.ExecutePreProcessingScript.GetValue() && !File.Exists(settings.PreProcessingScriptFilePath.GetValue()))
            errors.Add("ERROR: You must select an existing Pre-Processing Python script!");

        if (settings.ExecutePostProcessingScript.GetValue() && !File.Exists(settings.PostProcessingScriptFilePath.GetValue()))
            errors.Add("ERROR: You must select an existing Post-Processing Python script!");

        return BatchRunValidationResult.Create(errors);
    }
}

public sealed class BatchRunValidationResult
{
    private BatchRunValidationResult(IReadOnlyList<string> errors)
    {
        Errors = errors;
    }

    public bool IsValid => Errors.Count == 0;
    public IReadOnlyList<string> Errors { get; }
    public string FirstError => IsValid ? null : Errors[0];

    public static BatchRunValidationResult Create(IReadOnlyList<string> errors)
    {
        return new BatchRunValidationResult(errors ?? Array.Empty<string>());
    }
}

public interface IBatchOutputPolicy
{
    bool TryFormatStandardOutput(string line, out string formattedLine);
    bool TryFormatStandardError(string line, bool showRevitProcessErrorMessages, out string formattedLine);
}

public sealed class BatchOutputPolicy : IBatchOutputPolicy
{
    public bool TryFormatStandardOutput(string line, out string formattedLine)
    {
        formattedLine = null;

        if (string.IsNullOrWhiteSpace(line))
            return false;

        if (!BatchRvt.IsBatchRvtLine(line))
            return false;

        formattedLine = line;
        return true;
    }

    public bool TryFormatStandardError(string line, bool showRevitProcessErrorMessages, out string formattedLine)
    {
        formattedLine = null;

        if (string.IsNullOrWhiteSpace(line))
            return false;

        if (line.StartsWith("log4cplus:", StringComparison.OrdinalIgnoreCase))
            return false;

        if (!showRevitProcessErrorMessages)
            return false;

        formattedLine = "[ REVIT ERROR MESSAGE ] : " + line;
        return true;
    }
}

public interface IBatchRunService
{
    BatchRunStartResult Start(string settingsFilePath, string logFolderPath = null);
    BatchRunStopResult Stop(Process process, bool killProcessTree);
}

public sealed class BatchRunService : IBatchRunService
{
    public BatchRunStartResult Start(string settingsFilePath, string logFolderPath = null)
    {
        try
        {
            var process = BatchRvt.StartBatchRvt(settingsFilePath, logFolderPath);
            return BatchRunStartResult.Success(process);
        }
        catch (Exception ex)
        {
            return BatchRunStartResult.Error(ex);
        }
    }

    public BatchRunStopResult Stop(Process process, bool killProcessTree)
    {
        if (process == null)
            return BatchRunStopResult.Success();

        try
        {
            if (!process.HasExited)
            {
#if NETFRAMEWORK
                process.Kill();
#else
                process.Kill(killProcessTree);
#endif
            }

            return BatchRunStopResult.Success();
        }
        catch (Exception ex)
        {
            return BatchRunStopResult.Error(ex);
        }
    }
}

public sealed class BatchRunStartResult
{
    private BatchRunStartResult()
    {
    }

    public bool Succeeded { get; private set; }
    public Process Process { get; private set; }
    public Exception Exception { get; private set; }

    public static BatchRunStartResult Success(Process process)
    {
        return new BatchRunStartResult
        {
            Succeeded = true,
            Process = process
        };
    }

    public static BatchRunStartResult Error(Exception exception)
    {
        return new BatchRunStartResult
        {
            Succeeded = false,
            Exception = exception
        };
    }
}

public sealed class BatchRunStopResult
{
    private BatchRunStopResult()
    {
    }

    public bool Succeeded { get; private set; }
    public Exception Exception { get; private set; }

    public static BatchRunStopResult Success()
    {
        return new BatchRunStopResult
        {
            Succeeded = true
        };
    }

    public static BatchRunStopResult Error(Exception exception)
    {
        return new BatchRunStopResult
        {
            Succeeded = false,
            Exception = exception
        };
    }
}
