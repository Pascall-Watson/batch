using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.ExceptionServices;
using System.Runtime.Versioning;
#if !NETFRAMEWORK
using System.Runtime.Loader;
#endif

namespace Batch.ScriptHost.Compatibility
{
    internal static class Program
    {
        private static string payload;
        private static int checks;
        private static readonly Dictionary<string, Assembly> Loaded =
            new Dictionary<string, Assembly>(StringComparer.OrdinalIgnoreCase);

        private static int Main(string[] args)
        {
            try
            {
                Run(args);
                return 0;
            }
            catch (Exception exception)
            {
                Console.Error.WriteLine("FAIL: " + Unwrap(exception));
                return 1;
            }
        }

        private static void Run(string[] args)
        {
            Require(args.Length == 4 || args.Length == 5,
                "Usage: probe payloadDirectory expectedTargetFramework expectedScriptsFolder expectedEngineVersion [addinYear]");
            payload = Path.GetFullPath(args[0]);
            Require(Directory.Exists(payload), "Payload directory exists: " + payload);
            Require(Environment.Is64BitProcess, "Probe is running x64");
            var engineVersion = new Version(args[3]);
            var python3 = engineVersion == new Version(3, 4, 2, 0);
            Require(python3 || engineVersion == new Version(2, 7, 12, 0),
                "Expected engine is exactly 2.7.12.0 or 3.4.2.0");
            var scriptsName = python3 ? "Scripts34" : "Scripts27";
            Require(args[2] == scriptsName, "Expected scripts folder agrees with expected engine");
            if (args.Length == 5)
                Console.WriteLine("Add-in year (label only, handler selection not inspected): " + args[4]);

#if NETFRAMEWORK
            AppDomain.CurrentDomain.AssemblyResolve += Resolve;
#else
            AssemblyLoadContext.Default.Resolving += Resolve;
#endif
            try
            {
                CheckLayout(scriptsName, python3);
                var host = LoadPayload("Batch.Shared.ScriptHost");
                var util = LoadPayload("Batch.Shared.Util");
                CheckFramework(host, args[1]);
                CheckFramework(util, args[1]);
                var ironPython = LoadPayload("IronPython");
                var dynamicAssembly = LoadPayload("Microsoft.Dynamic");
                var scripting = LoadPayload("Microsoft.Scripting");
                var dlrVersion = new Version(python3 ? "1.3.5.0" : "1.3.1.0");
                Require(ironPython.GetName().Version == engineVersion, "IronPython version: " + engineVersion);
                Require(dynamicAssembly.GetName().Version == dlrVersion, "Microsoft.Dynamic version: " + dlrVersion);
                Require(scripting.GetName().Version == dlrVersion, "Microsoft.Scripting version: " + dlrVersion);

                var scriptUtil = host.GetType("Batch.Shared.ScriptHost.ScriptUtil", true);
                var folderField = scriptUtil.GetField("ScriptsFolderName", BindingFlags.Public | BindingFlags.Static);
                Require(folderField != null && Equals(folderField.GetValue(null), scriptsName),
                    "Actual ScriptUtil.ScriptsFolderName matches " + scriptsName);

                // Run the guard before creating an engine. The deliberately invalid folder must
                // fail before the dummy UIApplication can reach any host script or Revit API.
                CheckRuntimeGuard(host, scriptsName);
                var engine = CallStatic(scriptUtil, "CreatePythonEngine");
                Call(engine, "SetSearchPaths", (object)new string[0]);
                var scope = CallStatic(scriptUtil, "CreateMainModule", engine);
                CallStatic(scriptUtil, "AddPythonStandardLibrary", scope);
                Pass("Created engine/main scope and added standard library through actual ScriptUtil");

                var files = Directory.GetFiles(Path.Combine(payload, scriptsName), "*.py", SearchOption.AllDirectories);
                Array.Sort(files, StringComparer.OrdinalIgnoreCase);
                Require(files.Length > 0, "Payload contains Python host scripts");
                foreach (var file in files)
                {
                    try
                    {
                        var source = CallStatic(scriptUtil, "CreateScriptSourceFromFile", engine, file);
                        Call(source, "Compile");
                    }
                    catch (Exception exception)
                    {
                        throw new InvalidOperationException("Compile-only failure: " + file, Unwrap(exception));
                    }
                }
                Pass("Compiled all " + files.Length + " host scripts without executing them");

                if (python3)
                {
                    var original = Path.Combine(FindRepository(), "src", "shared", "Batch.Shared.Util",
                        "Scripts27", "revit_script_host.py");
                    var rejected = false;
                    try
                    {
                        var source = CallStatic(scriptUtil, "CreateScriptSourceFromFile", engine, original);
                        Call(source, "Compile");
                    }
                    catch (Exception exception)
                    {
                        if (Unwrap(exception).GetType().FullName != "Microsoft.Scripting.SyntaxErrorException")
                            throw;
                        rejected = true;
                    }
                    Require(rejected, "IronPython 3 rejects original repository Scripts27 host source");
                }
                else
                {
                    var source = Call(engine, "CreateScriptSourceFromString",
                        "try:\n    pass\nexcept Exception, e:\n    pass\n");
                    Call(source, "Compile");
                    Pass("IronPython 2 accepts Python 2 exception syntax (compile only)");
                }

                // Explicit non-generic Execute(string); no dynamic binder or IronPython references.
                var actualVersion = Convert.ToString(Call(engine, "Execute",
                    "__import__('sys').version_info[:3]"), CultureInfo.InvariantCulture);
                var expectedTuple = python3 ? "(3, 4, 2)" : "(2, 7, 12)";
                Require(actualVersion == expectedTuple, "sys.version_info[:3] = " + actualVersion);
                Call(engine, "Execute",
                    "import sys\nimport os\nimport json\nimport traceback\nimport collections\nimport encodings\n" +
                    "assert json.loads(json.dumps({'probe': [1, 2]}))['probe'] == [1, 2]\n", scope);
                Pass("Standard-library imports and JSON round trip in main scope");
                if (python3)
                {
                    var jsonFile = Convert.ToString(Call(engine, "Execute", "json.__file__", scope));
                    Require(Path.GetFullPath(jsonFile).StartsWith(Path.Combine(payload, "lib") + Path.DirectorySeparatorChar,
                        StringComparison.OrdinalIgnoreCase), "JSON imported from packaged Python 3 standard library");
                }
                else
                {
                    Require(Equals(Call(engine, "Execute", "len(sys.path) == 0 and len(sys.meta_path) > 0", scope), true),
                        "Python 2 imported standard library with no filesystem search paths");
                }
                CheckBindings();
                Console.WriteLine("PASS: " + checks + " checks; " + files.Length + " scripts compiled; no host scripts executed.");
            }
            finally
            {
#if NETFRAMEWORK
                AppDomain.CurrentDomain.AssemblyResolve -= Resolve;
#else
                AssemblyLoadContext.Default.Resolving -= Resolve;
#endif
            }
        }

