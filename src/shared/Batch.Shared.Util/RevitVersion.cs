//
// Revit Batch Processor
//
// Copyright (c) 2020  Daniel Rumery, BVN
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
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Win32;

namespace Batch.Shared.Util;

public static class RevitVersion
{
    // Extend this enum when adding future supported Revit versions.
    public enum SupportedRevitVersion
    {
        Revit2024 = 0,
        Revit2025 = 1,
        Revit2026 = 2,
        Revit2027 = 3,
    }

    private const string REVIT_EXECUTABLE_FILE_NAME = "Revit.exe";

    // Keep add-in folder mappings aligned with SupportedRevitVersion entries.
    private static readonly Dictionary<SupportedRevitVersion, string> REVIT_ADDINS_RELATIVE_PATHS =
        new Dictionary<SupportedRevitVersion, string>()
        {
            { SupportedRevitVersion.Revit2024, @".\Autodesk\Revit\Addins\2024" },
            { SupportedRevitVersion.Revit2025, @".\Autodesk\Revit\Addins\2025" },
            { SupportedRevitVersion.Revit2026, @".\Autodesk\Revit\Addins\2026" },
            { SupportedRevitVersion.Revit2027, @".\Autodesk\Revit\Addins\2027" },
        };

    // Canonical version-number text used by config/CLI parsing and display.
    private static readonly Dictionary<SupportedRevitVersion, string> SUPPORTED_REVIT_VERSION_NUMBERS =
        new Dictionary<SupportedRevitVersion, string>()
        {
            { SupportedRevitVersion.Revit2024, "2024" },
            { SupportedRevitVersion.Revit2025, "2025" },
            { SupportedRevitVersion.Revit2026, "2026" },
            { SupportedRevitVersion.Revit2027, "2027" },
        };

    private static Dictionary<SupportedRevitVersion, string> REVIT_EXECUTABLE_FOLDER_PATHS()
    {
        var revitInstallPaths = new Dictionary<SupportedRevitVersion, string>();
        foreach (var versionName in Enum.GetNames(typeof(SupportedRevitVersion)))
        {
            SupportedRevitVersion enumOfVersion = (SupportedRevitVersion)Enum.Parse(typeof(SupportedRevitVersion), versionName);

            var installLocation = GetRevitInstallPath(enumOfVersion);
            if (installLocation == null)
            {
                continue;
            }
            revitInstallPaths.Add(enumOfVersion, GetRevitInstallPath(enumOfVersion));
        }

        return revitInstallPaths;
    }


    public static string GetVersionNumber(SupportedRevitVersion supportedRevitVersion)
    {
        var versionName = Enum.GetName(typeof(SupportedRevitVersion), supportedRevitVersion);
        return versionName?.Remove(0, 5);
    }

    public static string GetAddinPath(SupportedRevitVersion supportedRevitVersion)
    {
        return $".\\Autodesk\\Revit\\Addins\\{GetVersionNumber(supportedRevitVersion)}";
    }

    public static string GetAddinName(SupportedRevitVersion supportedRevitVersion)
    {
        return $"BatchRvtAddin{GetVersionNumber(supportedRevitVersion)}.addin";
    }

    // Keep local working-folder mappings aligned with SupportedRevitVersion entries.
    private static readonly Dictionary<SupportedRevitVersion, string> REVIT_LOCAL_FOLDER_PATHS =
        new Dictionary<SupportedRevitVersion, string>()
        {
            { SupportedRevitVersion.Revit2024, @"C:\REVIT_LOCAL2024" },
            { SupportedRevitVersion.Revit2025, @"C:\REVIT_LOCAL2025" },
            { SupportedRevitVersion.Revit2026, @"C:\REVIT_LOCAL2026" },
            { SupportedRevitVersion.Revit2027, @"C:\REVIT_LOCAL2027" },
        };


