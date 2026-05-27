#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). The 2.7 original referenced `e.message` against
# an undefined `e` — broken even in Py2; would NameError if invoked. Fixed here
# to `str(exception)` which also drops the Py2-only `.message` attribute.
#

import clr
import System

DYNAMO_REVIT_MODULE_NOT_FOUND_ERROR_MESSAGE = "Could not load the Dynamo module! There must be EXACTLY ONE VERSION of Dynamo installed!"


def IsDynamoNotFoundException(exception):
    return (
        isinstance(exception, Exception)
        and str(exception) == DYNAMO_REVIT_MODULE_NOT_FOUND_ERROR_MESSAGE
    )