        private static void CheckLayout(string scriptsName, bool python3)
        {
            Require(Directory.Exists(Path.Combine(payload, scriptsName)), "Matching scripts directory exists");
            Require(!Directory.Exists(Path.Combine(payload, python3 ? "Scripts27" : "Scripts34")),
                "Other engine's scripts directory is absent");
            var lib = Path.Combine(payload, "lib");
            Require(python3 ? File.Exists(Path.Combine(lib, "os.py")) : !Directory.Exists(lib),
                python3 ? "Python 3 loose stdlib exists" : "Python 2 payload has no loose lib directory");
            var nested = Directory.GetDirectories(payload, "*", SearchOption.AllDirectories)
                .Where(path => new[] { "net48", "net8", "net10" }.Any(prefix =>
                {
                    var name = Path.GetFileName(path);
                    return name.Equals(prefix, StringComparison.OrdinalIgnoreCase) ||
                        name.StartsWith(prefix + ".", StringComparison.OrdinalIgnoreCase) ||
                        name.StartsWith(prefix + "-", StringComparison.OrdinalIgnoreCase);
                })).ToArray();
            Require(nested.Length == 0, "No nested framework build-output directories: " + string.Join(", ", nested));
        }

        private static void CheckRuntimeGuard(Assembly host, string scriptsName)
        {
            const string marker = "BATCHRVT__SCRIPT_FILE_PATH";
            var previous = Environment.GetEnvironmentVariable(marker);
            var wrongFolder = scriptsName == "Scripts34" ? "Scripts27" : "Scripts34";
            var rejected = false;
            try
            {
                Environment.SetEnvironmentVariable(marker, "compatibility-probe-dummy-nonempty.py");
                try
                {
                    CallStatic(host.GetType("Batch.Shared.ScriptHost.ScriptHostUtil", true),
                        "ExecuteBatchScriptHost", payload, new object(), wrongFolder);
                }
                catch (Exception exception)
                {
                    var cause = Unwrap(exception);
                    if (!(cause is InvalidOperationException) ||
                        !cause.Message.Contains("Incompatible script-host payload") ||
                        !cause.Message.Contains(scriptsName) || !cause.Message.Contains(wrongFolder))
                        throw;
                    rejected = true;
                }
            }
            finally
            {
                Environment.SetEnvironmentVariable(marker, previous);
            }
            Require(rejected, "Runtime guard rejects mismatched scripts folder before host execution");
        }

