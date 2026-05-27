#
# Revit Batch Processor - Cloud Region Utilities
#
# IronPython 3.4 port (Phase 2b). The original is already Py3-compatible
# (uses .format(), hasattr, no Py2-specific syntax). Copied verbatim.
#

import clr

# Constants for hardcoded region strings (no official API support, not sure this is correct either...maybe 'APAC'?)
AUSTRALIA_REGION_STRING = "AUS"

# Mapping of user-friendly region codes to their descriptions and geographic coverage
REGION_DESCRIPTIONS = {
    "US": "United States East Region",
    "AUS": "Australia",
    "EU": "Europe, Middle East, Africa",
    "APAC": "Asia-Pacific, Australia",
}

DEFAULT_REGION = "US"
FALLBACK_ORDER = ["US", "EU", "APAC"]

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
    return _find_region_by_keywords(regions, REGION_CODE_KEYWORDS.get(region_code, []))


def _get_discovered_regions():
    model_path_utils = _get_model_path_utils()
    regions = []
    for region in _try_get_all_cloud_regions(model_path_utils):
        _append_unique(regions, region)
    for region in _try_get_legacy_cloud_regions(model_path_utils):
        _append_unique(regions, region)
    return regions


def _get_revit_api_constants():
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
    return _get_discovered_regions()[:]


def get_region_api_mapping():
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
    return REGION_DESCRIPTIONS.copy()


def GetRegionDescription(regionCode):
    if regionCode is None:
        return GetRegionDescription(DEFAULT_REGION)
    return REGION_DESCRIPTIONS.get(regionCode.upper(), "Unknown Region")


def GetRevitApiRegion(regionCode):
    if regionCode is None:
        regionCode = DEFAULT_REGION
    normalized_region_code = NormalizeRegionCode(regionCode)
    usRegion, euRegion = _get_revit_api_constants()
    return get_region_api_mapping().get(normalized_region_code, usRegion)


def NormalizeRegionCode(regionCode):
    if regionCode is None:
        return DEFAULT_REGION
    normalized = regionCode.upper().strip()
    return normalized if normalized in REGION_DESCRIPTIONS else DEFAULT_REGION


def ValidateRegionCode(regionCode):
    if regionCode is None:
        return True
    return regionCode.upper() in REGION_DESCRIPTIONS


def GetFallbackOrder(excludeRegion=None):
    fallbackList = FALLBACK_ORDER.copy()
    if excludeRegion is not None:
        excludeRegion = excludeRegion.upper()
        if excludeRegion in fallbackList:
            fallbackList.remove(excludeRegion)
    return fallbackList


def GetRegionMapping():
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
    return GetRevitApiRegion(regionCode) != AUSTRALIA_REGION_STRING


def GetMappingWarnings():
    warnings = []
    for regionCode in sorted(REGION_DESCRIPTIONS.keys()):
        api_constant = GetRevitApiRegion(regionCode)
        if api_constant == AUSTRALIA_REGION_STRING:
            warnings.append(
                "Region '{0}' ({1}) uses hardcoded '{2}' string - no official Revit API support yet.".format(
                    regionCode, GetRegionDescription(regionCode), AUSTRALIA_REGION_STRING,
                )
            )
    return warnings


def GetAustraliaRegionString():
    return AUSTRALIA_REGION_STRING
