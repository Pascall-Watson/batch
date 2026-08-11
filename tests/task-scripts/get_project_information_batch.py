# -*- coding: utf-8 -*-

import clr
clr.AddReference("RevitAPI")

import json
import os
import traceback

from Autodesk.Revit.DB import StorageType
from System import DateTime, Environment

import revit_script_util
from revit_script_util import Output


SUMMARY_HEADERS = [
    "timestamp_utc",
    "session_id",
    "document_title",
    "revit_file_path",
    "is_cloud_model",
    "cloud_project_id",
    "cloud_model_id",
    "project_number",
    "project_name",
    "client_name",
    "building_name",
    "organization_name",
    "organization_description",
    "project_status",
    "issue_date",
    "project_address",
    "parameter_count",
]


def safe_unicode(raw_value):
    """Return value as unicode for IronPython 2.7-safe serialization."""
    if raw_value is None:
        return u""
    if isinstance(raw_value, unicode):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return raw_value.decode("utf-8")
        except Exception:
            try:
                return raw_value.decode("latin-1")
            except Exception:
                return raw_value.decode("ascii", "replace")
    try:
        return unicode(raw_value)
    except Exception:
        return u""


def get_element_id_value(element_id):
    """Return ElementId numeric value across Revit versions."""
    if element_id is None:
        return -1
    try:
        return element_id.Value
    except AttributeError:
        return element_id.IntegerValue


def safe_json_number(raw_value):
    """Return a JSON-serializable number for IronPython 2.7.

    IronPython 2.7's bundled json module cannot serialize `long`, so coerce
    to int when possible and fall back to unicode for out-of-range values.
    """
    if raw_value is None:
        return -1
    try:
        return int(raw_value)
    except Exception:
        return safe_unicode(raw_value)


def clean_file_name(raw_name):
    """Return a filesystem-safe file name token."""
    safe_name = safe_unicode(raw_name)
    if not safe_name:
        return u"unnamed"
    cleaned = u"".join(
        c if c.isalnum() or c in (u"_", u"-", u".") else u"_"
        for c in safe_name
    )
    cleaned = cleaned.strip(u"_.")
    return cleaned if cleaned else u"unnamed"


def csv_escape(raw_value):
    value = safe_unicode(raw_value)
    value = value.replace(u'"', u'""')
    return u'"' + value + u'"'


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_export_folder_path():
    """Prefer data export folder, then session folder, then user Documents."""
    candidate_paths = [
        safe_unicode(revit_script_util.GetDataExportFolderPath()),
        safe_unicode(revit_script_util.GetSessionDataFolderPath()),
    ]

    for candidate_path in candidate_paths:
        if candidate_path and candidate_path.strip():
            ensure_directory(candidate_path)
            return candidate_path

    fallback = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
    fallback = safe_unicode(fallback)
    ensure_directory(fallback)
    return fallback


def safe_project_info_property(project_info, property_name):
    try:
        return safe_unicode(getattr(project_info, property_name))
    except Exception:
        return u""


def safe_as_value_string(parameter):
    try:
        value = parameter.AsValueString()
        return safe_unicode(value)
    except Exception:
        return u""


def get_parameter_value(parameter):
    if parameter is None or not parameter.HasValue:
        return None

    storage_type = parameter.StorageType

    if storage_type == StorageType.String:
        return safe_unicode(parameter.AsString())

    if storage_type == StorageType.Integer:
        display_value = safe_as_value_string(parameter)
        if display_value:
            return display_value
        return safe_unicode(parameter.AsInteger())

    if storage_type == StorageType.Double:
        display_value = safe_as_value_string(parameter)
        if display_value:
            return display_value
        return safe_unicode(parameter.AsDouble())

    if storage_type == StorageType.ElementId:
        display_value = safe_as_value_string(parameter)
        if display_value:
            return display_value
        element_id = parameter.AsElementId()
        if element_id is None:
            return None
        return safe_unicode(get_element_id_value(element_id))

    display_value = safe_as_value_string(parameter)
    return display_value if display_value else None


def get_model_name_token(document_title, revit_file_path):
    if revit_file_path:
        try:
            file_name = os.path.basename(revit_file_path)
            file_stem = os.path.splitext(file_name)[0]
            if file_stem:
                return clean_file_name(file_stem)
        except Exception:
            pass
    return clean_file_name(document_title)


def collect_project_info_payload(document):
    project_info = document.ProjectInformation
    if project_info is None:
        raise Exception("Document.ProjectInformation returned None.")

    project_info_data = {
        "element_id": safe_json_number(get_element_id_value(project_info.Id)),
        "project_number": safe_project_info_property(project_info, "Number"),
        "project_name": safe_project_info_property(project_info, "Name"),
        "client_name": safe_project_info_property(project_info, "ClientName"),
        "building_name": safe_project_info_property(project_info, "BuildingName"),
        "organization_name": safe_project_info_property(project_info, "OrganizationName"),
        "organization_description": safe_project_info_property(project_info, "OrganizationDescription"),
        "project_status": safe_project_info_property(project_info, "Status"),
        "issue_date": safe_project_info_property(project_info, "IssueDate"),
        "project_address": safe_project_info_property(project_info, "Address"),
        "parameters": [],
    }

    for parameter in project_info.Parameters:
        if parameter is None:
            continue
        try:
            definition = parameter.Definition
            parameter_name = safe_unicode(definition.Name) if definition is not None else u"Unnamed Parameter"
        except Exception:
            parameter_name = u"Unnamed Parameter"

        parameter_value = get_parameter_value(parameter)
        if parameter_value is None:
            continue

        project_info_data["parameters"].append({
            "name": parameter_name,
            "value": safe_unicode(parameter_value),
        })

    project_info_data["parameters"].sort(key=lambda row: row["name"].lower())
    return project_info_data