        private static void CheckFramework(Assembly assembly, string expected)
        {
            var attribute = assembly.GetCustomAttributes(typeof(TargetFrameworkAttribute), false)
                .Cast<TargetFrameworkAttribute>().SingleOrDefault();
            Require(attribute != null && attribute.FrameworkName == expected,
                assembly.GetName().Name + " TargetFrameworkAttribute = " +
                (attribute == null ? "<missing>" : attribute.FrameworkName) + "; expected " + expected);
        }

#if NETFRAMEWORK
        private static Assembly Resolve(object sender, ResolveEventArgs args)
        {
            return ResolveName(new AssemblyName(args.Name));
        }
#else
        private static Assembly Resolve(AssemblyLoadContext context, AssemblyName name)
        {
            return ResolveName(name);
        }
#endif

        private static Assembly ResolveName(AssemblyName name)
        {
            if (IsRevit(name.Name))
                throw new InvalidOperationException("Revit assembly resolution forbidden: " + name.FullName);
            var file = Path.Combine(payload, name.Name + ".dll");
            if (!File.Exists(file))
                return null; // Framework assemblies may be supplied by the selected runtime.
            var assembly = LoadPayload(name.Name);
            if (IsEngineFamily(name.Name))
                Require(assembly.GetName().FullName == name.FullName,
                    "Resolver bound exact engine/DLR identity: " + name.FullName);
            return assembly;
        }

        private static Assembly LoadPayload(string name)
        {
            Assembly assembly;
            if (Loaded.TryGetValue(name, out assembly))
                return assembly;
            var file = Path.GetFullPath(Path.Combine(payload, name + ".dll"));
            if (!File.Exists(file))
                throw new FileNotFoundException("Required payload assembly missing", file);
#if NETFRAMEWORK
            assembly = Assembly.LoadFrom(file);
#else
            assembly = AssemblyLoadContext.Default.LoadFromAssemblyPath(file);
#endif
            Require(string.Equals(Path.GetFullPath(assembly.Location), file, StringComparison.OrdinalIgnoreCase),
                "Loaded from payload: " + name);
            Loaded.Add(name, assembly);
            return assembly;
        }

