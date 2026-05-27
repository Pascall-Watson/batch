using IronPython.Hosting;

Console.WriteLine($"[host] running on .NET {Environment.Version}, OS {Environment.OSVersion}");

var engine = Python.CreateEngine();
Console.WriteLine($"[host] IPy engine language version: {engine.LanguageVersion}");

var scope = engine.CreateScope();
engine.Execute("""
import sys
print(f"[ipy] hello from IronPython {sys.version}")
print(f"[ipy] sys.implementation.name = {sys.implementation.name}")
print(f"[ipy] f-strings work, 1//2 = {1//2}, b'bytes'[0] = {b'bytes'[0]}")
""", scope);

Console.WriteLine("[host] done.");
