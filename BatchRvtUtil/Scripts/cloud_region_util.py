#
# Revit Batch Processor - Cloud Region Utilities
#
# Copyright (c) 2020  Dan Rumery, BVN
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import clr

# Constants for hardcoded region strings (no official API support, not sure this is correct either...maybe 'APAC'?)
AUSTRALIA_REGION_STRING = "AUS"

# https://aps.autodesk.com/blog/expanding-regional-offerings-uk-germany-japan-india-and-canada
# On June 30, Autodesk announced the availability of five (5) additional regions as a primary storage location for your project data for certain Autodesk Construction Cloud (ACC) products:
# the United Kingdom, Germany, Japan, Canada, and India.
# For example, as a primary account admin , you can create an ACC hub in any of the regions above for your team in manage.autodesk.com and activate an Autodesk BIM Collaborate account.
# The newly created ACC account will use the specified region as the primary storage location for your Autodesk BIM Collaborate project data.
# no idea what the region strings are for these...

# Mapping of user-friendly region codes to their descriptions and geographic coverage
REGION_DESCRIPTIONS = {
    "US": "United States East Region",
    "AUS": "Australia",
    "EU": "Europe, Middle East, Africa",
    "APAC": "Asia-Pacific, Australia",
}

# Default region when none is specified
DEFAULT_REGION = "US"

# Priority order for fallback attempts
FALLBACK_ORDER = ["US", "EU", "APAC"]

# Keywords used to infer region identity from dynamically discovered region names.
REGION_CODE_KEYWORDS = {
    "US": ["CLOUDREGIONUS", "UNITEDSTATES", "US", "USA", "AMERICA"],
    "EU": ["CLOUDREGIONEMEA", "EMEA", "EUROPE", "EU", "UK", "GERMANY", "MIDDLE", "AFRICA"],
    "APAC": ["APAC", "ASIA", "PACIFIC", "JAPAN", "INDIA", "SINGAPORE"],
    "AUS": ["AUS", "AUSTRALIA"],
}


def _append_unique(values, value):
    if value is None:
        return
    for existing in values:
        if existing == value:
            return
    values.append(value)


def _to_region_text(region_value):
    try:
        return str(region_value).upper()
    except:
        return ""


def _get_model_path_utils():
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import ModelPathUtils
    return ModelPathUtils


def _try_get_all_cloud_regions(model_path_utils):
    regions = []
    if hasattr(model_path_utils, "GetAllCloudRegions"):
        try:
            discovered_regions = model_path_utils.GetAllCloudRegions()
            if discovered_regions is not None:
                for region in discovered_regions:
                    _append_unique(regions, region)
        except Exception:
            pass
    return regions


def _try_get_legacy_cloud_regions(model_path_utils):
    regions = []
    if hasattr(model_path_utils, "CloudRegionUS"):
        _append_unique(regions, model_path_utils.CloudRegionUS)
    if hasattr(model_path_utils, "CloudRegionEMEA"):
        _append_unique(regions, model_path_utils.CloudRegionEMEA)
    return regions


def _find_region_by_keywords(regions, keywords):
    for region in regions:
        region_text = _to_region_text(region)
        for keyword in keywords:
            if region_text == keyword or region_text.find(keyword) >= 0:
                return region
    return None


def _find_region_for_code(regions, region_code):
    keywords = REGION_CODE_KEYWORDS.get(region_code, [])
    return _find_region_by_keywords(regions, keywords)


def _get_discovered_regions():
    model_path_utils = _get_model_path_utils()
    regions = []
    for region in _try_get_all_cloud_regions(model_path_utils):
        _append_unique(regions, region)
    for region in _try_get_legacy_cloud_regions(model_path_utils):
        _append_unique(regions, region)
    return regions


def _get_revit_api_constants():
    """
    Lazy loading function to import RevitAPI only when needed.
    This prevents import errors when the script is loaded without Revit access.

    Returns:
        tuple: (ModelPathUtils.CloudRegionUS, ModelPathUtils.CloudRegionEMEA)
    """
    model_path_utils = _get_model_path_utils()
    discovered_regions = _get_discovered_regions()

    us_region = model_path_utils.CloudRegionUS if hasattr(model_path_utils, "CloudRegionUS") else None
    emea_region = model_path_utils.CloudRegionEMEA if hasattr(model_path_utils, "CloudRegionEMEA") else None

    if us_region is None:
        us_region = _find_region_for_code(discovered_regions, "US")
    if us_region is None and len(discovered_regions) > 0:
        us_region = discovered_regions[0]

    if emea_region is None:
        emea_region = _find_region_for_code(discovered_regions, "EU")
    if emea_region is None:
        emea_region = us_region

    return us_region, emea_region


def GetDiscoveredApiRegions():
    """
    Returns all discoverable cloud regions from the active Revit API.

    Returns:
        list: Region constants/strings accepted by ConvertCloudGUIDsToCloudPath.
    """
    regions = _get_discovered_regions()
    return regions[:]


def get_region_api_mapping():
    """
    Get the mapping of user-friendly region codes to actual Revit API constants.
    Uses lazy loading to avoid importing RevitAPI until needed.

    Returns:
        dict: Mapping of region codes to API constants
    """
    cloud_region_us, cloud_region_emea = _get_revit_api_constants()
    discovered_regions = _get_discovered_regions()

    apac_region = _find_region_for_code(discovered_regions, "APAC")
    aus_region = _find_region_for_code(discovered_regions, "AUS")

    if apac_region is None:
        apac_region = aus_region

    if aus_region is None:
        aus_region = apac_region if apac_region is not None else AUSTRALIA_REGION_STRING

    region_mapping = {}
    if cloud_region_us is not None:
        region_mapping["US"] = cloud_region_us
    if cloud_region_emea is not None:
        region_mapping["EU"] = cloud_region_emea
    if apac_region is not None:
        region_mapping["APAC"] = apac_region
    region_mapping["AUS"] = aus_region

    return region_mapping


