import glob
import logging
import os
from dataclasses import asdict

from etmfa.consts import Consts as consts
from etmfa.messaging.messagepublisher import MessagePublisher
from etmfa.messaging.models.generic_request import FeedbackRun
from etmfa.messaging.models.queue_names import EtmfaQueues
from flask import current_app

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"

def get_latest_file_path(dfs_folder_path, prefix, suffix="*.xml*"):
    """
    Get latest file amound digitized and feedback run
    """
    feedback_pattern = "R??"+prefix+suffix
    digitization_pattern = prefix+suffix

    full_feedback_pattern = os.path.join(dfs_folder_path, feedback_pattern)
    feedback_files = glob.glob(full_feedback_pattern)

    if feedback_files:
        sorted_feedback_files = sorted(feedback_files, reverse=True)
        return sorted_feedback_files[0]

    full_digitization_pattern = os.path.join(dfs_folder_path, digitization_pattern)
    digitization_files = glob.glob(full_digitization_pattern)
    if digitization_files:
        return sorted(digitization_files)[0]



def on_qc_approval_complete(aidoc_id, parent_path):
    """
    Initiate feedback run process
    """
    from etmfa.db import get_doc_resource_by_id, update_doc_resource_by_id

    dest_queue_name = EtmfaQueues.FEEDBACK.request
    # next_run_id = update_run_id(aidoc_id)
    metadata_resource = get_doc_resource_by_id(aidoc_id)
    current_run_id = metadata_resource.runId
    next_run_id = current_run_id + 1
    output_file_prefix = "R" + str(next_run_id).zfill(2)
    # dfs_folder_path = os.path.join(parent_path, aidoc_id)
 
    dig2_xml_path = get_latest_file_path(dfs_folder_path=parent_path, prefix="D2_", suffix="*.xml*")
    qc_json_path = get_latest_file_path(dfs_folder_path=parent_path, prefix="QC_", suffix="*.json")
    feedback_request = FeedbackRun(id=aidoc_id, IQVXMLPath=dig2_xml_path, FeedbackJSONPath=qc_json_path, FeedbackRunId=next_run_id, OutputFilePrefix=output_file_prefix, QUEUE_NAME=dest_queue_name)
    BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
    EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']
    if qc_json_path and dig2_xml_path:
        metadata_resource.runId = next_run_id
        metadata_resource.qcStatus = 'FEEDBACK_RUN'
        _ = update_doc_resource_by_id(aidoc_id=aidoc_id, resource=metadata_resource)
        MessagePublisher(BROKER_ADDR, EXCHANGE).send_dict(asdict(feedback_request), dest_queue_name)
    else:
        logger.warning(f"Could not locate proper: qc_json_path:[{qc_json_path}] OR dig2_xml_path:[{dig2_xml_path}]")
        return False

    return True
