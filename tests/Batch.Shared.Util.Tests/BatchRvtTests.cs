using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using Batch.Shared.Util;
using Xunit;


namespace Batch.Shared.Util.Tests
{
    public class BatchRvtTests
    {
        
        [Fact]
        public void ConstructCommandLineArguments_ShouldReturnArguments()
        {
            IEnumerable<KeyValuePair<string, string>> arguments = new List<KeyValuePair<string, string>>(){ new(
                "test1", "test2")};
            var result = BatchRvt.ConstructCommandLineArguments(arguments);
            Assert.Equal(string.Join(" ", "--" + "test1" + " " + "test2"), result);

        }

        [Theory]
        [InlineData(null)]
        public void ConstructCommandLineArguments_ShouldFail(List<KeyValuePair<string, string>> arguments)
        {
            Assert.Throws<ArgumentException>(() => BatchRvt.ConstructCommandLineArguments(arguments));
        }

        [Theory]
        [InlineData("16:30:13")]
        public void IsBatchRvtLine_ShouldReturnTrueOnCorrectLine(string line)
        {
            Assert.True(BatchRvt.IsBatchRvtLine(line));
        }
        
        [Theory]
        [InlineData("x:x:x")]
        [InlineData("")]
        
        public void IsBatchRvtLine_ShouldReturnFalseOnIncorrectLine(string line)
        {
            Assert.False(BatchRvt.IsBatchRvtLine(line));
        }
        [Theory]
        [InlineData(null)]
        public void IsBatchRvtLine_ShouldReturnExceptionOnNullArgument(string line)
        {
            Assert.Throws<ArgumentException>(() => BatchRvt.IsBatchRvtLine(line));
        }

        [Theory]
        [InlineData("2024")]
        [InlineData("2025")]
        [InlineData("2026")]
        [InlineData("2027")]
        public void IsSupportedRevitVersionNumber_ShouldReturnTrue_ForSupportedVersions(string revitVersionNumber)
        {
            Assert.True(RevitVersion.IsSupportedRevitVersionNumber(revitVersionNumber));
        }

        [Theory]
        [InlineData("2023")]
        [InlineData("2019")]
        [InlineData("2028")]
        [InlineData("foo")]
        public void IsSupportedRevitVersionNumber_ShouldReturnFalse_ForUnsupportedVersions(string revitVersionNumber)
        {
            Assert.False(RevitVersion.IsSupportedRevitVersionNumber(revitVersionNumber));
        }

        [Theory]
        [InlineData("2024", RevitVersion.SupportedRevitVersion.Revit2024)]
        [InlineData("2025", RevitVersion.SupportedRevitVersion.Revit2025)]
        [InlineData("2026", RevitVersion.SupportedRevitVersion.Revit2026)]
        [InlineData("2027", RevitVersion.SupportedRevitVersion.Revit2027)]
        public void GetSupportedRevitVersion_ShouldReturnExpectedEnum_ForSupportedVersions(
            string revitVersionNumber,
            RevitVersion.SupportedRevitVersion expectedVersion)
        {
            var actualVersion = RevitVersion.GetSupportedRevitVersion(revitVersionNumber);

            Assert.Equal(expectedVersion, actualVersion);
        }

        [Fact]
        public void SupportedRevitVersion_Enum_ShouldContainOnlyExpectedVersions()
        {
            var versionNames = Enum.GetNames(typeof(RevitVersion.SupportedRevitVersion));

            Assert.Equal(4, versionNames.Length);
            Assert.Equal(
                new[]
                {
                    nameof(RevitVersion.SupportedRevitVersion.Revit2024),
                    nameof(RevitVersion.SupportedRevitVersion.Revit2025),
                    nameof(RevitVersion.SupportedRevitVersion.Revit2026),
                    nameof(RevitVersion.SupportedRevitVersion.Revit2027)
                },
                versionNames.ToArray());
        }

