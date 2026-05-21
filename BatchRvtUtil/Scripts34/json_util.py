#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System

clr.AddReference("Newtonsoft.Json")

import Newtonsoft.Json as JSON
from Newtonsoft.Json import JsonConvert, Formatting
from Newtonsoft.Json.Linq import JObject, JArray, JValue

# Py3 treats `None`/`True`/`False` as strict keywords, so `Formatting.None`
# is a syntax error (it was legal attribute access in Py2). Resolve the enum
# value via getattr so we keep the same .NET semantics.
_FORMATTING_NONE = getattr(Formatting, "None")


def GetValueFromJValue(jvalue):
    return JValue.Value.GetValue(jvalue)


def ToJObject(pythonObject):
    return JObject.FromObject(pythonObject)


def DeserializeToJObject(text):
    return JsonConvert.DeserializeObject(text)


def ToString(jobject, prettyPrint=False):
    return (
        JObject.ToString(jobject)
        if prettyPrint
        else JObject.ToString(jobject, _FORMATTING_NONE)
    )


def SerializeObject(pythonObject, prettyPrint=False):
    return ToString(ToJObject(pythonObject), prettyPrint)