        private static void CheckBindings()
        {
            // Audit every loaded consumer, not just ScriptHost: default probing can bypass
            // a resolving event, so the final location and identity checks are essential.
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var assembly in assemblies)
            {
                var name = assembly.GetName().Name;
                Require(!IsRevit(name), "No Revit API loaded: " + name);
                if (assembly == typeof(Program).Assembly || assembly.IsDynamic)
                    continue;
                if (File.Exists(Path.Combine(payload, name + ".dll")) || IsEngineFamily(name) ||
                    name.StartsWith("Batch.", StringComparison.OrdinalIgnoreCase))
                    Require(IsWithinPayload(assembly.Location), "Dependency remains in payload: " + name);
                foreach (var reference in assembly.GetReferencedAssemblies().Where(r => IsEngineFamily(r.Name)))
                {
                    var bound = Assembly.Load(reference);
                    Require(bound.GetName().FullName == reference.FullName,
                        name + " binds exact reference " + reference.FullName);
                    Require(IsWithinPayload(bound.Location), "Referenced engine/DLR assembly stays in payload");
                    Require(AppDomain.CurrentDomain.GetAssemblies().Count(a =>
                        a.GetName().Name.Equals(reference.Name, StringComparison.OrdinalIgnoreCase)) == 1,
                        "Single assembly identity/major loaded for " + reference.Name);
                }
            }
            // Include assemblies loaded during the reference audit.
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                var name = assembly.GetName().Name;
                Require(!IsRevit(name), "Final no-Revit check: " + name);
                if (IsEngineFamily(name))
                    Require(IsWithinPayload(assembly.Location), "Final engine/DLR location: " + name);
            }
        }

        private static bool IsEngineFamily(string name)
        {
            return name.Equals("IronPython", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("IronPython.", StringComparison.OrdinalIgnoreCase) ||
                name.Equals("Microsoft.Dynamic", StringComparison.OrdinalIgnoreCase) ||
                name.Equals("Microsoft.Scripting", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("Microsoft.Scripting.", StringComparison.OrdinalIgnoreCase);
        }

        private static bool IsRevit(string name)
        {
            return name.StartsWith("RevitAPI", StringComparison.OrdinalIgnoreCase);
        }

        private static bool IsWithinPayload(string path)
        {
            return !string.IsNullOrEmpty(path) && Path.GetFullPath(path).StartsWith(
                payload.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar,
                StringComparison.OrdinalIgnoreCase);
        }

        private static string FindRepository()
        {
            for (var directory = new DirectoryInfo(payload); directory != null; directory = directory.Parent)
                if (File.Exists(Path.Combine(directory.FullName, "Batch.sln")))
                    return directory.FullName;
            throw new DirectoryNotFoundException("Python 3 negative control requires payload beneath repository containing Batch.sln");
        }

        private static object CallStatic(Type type, string name, params object[] args)
        {
            return Invoke(type, null, name, BindingFlags.Public | BindingFlags.Static, args);
        }

        private static object Call(object instance, string name, params object[] args)
        {
            return Invoke(instance.GetType(), instance, name, BindingFlags.Public | BindingFlags.Instance, args);
        }

        private static object Invoke(Type type, object instance, string name, BindingFlags flags, object[] args)
        {
            var methods = type.GetMethods(flags).Where(method => method.Name == name &&
                !method.ContainsGenericParameters && method.GetParameters().Length == args.Length &&
                method.GetParameters().Select((parameter, index) =>
                    args[index] == null || parameter.ParameterType.IsInstanceOfType(args[index])).All(match => match)).ToArray();
            if (methods.Length != 1)
                throw new AmbiguousMatchException(type.FullName + "." + name + ": expected one non-generic compatible overload, found " + methods.Length);
            try
            {
                return methods[0].Invoke(instance, args);
            }
            catch (TargetInvocationException exception)
            {
                ExceptionDispatchInfo.Capture(Unwrap(exception)).Throw();
                throw;
            }
        }

        private static Exception Unwrap(Exception exception)
        {
            while (exception is TargetInvocationException && exception.InnerException != null)
                exception = exception.InnerException;
            return exception;
        }

        private static void Require(bool condition, string description)
        {
            if (!condition)
                throw new InvalidOperationException(description);
            Pass(description);
        }

        private static void Pass(string description)
        {
            checks++;
            Console.WriteLine("PASS: " + description);
        }
    }
}