    public static string GetRevitInstallPath(SupportedRevitVersion supportedRevitVersion)
    {
        var appPath = $@"SOFTWARE\Autodesk\Revit\{GetVersionNumber(supportedRevitVersion)}";
        if (appPath == null) throw new ArgumentNullException(nameof(appPath));
        using var sk = Registry.LocalMachine.OpenSubKey(appPath);
        if (sk is null) return null;

        string revitSubkey = null;
        foreach (var revitKey in sk.GetSubKeyNames())
        {
            if (!revitKey.Contains("REVIT-")) continue;

            revitSubkey = revitKey;
        }

        if (revitSubkey == null) return null;

        using var rk = sk.OpenSubKey(revitSubkey);
        var installLocation = rk?.GetValue("InstallationLocation");
        return installLocation?.ToString();
    }

    public static string GetRevitExecutableFolderPath(SupportedRevitVersion revitVersion)
    {
        if (GetRevitInstallPath(revitVersion) == null) return null;
        return File.Exists(Path.Combine(GetRevitInstallPath(revitVersion) ?? string.Empty,
            REVIT_EXECUTABLE_FILE_NAME))
            ? GetRevitInstallPath(revitVersion)
            : null;
    }

    public static string GetRevitLocalFolderPath(SupportedRevitVersion revitVersion)
    {
        return REVIT_LOCAL_FOLDER_PATHS.ContainsKey(revitVersion) ?
            REVIT_LOCAL_FOLDER_PATHS[revitVersion] : null;
    }

    public static string GetRevitLocalFilePath(SupportedRevitVersion revitVersion, string centralFilePath)
    {
        string localFilePath = null;

        var localFolderPath = GetRevitLocalFolderPath(revitVersion);

        if (localFolderPath != null)
        {
            var localFileName = Path.GetFileNameWithoutExtension(centralFilePath) + "_" + Environment.UserName + Path.GetExtension(centralFilePath);

            localFilePath = Path.Combine(localFolderPath, localFileName);
        }

        return localFilePath;
    }

    public static IEnumerable<SupportedRevitVersion> GetInstalledRevitVersions()
    {
        return REVIT_EXECUTABLE_FOLDER_PATHS().Keys
            .Where(IsRevitVersionInstalled)
            .Where(BatchRvt.IsBatchRvtAddinInstalled)
            .ToList();
    }

    public static string GetRevitExecutableFilePath(SupportedRevitVersion revitVersion)
    {
        var folderPath = GetRevitExecutableFolderPath(revitVersion);

        return folderPath != null ? Path.Combine(folderPath, REVIT_EXECUTABLE_FILE_NAME) : null;
    }

    public static bool IsRevitVersionInstalled(SupportedRevitVersion revitVersion)
    {
        return File.Exists(GetRevitExecutableFilePath(revitVersion));
    }

    public static SupportedRevitVersion GetMinimumInstalledRevitVersion()
    {
        return GetInstalledRevitVersions().OrderBy(supportedRevitVersion => supportedRevitVersion).FirstOrDefault();
    }


    public static string GetRevitVersionText(SupportedRevitVersion supportedRevitVersion)
    {
        return GetVersionNumber(supportedRevitVersion) ?? "UNSUPPORTED";
    }

    public static bool IsSupportedRevitVersionNumber(string revitVersionNumber)
    {
        return Enum.TryParse($"Revit{revitVersionNumber}", out SupportedRevitVersion _);
    }

    public static SupportedRevitVersion GetSupportedRevitVersion(string revitVersionNumber)
    {
        Enum.TryParse($"Revit{revitVersionNumber}", out SupportedRevitVersion version);
        return version;
    }

    public static string GetRevitAddinsFolderPath(SupportedRevitVersion revitVersion,
        Environment.SpecialFolder specialFolder)
    {
        return Path.Combine(Environment.GetFolderPath(specialFolder), GetAddinPath(revitVersion));
    }
}