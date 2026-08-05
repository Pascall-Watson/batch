#
# Revit Batch Processor - Cloud Region Utilities
#
# IronPython 3.4 port (Phase 2b), aligned with the Scripts27 region model.
#

import clr

# Cloud region handling for the Revit 2021+ cloud path API:
# ModelPathUtils.ConvertCloudGUIDsToCloudPath(string region, Guid, Guid)
#
# Canonical region codes follow current ACC/Forma region host identifiers.
# Alias inputs (for example EMEA, APAC, UK) normalize to canonical region codes.

# Canonical region codes used by this module.
REGION_DESCRIPTIONS = {
    "US": "United States",
    "EU": "European Union",
    "AUS": "Australia",
    "GBR": "United Kingdom",
    "DEU": "Germany",
    "CAN": "Canada",
    "IND": "India",
    "JPN": "Japan",
}

DEFAULT_REGION = "US"

# Map external aliases to canonical region codes.
REGION_CODE_ALIASES = {
    "APAC": "AUS",
    "AU": "AUS",
    "CA": "CAN",
    "DE": "DEU",
    "EMEA": "EU",
    "GB": "GBR",
    "IN": "IND",
    "JP": "JPN",
    "UK": "GBR",
    "USA": "US",
}

# Priority order when an explicit region cannot be resolved.
FALLBACK_ORDER = ["US", "EU", "AUS", "GBR", "DEU", "CAN", "IND", "JPN"]

# Keywords used to infer canonical regions from discovered API region strings.
REGION_CODE_KEYWORDS = {
    "US": ["CLOUDREGIONUS", "UNITEDSTATES", "US", "USA", "AMERICA"],
    "EU": ["CLOUDREGIONEMEA", "EMEA", "EUROPE", "EU"],
    "AUS": ["AUS", "AUSTRALIA", "APAC"],
    "GBR": ["GBR", "UK", "UNITEDKINGDOM", "BRITAIN"],
    "DEU": ["DEU", "DE", "GERMANY"],
    "CAN": ["CAN", "CA", "CANADA"],
    "IND": ["IND", "IN", "INDIA"],
    "JPN": ["JPN", "JP", "JAPAN"],
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


def _normalize_input_region_code(region_code):
    if region_code is None:
        return None
    normalized = region_code.upper().strip()
    return REGION_CODE_ALIASES.get(normalized, normalized)


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

    region_mapping = {
        "US": cloud_region_us if cloud_region_us is not None else (_find_region_for_code(discovered_regions, "US") or "US"),
        "EU": cloud_region_emea if cloud_region_emea is not None else (_find_region_for_code(discovered_regions, "EU") or "EMEA"),
    }

    for region_code in ["AUS", "GBR", "DEU", "CAN", "IND", "JPN"]:
        region_mapping[region_code] = _find_region_for_code(discovered_regions, region_code) or region_code

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
    normalized_region_code = _normalize_input_region_code(regionCode)
    return REGION_DESCRIPTIONS.get(normalized_region_code, "Unknown Region")


def GetRevitApiRegion(regionCode):
    if regionCode is None:
        regionCode = DEFAULT_REGION
    normalized_region_code = NormalizeRegionCode(regionCode)
    usRegion, _ = _get_revit_api_constants()
    return get_region_api_mapping().get(normalized_region_code, usRegion)


def NormalizeRegionCode(regionCode):
    if regionCode is None:
        return DEFAULT_REGION
    normalized = _normalize_input_region_code(regionCode)
    return normalized if normalized in REGION_DESCRIPTIONS else DEFAULT_REGION


def ValidateRegionCode(regionCode):
    if regionCode is None:
        return True
    normalized = _normalize_input_region_code(regionCode)
    return normalized in REGION_DESCRIPTIONS


def GetFallbackOrder(excludeRegion=None):
    fallbackList = list(FALLBACK_ORDER)
    if excludeRegion is not None:
        normalized_exclude_region = _normalize_input_region_code(excludeRegion)
        if normalized_exclude_region in fallbackList:
            fallbackList.remove(normalized_exclude_region)
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
    else:
        return str(api_constant)


def IsDirectApiMapping(regionCode):
    return ValidateRegionCode(regionCode)


def GetMappingWarnings():
    return []