def write_json_utf8(file_path, data):
    json_text = json.dumps(data, indent=4, ensure_ascii=False)
    with open(file_path, "wb") as output_stream:
        output_stream.write(json_text.encode("utf-8"))


def append_csv_row(csv_path, row_data):
    create_header = not os.path.exists(csv_path)

    with open(csv_path, "ab") as csv_stream:
        if create_header:
            csv_stream.write(u"\ufeff".encode("utf-8"))
            header_line = u",".join([csv_escape(header) for header in SUMMARY_HEADERS])
            csv_stream.write((header_line + u"\r\n").encode("utf-8"))

        row_line = u",".join([
            csv_escape(row_data.get(header, u""))
            for header in SUMMARY_HEADERS
        ])
        csv_stream.write((row_line + u"\r\n").encode("utf-8"))


def build_context(document, project_info_data):
    session_id = safe_unicode(revit_script_util.GetSessionId())
    revit_file_path = safe_unicode(revit_script_util.GetRevitFilePath())
    document_title = safe_unicode(document.Title)

    is_cloud_model = False
    cloud_project_id = u""
    cloud_model_id = u""

    try:
        is_cloud_model = bool(revit_script_util.IsCloudModel())
    except Exception:
        is_cloud_model = False

    if is_cloud_model:
        try:
            cloud_project_id = safe_unicode(revit_script_util.GetCloudProjectId())
            cloud_model_id = safe_unicode(revit_script_util.GetCloudModelId())
        except Exception:
            cloud_project_id = u""
            cloud_model_id = u""

    timestamp_utc = safe_unicode(DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss"))

    payload = {
        "timestamp_utc": timestamp_utc,
        "session_id": session_id,
        "document_title": document_title,
        "revit_file_path": revit_file_path,
        "is_cloud_model": is_cloud_model,
        "cloud_project_id": cloud_project_id,
        "cloud_model_id": cloud_model_id,
        "project_information": project_info_data,
    }

    summary_row = {
        "timestamp_utc": timestamp_utc,
        "session_id": session_id,
        "document_title": document_title,
        "revit_file_path": revit_file_path,
        "is_cloud_model": safe_unicode(is_cloud_model),
        "cloud_project_id": cloud_project_id,
        "cloud_model_id": cloud_model_id,
        "project_number": project_info_data.get("project_number", u""),
        "project_name": project_info_data.get("project_name", u""),
        "client_name": project_info_data.get("client_name", u""),
        "building_name": project_info_data.get("building_name", u""),
        "organization_name": project_info_data.get("organization_name", u""),
        "organization_description": project_info_data.get("organization_description", u""),
        "project_status": project_info_data.get("project_status", u""),
        "issue_date": project_info_data.get("issue_date", u""),
        "project_address": project_info_data.get("project_address", u""),
        "parameter_count": safe_unicode(len(project_info_data.get("parameters", []))),
    }

    return payload, summary_row


def main():
    Output("")
    Output("Running project information export task...")

    document = revit_script_util.GetScriptDocument()
    if document is None:
        Output("ERROR: No active script document available from Revit Batch Processor.")
        return

    try:
        project_info_data = collect_project_info_payload(document)
        payload, summary_row = build_context(document, project_info_data)

        export_folder_path = get_export_folder_path()
        session_token = clean_file_name(payload.get("session_id", u"session"))
        model_token = get_model_name_token(
            payload.get("document_title", u""),
            payload.get("revit_file_path", u""),
        )

        json_file_path = os.path.join(
            export_folder_path,
            u"{0}_ProjectInfo.json".format(model_token),
        )
        csv_file_path = os.path.join(
            export_folder_path,
            u"ProjectInfo_Summary_{0}.csv".format(session_token),
        )

        write_json_utf8(json_file_path, payload)
        append_csv_row(csv_file_path, summary_row)

        Output("Project information export complete.")
        Output("Model: {0}".format(summary_row.get("document_title", u"")))
        Output("Project Number: {0}".format(summary_row.get("project_number", u"")))
        Output("Project Name: {0}".format(summary_row.get("project_name", u"")))
        Output("Client Name: {0}".format(summary_row.get("client_name", u"")))
        Output("JSON Output: {0}".format(json_file_path))
        Output("CSV Summary: {0}".format(csv_file_path))

    except Exception as error:
        Output("ERROR: Failed to export project information.")
        Output(safe_unicode(error))
        Output(traceback.format_exc())


main()
