#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). Fixes vs 2.7:
#   - Dropped `import exceptions` (Py2-only built-in module; in Py3 the base
#     Python exception class is just `Exception`).
#   - `.message` (Py2-only attribute) → `str(...)`.
#

import clr
import System
from System.Text import StringBuilder

import global_test_mode

EXCEPTION_MESSAGE_HANDLER_PREFIX = "[ EXCEPTION MESSAGE ]"


def GetInterpretedFrameInfo(clsExceptionData):
    interpretedFrameInfo = None
    for kv in clsExceptionData:
        entryName = None
        try:
            entryName = kv.Key.Name
        except:
            pass
        if entryName == "InterpretedFrameInfo":
            interpretedFrameInfo = kv.Value
            break
    return interpretedFrameInfo


def GetClrException(exception):
    if isinstance(exception, System.Exception):
        return exception
    # IronPython attaches the wrapped CLR exception as `.clsException` on Python
    # exceptions originating from CLR code. Use getattr so the absence of the
    # attribute under IPy 3.4 just yields None instead of AttributeError.
    return getattr(exception, "clsException", None)


def LogOutputErrorDetails(exception, output_, verbose=True):
    output = global_test_mode.PrefixedOutputForGlobalTestMode(output_, EXCEPTION_MESSAGE_HANDLER_PREFIX)
    if isinstance(exception, System.Exception):
        exceptionMessage = str(exception.Message)
    else:
        exceptionMessage = str(exception)
    output()
    output("Exception: [" + type(exception).__name__ + "] " + exceptionMessage)
    try:
        clsException = GetClrException(exception)
        if clsException is not None:
            clsExceptionType = clr.GetClrType(type(clsException))
            output(".NET exception: [" + str(clsExceptionType.Name) + "] " + str(clsException.Message))
            if verbose:
                interpretedFrameInfo = GetInterpretedFrameInfo(clsException.Data)
                if interpretedFrameInfo is not None:
                    output()
                    output("Further exception information:")
                    output()
                    for i in interpretedFrameInfo:
                        if str(i) != "CallSite.Target":
                            output("\t" + str(i))
    except:
        output("Could not obtain further exception information.")
    return


def GetExceptionDetails(exception):
    exceptionDetails = StringBuilder()

    def output(message=""):
        exceptionDetails.AppendLine(message)
        return

    LogOutputErrorDetails(exception, output)
    return exceptionDetails.ToString()
