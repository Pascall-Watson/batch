#
# Revit Batch Processor
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax.
#

import clr
import System
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

try:
    clr.AddReference("System.Net.Primitives")
except:
    pass

import batch_rvt_util
from batch_rvt_util import Network


def IsSpecialAddress(address):
    return (
        address.Equals(System.Net.IPAddress.Any)
        or address.Equals(System.Net.IPAddress.Broadcast)
        or address.Equals(System.Net.IPAddress.IPv6Any)
        or address.Equals(System.Net.IPAddress.IPv6Loopback)
        or address.Equals(System.Net.IPAddress.IPv6None)
        or address.Equals(System.Net.IPAddress.Loopback)
    )


def GetGatewayAddresses():
    return list(
        address for address in
        Network.GetGatewayAddresses()
        .Where(lambda a: not IsSpecialAddress(a))
        .Select(lambda a: a.ToString())
        .Distinct()
        .OrderBy(lambda a: a)
    )


def GetIPAddresses():
    return list(
        address for address in
        Network.GetIPAddresses()
        .Where(lambda a: not IsSpecialAddress(a))
        .Select(lambda a: a.ToString())
        .Distinct()
        .OrderBy(lambda a: a)
    )
