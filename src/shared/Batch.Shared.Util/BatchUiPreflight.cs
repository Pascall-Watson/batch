using System.Linq;
using System.Text;

namespace Batch.Shared.Util;

public static class BatchUiPreflight
{
    public const string WindowTitle = "Revit Batch Processor";

    public static bool HasAnyInstalledBatchRvtAddin()
    {
        return RevitVersion.GetInstalledRevitVersions().Any();
    }

    public static string BuildMissingAddinErrorMessage()
    {
        var errorMessage = new StringBuilder();
        errorMessage.AppendLine(
            "ERROR: Could not detect the BatchRvt addin for any version of Revit installed on this machine!");
        errorMessage.AppendLine();
        errorMessage.AppendLine("You must first install the BatchRvt addin for at least one version of Revit.");

        return errorMessage.ToString();
    }
}
