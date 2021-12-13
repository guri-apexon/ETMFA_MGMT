import logging
import os
from datetime import datetime

import pandas as pd
from etmfa.consts import Consts as consts
from etmfa.db import config
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.server.namespaces.serializers import latest_protocol_contract_fields
# from etmfa.error import ManagementException
# from etmfa.error import ErrorCodes

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"


# def get_iqvxml_file_path(dfs_folder_path, prefix):
#     try:
#         files = os.listdir(dfs_folder_path)
#         file = [file for file in files if file.startswith(prefix)][0]
#         return os.path.join(dfs_folder_path, file)
#     except Exception as ex:
#         logger.error("Could not {} XML file in path: {} {}".format(prefix, dfs_folder_path, str(ex)))
#         exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)

def get_summary_records(aidoc_id, source):
    """
        Fetch the summary record
    """
    all_summary_records = PDProtocolQCSummaryData.query.filter(PDProtocolQCSummaryData.aidocId == aidoc_id,
                                                               PDProtocolQCSummaryData.source == source).all()
    return all_summary_records


def fix_data(value, json_col, max_len, data_type, data_format):
    """
    Makes the data aligned to the required format and length
    """
    if max_len is not None:
        value = value.strip()[:max_len]

    if data_type == 'date':
        try:
            datetime.strptime(value, data_format)
        except ValueError as exc:
            logging.warning(
                f"{json_col} received data [{value}] not matching the expected format[{data_format}], default value used.\nException: {str(exc)}")
            return ''
    return value


def get_updated_qc_summary_record(doc_id, source, summary_dict, is_active_flg=True, qc_approved_by='', FeedbackRunId=0):
    """
    Returns the Updated Summary record table record based on summary_dict
    """
    current_utctime = datetime.utcnow()

    qc_summ_record = PDProtocolQCSummaryData()
    qc_summ_record.aidocId = doc_id
    qc_summ_record.source = source
    qc_summ_record.isActive = is_active_flg
    qc_summ_record.qcApprovedBy = qc_approved_by
    qc_summ_record.timeUpdated = current_utctime
    qc_summ_record.runId = FeedbackRunId

    resource = PDProtocolQCSummaryData.query.filter(PDProtocolQCSummaryData.aidocId == doc_id,
                                                    PDProtocolQCSummaryData.source == source).first()
    if resource:
        qc_summ_record.timeCreated = resource.timeCreated
    else:
        qc_summ_record.timeCreated = current_utctime

    _ = [setattr(qc_summ_record, tab_col,
                 fix_data(summary_dict.get(json_col, config.JSON_DEFAULT_MISSING_VALUE), json_col, max_len, data_type,
                          data_format)) \
         for tab_col, (json_col, max_len, data_type, data_format) in config.summary_table_json_mapper.items()]
    return qc_summ_record


def clean_inputs(protocol_number="", version_number="", approval_date="", aidoc_id="", document_status="", qc_status="",
                 compare_doc_id="") -> dict:
    """
    Clean the input arguments
    """
    cleaned_inputs = dict()

    # Clean the inputs
    cleaned_inputs['protocol_number'] = protocol_number.strip() if protocol_number is not None else ''
    cleaned_inputs['version_number'] = version_number.strip() if version_number is not None else ''
    cleaned_inputs['approval_date'] = approval_date.strip() if approval_date is not None else ''
    cleaned_inputs['aidoc_id'] = aidoc_id.strip() if aidoc_id is not None else ''
    cleaned_inputs['document_status'] = document_status.strip().lower() if document_status is not None else ''
    cleaned_inputs['qc_status'] = qc_status.strip().lower() if qc_status is not None else ''
    cleaned_inputs['compare_doc_id'] = compare_doc_id.strip() if compare_doc_id is not None else ''
    return cleaned_inputs


def validate_inputs(protocol_number="") -> bool:
    """
    Verify if the input arguments are valid to proceed further OR not
    """
    cleaned_inputs = clean_inputs(protocol_number=protocol_number)
    protocol_number = cleaned_inputs.get('protocol_number', '')

    if protocol_number:
        return True
    else:
        return False


