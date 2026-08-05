#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). One fix: `except NameError, e:` → `as e:`.
#

import clr
import System

# NOTE: must not add any references to Revit API modules here because this module
# is allowed to run outside of a Revit application.


def GetRevitVersionNumber(uiapp):
    return uiapp.Application.VersionNumber


def GetSessionUIApplication():
    uiapp = None
    try:
        uiapp = __revit__  # noqa: F821 — injected as a built-in by ScriptUtil.AddBuiltinVariables
    except NameError:
        pass
    return uiapp


def GetSessionRevitVersionNumber():
    uiapp = GetSessionUIApplication()
    revitVersionNumber = GetRevitVersionNumber(uiapp) if uiapp is not None else None
    return revitVersionNumber