        [Fact]
        public void LoadFromFile_ShouldRejectLegacyRevitVersionSetting()
        {
            var settingsFilePath = CreateTempSettingsFile(
                "{\"singleRevitTaskRevitVersion\":\"Revit2023\"}");

            try
            {
                var settings = new BatchRvtSettings();
                var loaded = settings.LoadFromFile(settingsFilePath);

                Assert.False(loaded);
                Assert.IsType<NotSupportedException>(settings.LastLoadException);
            }
            finally
            {
                File.Delete(settingsFilePath);
            }
        }

        [Fact]
        public void LoadFromFile_ShouldRejectInvalidRevitVersionSetting()
        {
            var settingsFilePath = CreateTempSettingsFile(
                "{\"singleRevitTaskRevitVersion\":\"NotARealVersion\"}");

            try
            {
                var settings = new BatchRvtSettings();
                var loaded = settings.LoadFromFile(settingsFilePath);

                Assert.False(loaded);
                Assert.IsType<FormatException>(settings.LastLoadException);
            }
            finally
            {
                File.Delete(settingsFilePath);
            }
        }

        [Fact]
        public void LoadFromFile_ShouldAcceptSupportedRevitVersionSetting()
        {
            var settingsFilePath = CreateTempSettingsFile(
                "{\"singleRevitTaskRevitVersion\":\"Revit2024\"}");

            try
            {
                var settings = new BatchRvtSettings();
                var loaded = settings.LoadFromFile(settingsFilePath);

                Assert.True(loaded);
                Assert.Null(settings.LastLoadException);
                Assert.Equal(
                    RevitVersion.SupportedRevitVersion.Revit2024,
                    settings.SingleRevitTaskRevitVersion.GetValue());
            }
            finally
            {
                File.Delete(settingsFilePath);
            }
        }

        [Fact]
        public void LoadFromFile_ShouldRejectUndefinedNumericRevitVersionSetting()
        {
            var settingsFilePath = CreateTempSettingsFile(
                "{\"singleRevitTaskRevitVersion\":\"2023\"}");

            try
            {
                var settings = new BatchRvtSettings();
                var loaded = settings.LoadFromFile(settingsFilePath);

                Assert.False(loaded);
                Assert.IsType<FormatException>(settings.LastLoadException);
            }
            finally
            {
                File.Delete(settingsFilePath);
            }
        }

        [Fact]
        public void LoadFromFile_ShouldRejectUndefinedNumericWorksetOptionSetting()
        {
            var settingsFilePath = CreateTempSettingsFile(
                "{\"worksetConfigurationOption\":\"99\"}");

            try
            {
                var settings = new BatchRvtSettings();
                var loaded = settings.LoadFromFile(settingsFilePath);

                Assert.False(loaded);
                Assert.IsType<FormatException>(settings.LastLoadException);
            }
            finally
            {
                File.Delete(settingsFilePath);
            }
        }

        [Fact]
        public void ResolveBatchRvtExecutableFilePath_ShouldPreferCliExecutableName()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var legacyExecutablePath = Path.Combine(tempDirectoryPath, "BatchRvt.exe");
                var cliExecutablePath = Path.Combine(tempDirectoryPath, "Batch.App.Cli.exe");

                File.WriteAllText(legacyExecutablePath, string.Empty);
                File.WriteAllText(cliExecutablePath, string.Empty);

                var executablePath = ResolveBatchRvtExecutableFilePathForTest(tempDirectoryPath);

                Assert.Equal(cliExecutablePath, executablePath);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void ResolveBatchRvtExecutableFilePath_ShouldFallbackToLegacyExecutableName()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var legacyExecutablePath = Path.Combine(tempDirectoryPath, "BatchRvt.exe");

                File.WriteAllText(legacyExecutablePath, string.Empty);

                var executablePath = ResolveBatchRvtExecutableFilePathForTest(tempDirectoryPath);

                Assert.Equal(legacyExecutablePath, executablePath);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void ResolveBatchRvtExecutableFilePath_ShouldThrowWhenNoExecutableExists()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var exception = Assert.Throws<FileNotFoundException>(() =>
                    ResolveBatchRvtExecutableFilePathForTest(tempDirectoryPath));