def get_filter_conditions(protocol_number, version_number="", approval_date="", aidoc_id="", document_status="") -> (
str, str):
    """
    Build dynamic filter condition based on input arguments
    """
    cleaned_inputs = clean_inputs(protocol_number=protocol_number, version_number=version_number,
                                  approval_date=approval_date, aidoc_id=aidoc_id, document_status=document_status)
    protocol_number = cleaned_inputs.get('protocol_number', '')
    version_number = cleaned_inputs.get('version_number', '')
    approval_date = cleaned_inputs.get('approval_date', '')
    aidoc_id = cleaned_inputs.get('aidoc_id', '')
    document_status = cleaned_inputs.get('document_status', '')

    # Init
    additional_filter = None
    all_filter = None
    order_condition = None

    # Default filter
    default_filter = f"pd_protocol_qc_summary_data.isActive = 1 AND pd_protocol_metadata.protocol = '{protocol_number}'"

    # Build filter based on document Status
    if document_status == 'all':
        all_filter = default_filter
    else:
        document_status = document_status if document_status in config.VALID_DOCUMENT_STATUS else config.DEFAULT_DOCUMENT_STATUS
        document_status_filter = f"pd_protocol_metadata.documentStatus = '{document_status}'"
        all_filter = default_filter + ' AND ' + document_status_filter

    logger.debug(f"Initial all_filter: {all_filter}\n")

    # Build filter based on other input arguments
    if aidoc_id:
        logger.debug("In aidoc_id type ...")
        additional_filter = f"pd_protocol_metadata.id = '{aidoc_id}'"
    elif version_number and approval_date:
        logger.debug("In version_number and approval_date type ...")
        additional_filter = f"pd_protocol_qc_summary_data.versionNumber = '{version_number}' AND CONVERT(VARCHAR(8), pd_protocol_qc_summary_data.approvalDate, 112) = '{approval_date}'"
    elif version_number:
        logger.debug("In version_number type ...")
        additional_filter = f"pd_protocol_qc_summary_data.versionNumber = '{version_number}'"
    elif approval_date:
        logger.debug("In approval_date type ...")
        additional_filter = f"CONVERT(VARCHAR(8), pd_protocol_qc_summary_data.approvalDate, 112) = '{approval_date}'"
    else:
        logger.debug("In [only protocol_number] type ...")

    if additional_filter:
        all_filter = all_filter + ' AND ' + additional_filter

    # order condition
    order_condition = f"pd_protocol_qc_summary_data.approvalDate desc, pd_protocol_metadata.uploadDate desc"

    logger.debug(
        f"Input arguments: protocol={protocol_number}; version_number={version_number}; approval_date={approval_date}; aidoc_id={aidoc_id}; document_status={document_status} \
                  \nDynamic conditions: {all_filter}\n order by {order_condition}")
    return all_filter, order_condition


def get_metadata_dict(field_values) -> dict:
    """
    Assign metadata fields into appropriate field name
    """
    metadata_dict = dict()
    metadata_dict['draftNumber'] = field_values[0]
    metadata_dict['amendmentFlag'] = field_values[1]
    metadata_dict['uploadDate'] = field_values[2]
    metadata_dict['documentFilePath'] = field_values[3]
    metadata_dict['projectId'] = field_values[4]
    metadata_dict['documentStatus'] = field_values[5]
    metadata_dict['protocol'] = field_values[6]
    return metadata_dict


def apply_contract_rules(top_resource: dict, metadata_fields: list, ignore_filepath=False) -> dict:
    """
    Restrict only the fields present in the contract
    """
    indications = []
    approval_date = ''
    metadata_dict = get_metadata_dict(metadata_fields)
    top_resource.update(metadata_dict)
    top_resource['amendmentFlag'] = metadata_dict['amendmentFlag'] if pd.isnull(top_resource['isAmendment']) else \
    top_resource['isAmendment']

    approval_date = approval_date if pd.isnull(top_resource['approvalDate']) else top_resource['approvalDate'].strftime(
        '%Y%m%d')
    top_resource['approvalDate'] = '' if approval_date == config.DEFAULT_DATE_VALUE else approval_date

    _ = indications if pd.isnull(top_resource['indications']) else indications.append(top_resource['indications'])
    top_resource['indications'] = str(indications)

    top_resource['uploadDate'] = '' if pd.isnull(top_resource['uploadDate']) else top_resource['uploadDate'].isoformat()
    restricted_top_resource = {key: ('' if value is None else value) for key, value in top_resource.items() if
                               key in latest_protocol_contract_fields}

    if not ignore_filepath:  # Used in download API
        restricted_top_resource['documentFilePath'] = metadata_dict['documentFilePath']
    return restricted_top_resource


def post_process_resource(resources, multiple_records=False) -> dict:
    """
    Align the resources based on the API contract
    """
    top_resource = None

    if multiple_records and resources is not None and type(resources) == list and len(resources) > 0:
        resource_list = []
        logger.debug(f"\nALL_RESPONSE:")
        for idx, resource in enumerate(resources):
            logger.debug(f"\n----- Processing for {idx} resource...")
            resource_dict = resource[0].as_dict()

            resource_dict = apply_contract_rules(top_resource=resource_dict, metadata_fields=resource[1:],
                                                 ignore_filepath=True)
            resource_list.append(resource_dict)

        first_row = resources[0]
        top_resource = first_row[0].as_dict()

        top_resource = apply_contract_rules(top_resource=top_resource, metadata_fields=first_row[1:],
                                            ignore_filepath=True)
        top_resource['allVersions'] = resource_list

    elif not multiple_records and resources is not None:
        logger.debug(f"\nTOP_1_RESPONSE:")
        top_resource = resources[0].as_dict()

        top_resource = apply_contract_rules(top_resource=top_resource, metadata_fields=resources[1:],
                                            ignore_filepath=False)
    else:
        logger.warning(f"No data for post process")

    logger.debug(f"top_resource:\n{top_resource}")
    return top_resource


def filter_qc_status(resources, qc_status):
    """
        Filter the results based on qc_status
    """
    qc_status = qc_status if qc_status in config.VALID_QC_STATUS else config.DEFAULT_QC_STATUS

    if resources is not None and type(resources) == list and len(resources) > 0:
        if qc_status == config.DEFAULT_QC_STATUS:
            resources = [resource for resource in resources if resource.source == 'QC']
        else:
            resources = [resource for resource in resources if resource.rank == 1]

    return resources
