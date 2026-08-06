using System;
using System.Collections.Generic;
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
        public void ResolveBatchRvtExecutableFilePath_ShouldPreferLegacyExecutableName()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var legacyExecutablePath = Path.Combine(tempDirectoryPath, "BatchRvt.exe");
                var cliExecutablePath = Path.Combine(tempDirectoryPath, "Batch.App.Cli.exe");

                File.WriteAllText(legacyExecutablePath, string.Empty);
                File.WriteAllText(cliExecutablePath, string.Empty);

                var executablePath = ResolveBatchRvtExecutableFilePathForTest(tempDirectoryPath);

                Assert.Equal(legacyExecutablePath, executablePath);
            }
            finally
            {
                Directory.Delete(tempDirectoryPath, true);
            }
        }

        [Fact]
        public void ResolveBatchRvtExecutableFilePath_ShouldFallbackToCliExecutableName()
        {
            var tempDirectoryPath = CreateTempDirectory();

            try
            {
                var cliExecutablePath = Path.Combine(tempDirectoryPath, "Batch.App.Cli.exe");

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
                throw ex.InnerException;
            }
        }
    }
}