                Assert.Contains("BatchRvt.exe", exception.Message);
                Assert.Contains("Batch.App.Cli.exe", exception.Message);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void BatchSettingsWorkflowService_ShouldSaveAndLoadSettingsJson()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var settingsFilePath = Path.Combine(tempDirectoryPath, "BatchRvt.Settings.json");
                var service = new BatchSettingsWorkflowService();

                var saveResult = service.SaveSettingsJson("{}", settingsFilePath);
                Assert.True(saveResult.Succeeded);
                Assert.True(File.Exists(settingsFilePath));

                var loadResult = service.Load(settingsFilePath);
                Assert.True(loadResult.Succeeded);
                Assert.NotNull(loadResult.Settings);
                Assert.NotNull(loadResult.Summary);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void BatchSettingsWorkflowService_ShouldSupportWinFormsAndWinUIStyleSaveFlows()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var scriptPathA = Path.Combine(tempDirectoryPath, "task-A.py");
                var listPathA = Path.Combine(tempDirectoryPath, "list-A.txt");
                var scriptPathB = Path.Combine(tempDirectoryPath, "task-B.py");
                var listPathB = Path.Combine(tempDirectoryPath, "list-B.txt");
                File.WriteAllText(scriptPathA, "# A");
                File.WriteAllText(listPathA, "C:/Models/A.rvt");
                File.WriteAllText(scriptPathB, "# B");
                File.WriteAllText(listPathB, "C:/Models/B.rvt");

                var settingsFilePathA = Path.Combine(tempDirectoryPath, "A.BatchRvt.Settings.json");
                var settingsFilePathB = Path.Combine(tempDirectoryPath, "B.BatchRvt.Settings.json");

                var service = new BatchSettingsWorkflowService();

                // WinForms-style save from model.
                var settings = new BatchRvtSettings();
                settings.TaskScriptFilePath.SetValue(scriptPathA);
                settings.RevitProcessingOption.SetValue(BatchRvt.RevitProcessingOption.BatchRevitFileProcessing);
                settings.RevitFileListFilePath.SetValue(listPathA);
                var saveModelResult = service.SaveSettings(settings, settingsFilePathA);
                Assert.True(saveModelResult.Succeeded);

                // WinUI-style save from editable JSON text.
                var uiJson =
                    "{\"taskScriptFilePath\":\"" + scriptPathB.Replace("\\", "\\\\") + "\","
                    + "\"revitProcessingOption\":\"BatchRevitFileProcessing\","
                    + "\"revitFileListFilePath\":\"" + listPathB.Replace("\\", "\\\\") + "\"}";
                var saveJsonResult = service.SaveSettingsJson(uiJson, settingsFilePathB);
                Assert.True(saveJsonResult.Succeeded);

                var loadA = service.Load(settingsFilePathA);
                var loadB = service.Load(settingsFilePathB);

                Assert.True(loadA.Succeeded);
                Assert.True(loadB.Succeeded);
                Assert.Equal(scriptPathA, loadA.Settings.TaskScriptFilePath.GetValue());
                Assert.Equal(listPathA, loadA.Settings.RevitFileListFilePath.GetValue());
                Assert.Equal(scriptPathB, loadB.Settings.TaskScriptFilePath.GetValue());
                Assert.Equal(listPathB, loadB.Settings.RevitFileListFilePath.GetValue());
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void BatchRunValidationService_ShouldRejectMissingRevitListInBatchMode()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var taskScriptPath = Path.Combine(tempDirectoryPath, "task.py");
                File.WriteAllText(taskScriptPath, "# test");

                var settings = new BatchRvtSettings();
                settings.TaskScriptFilePath.SetValue(taskScriptPath);
                settings.RevitProcessingOption.SetValue(BatchRvt.RevitProcessingOption.BatchRevitFileProcessing);
                settings.RevitFileListFilePath.SetValue(Path.Combine(tempDirectoryPath, "missing-list.txt"));

                var validationService = new BatchRunValidationService();
                var validationResult = validationService.Validate(settings);

