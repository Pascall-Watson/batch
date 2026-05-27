#
# Revit Batch Processor
#
# Copyright (c) 2020  Dan Rumery, BVN
#
# IronPython 3.4 port (Phase 2b). No Py2-specific syntax in the original.
#

import clr
import System
from System import DateTime
from System.Globalization import CultureInfo, DateTimeStyles

ISO8601_FORMAT_LOCAL = "yyyy-MM-ddTHH:mm:ss.fff"
ISO8601_FORMAT_UTC = "yyyy-MM-ddTHH:mm:ss.fffZ"


def GetDateTimeNow():
    return DateTime.Now


def GetDateTimeUtcNow():
    return DateTime.UtcNow


def GetISO8601FormattedUtcDate(dateTime):
    return dateTime.ToUniversalTime().ToString(ISO8601_FORMAT_UTC)


def GetISO8601FormattedLocalDate(dateTime):
    return dateTime.ToLocalTime().ToString(ISO8601_FORMAT_LOCAL)


def GetTimestampObject(dateTime):
    return {
        "local": GetISO8601FormattedLocalDate(dateTime),
        "utc": GetISO8601FormattedUtcDate(dateTime),
    }


def GetDateTimeDifferenceInSeconds(startDateTime, endDateTime):
    return int((endDateTime - startDateTime).TotalSeconds)


def GetSecondsElapsedSince(dateTime):
    return GetDateTimeDifferenceInSeconds(dateTime, GetDateTimeNow())


def GetSecondsElapsedSinceUtc(utcDateTime):
    return GetDateTimeDifferenceInSeconds(utcDateTime, GetDateTimeUtcNow())


def GetDateTimeFromISO8601FormattedDate(isoFormattedDate):
    return DateTime.ParseExact(
        isoFormattedDate,
        ISO8601_FORMAT_LOCAL,
        CultureInfo.InvariantCulture,
    )


def GetDateTimeUtcFromISO8601FormattedDate(isoFormattedDate):
    return DateTime.ParseExact(
        isoFormattedDate,
        ISO8601_FORMAT_UTC,
        CultureInfo.InvariantCulture,
        DateTimeStyles.AdjustToUniversal,
    )


def WithMeasuredTimeElapsed(action):
    start = DateTime.Now
    result = action()
    end = DateTime.Now
    return result, (end - start)