def get_unrecognised_region_msg():
    region_mapping = get_region_api_mapping()
    msg = "ERROR: Could not establish a valid Cloud Model Path using the region values {}."
    return msg.format(", ".join(sorted(region_mapping.keys())))


def GetSupportedRegions():
    """
    Returns a dictionary of all supported region codes with their descriptions.

    Returns:
        dict: Region code -> Description mapping
    """
    return REGION_DESCRIPTIONS.copy()


def GetRegionDescription(regionCode):
    """
    Get the human-readable description for a region code.

    Args:
        regionCode (str): Region code (e.g., 'US', 'EU')

    Returns:
        str: Human-readable description or 'Unknown Region' if not found
    """
    if regionCode is None:
        return GetRegionDescription(DEFAULT_REGION)

    return REGION_DESCRIPTIONS.get(regionCode.upper(), "Unknown Region")


def GetRevitApiRegion(regionCode):
    """
    Get the Revit API constant for a given region code.

    Args:
        regionCode (str): User-friendly region code

    Returns:
        Revit API CloudRegion constant or hardcoded string
    """
    if regionCode is None:
        regionCode = DEFAULT_REGION

    normalized_region_code = NormalizeRegionCode(regionCode)
    usRegion, euRegion = _get_revit_api_constants()
    regionMapping = get_region_api_mapping()

    return regionMapping.get(normalized_region_code, usRegion)


def NormalizeRegionCode(regionCode):
    """
    Normalize a region code to uppercase and validate it.

    Args:
        regionCode (str): Region code to normalize

    Returns:
        str: Normalized region code or DEFAULT_REGION if invalid
    """
    if regionCode is None:
        return DEFAULT_REGION

    normalized = regionCode.upper().strip()
    return normalized if normalized in REGION_DESCRIPTIONS else DEFAULT_REGION


def ValidateRegionCode(regionCode):
    """
    Validate if a region code is supported.

    Args:
        regionCode (str): Region code to validate

    Returns:
        bool: True if supported, False otherwise
    """
    if regionCode is None:
        return True  # None is valid (defaults to DEFAULT_REGION)

    return regionCode.upper() in REGION_DESCRIPTIONS


def GetFallbackOrder(excludeRegion=None):
    """
    Get the fallback order for region attempts, optionally excluding a specific region.

    Args:
        excludeRegion (str): Region to exclude from fallback list

    Returns:
        list: Ordered list of region codes for fallback attempts
    """
    fallbackList = FALLBACK_ORDER.copy()

    if excludeRegion is not None:
        excludeRegion = excludeRegion.upper()
        if excludeRegion in fallbackList:
            fallbackList.remove(excludeRegion)

    return fallbackList


def GetRegionMapping():
    """
    Get the complete mapping of user regions to Revit API regions.
    Useful for debugging and documentation.

    Returns:
        dict: Region code -> (API constant, description) mapping
    """
    mapping = {}
    for regionCode in REGION_DESCRIPTIONS:
        api_constant = GetRevitApiRegion(regionCode)
        mapping[regionCode] = {
            "api_constant": api_constant,
            "description": GetRegionDescription(regionCode),
            "api_region_name": GetApiRegionName(api_constant),
        }
    return mapping


def GetApiRegionName(api_constant):
    """
    Get the string representation of an API constant.

    Args:
        api_constant: The API constant or string

    Returns:
        str: String representation of the API region
    """
    cloud_region_us, cloud_region_emea = _get_revit_api_constants()

    if cloud_region_us is not None and api_constant == cloud_region_us:
        return "CloudRegionUS"
    elif cloud_region_emea is not None and api_constant == cloud_region_emea:
        return "CloudRegionEMEA"
    elif api_constant == AUSTRALIA_REGION_STRING:
        return "{0} (hardcoded)".format(AUSTRALIA_REGION_STRING)
    else:
        return str(api_constant)


def IsDirectApiMapping(regionCode):
    """
    Check if a region code maps directly to a Revit API constant or is approximated.

    Args:
        regionCode (str): Region code to check

    Returns:
        bool: True if direct mapping, False if approximated
    """
    api_constant = GetRevitApiRegion(regionCode)
    return api_constant != AUSTRALIA_REGION_STRING


def GetMappingWarnings():
    """
    Get warnings about regions that don't have direct API mappings.

    Returns:
        list: List of warning messages for approximated regions
    """
    warnings = []
    for regionCode in sorted(REGION_DESCRIPTIONS.keys()):
        api_constant = GetRevitApiRegion(regionCode)
        if api_constant == AUSTRALIA_REGION_STRING:
            warnings.append(
                "Region '{0}' ({1}) uses hardcoded '{2}' string - no official Revit API support yet.".format(
                    regionCode,
                    GetRegionDescription(regionCode),
                    AUSTRALIA_REGION_STRING,
                )
            )
    return warnings


def GetAustraliaRegionString():
    """
    Get the hardcoded Australia region string.
    Useful for external code that needs to check against this value.

    Returns:
        str: The Australia region string constant
    """
    return AUSTRALIA_REGION_STRING