                Assert.False(validationResult.IsValid);
                Assert.Contains("ERROR: You must select an existing Revit File List!", validationResult.Errors);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void BatchRunValidationService_ShouldAcceptValidPrimaryBatchInputs()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var taskScriptPath = Path.Combine(tempDirectoryPath, "task.py");
                var revitListPath = Path.Combine(tempDirectoryPath, "files.txt");
                File.WriteAllText(taskScriptPath, "# test");
                File.WriteAllText(revitListPath, "C:/Models/Test.rvt");

                var settings = new BatchRvtSettings();
                settings.TaskScriptFilePath.SetValue(taskScriptPath);
                settings.RevitProcessingOption.SetValue(BatchRvt.RevitProcessingOption.BatchRevitFileProcessing);
                settings.RevitFileListFilePath.SetValue(revitListPath);
                settings.EnableDataExport.SetValue(false);
                settings.ExecutePreProcessingScript.SetValue(false);
                settings.ExecutePostProcessingScript.SetValue(false);

                var validationService = new BatchRunValidationService();
                var validationResult = validationService.Validate(settings);

                Assert.True(validationResult.IsValid);
                Assert.Empty(validationResult.Errors);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void BatchOutputPolicy_ShouldSuppressNonBatchOutputLines()
        {
            var outputPolicy = new BatchOutputPolicy();

            var accepted = outputPolicy.TryFormatStandardOutput("this is not a BatchRvt line", out var formattedLine);

            Assert.False(accepted);
            Assert.Null(formattedLine);
        }

        [Fact]
        public void BatchOutputPolicy_ShouldAcceptBatchOutputLines()
        {
            var outputPolicy = new BatchOutputPolicy();

            var accepted = outputPolicy.TryFormatStandardOutput("16:30:13 : test", out var formattedLine);

            Assert.True(accepted);
            Assert.Equal("16:30:13 : test", formattedLine);
        }

        [Fact]
        public void BatchOutputPolicy_ShouldFilterStandardErrorByVisibilityAndNoiseRules()
        {
            var outputPolicy = new BatchOutputPolicy();

            var hiddenErrorAccepted = outputPolicy.TryFormatStandardError("runtime error", false, out var _);
            var log4CplusAccepted = outputPolicy.TryFormatStandardError("log4cplus: startup", true, out var _);
            var visibleErrorAccepted = outputPolicy.TryFormatStandardError("runtime error", true, out var formattedLine);

            Assert.False(hiddenErrorAccepted);
            Assert.False(log4CplusAccepted);
            Assert.True(visibleErrorAccepted);
            Assert.Equal("[ REVIT ERROR MESSAGE ] : runtime error", formattedLine);
        }

        [Fact]
        public void BatchRunService_Stop_ShouldSucceed_WhenProcessIsNull()
        {
            var runService = new BatchRunService();

            var stopResult = runService.Stop(null, killProcessTree: true);

            Assert.True(stopResult.Succeeded);
            Assert.Null(stopResult.Exception);
        }

        [Fact]
        public void BatchRunService_Stop_ShouldTerminateRunningProcess()
        {
            var processStartInfo = new ProcessStartInfo("cmd.exe", "/c ping 127.0.0.1 -n 8 > nul")
            {
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(processStartInfo);
            Assert.NotNull(process);

            var runService = new BatchRunService();
            var stopResult = runService.Stop(process, killProcessTree: true);

            Assert.True(stopResult.Succeeded);
            process.WaitForExit(5000);
            Assert.True(process.HasExited);
        }

        private static string CreateTempSettingsFile(string json)
        {
            var filePath = Path.GetTempFileName();
            File.WriteAllText(filePath, json);
            return filePath;
        }

        private static string CreateTempDirectory()
        {
            var directoryPath = Path.Combine(Path.GetTempPath(), "BatchRvtTests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directoryPath);
            return directoryPath;
        }

        private static string ResolveBatchRvtExecutableFilePathForTest(string baseDirectory)
        {
            var method = typeof(BatchRvt).GetMethod(
                "ResolveBatchRvtExecutableFilePath",
                BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Static
            );

            Assert.NotNull(method);

            try
            {
                return (string)method.Invoke(null, new object[] { baseDirectory });
            }
catch (TargetInvocationException ex) when (ex.InnerException != null)
{
    System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
    throw;
}
        }
    }
}