#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

import win32_pinvoke
import System.Runtime.InteropServices as Interop

MPR_MODULE_NAME = "mpr.dll"
WNETGETCONNECTION_FUNCTION_NAME = "WNetGetConnection"
REMOTE_NAME_MAX_LENGTH = 1024
NO_ERROR = 0

WNetGetConnectionWinApiFunc = win32_pinvoke.GetWinApiFunctionUnicode(
    WNETGETCONNECTION_FUNCTION_NAME,
    MPR_MODULE_NAME,
    System.Int32,                # Return value
    System.String,               # [in] lpLocalName
    System.Text.StringBuilder,   # [out] lpRemoteName
    System.IntPtr,               # [in, out] lpnLength
)


def WNetGetConnection(localName):
    remoteName = None
    length = REMOTE_NAME_MAX_LENGTH
    remoteNameBuffer = System.Text.StringBuilder(REMOTE_NAME_MAX_LENGTH)
    pLength = Interop.Marshal.AllocHGlobal(Interop.Marshal.SizeOf(length))
    Interop.Marshal.StructureToPtr(length, pLength, False)
    result = WNetGetConnectionWinApiFunc(localName, remoteNameBuffer, pLength)
    Interop.Marshal.FreeHGlobal(pLength)
    if result == NO_ERROR:
        remoteName = remoteNameBuffer.ToString()
    return remoteName
