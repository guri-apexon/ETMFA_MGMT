import threading
from dataclasses import asdict
from functools import partial

from kombu import Connection

from etmfa.messaging.messagelistener import MessageListener
from etmfa.messaging.models.generic_request import GenericRequest, OmapRequest, DIG2OMAPRequest
from etmfa.messaging.models.processing_status import ProcessingStatus, FeedbackStatus
from etmfa.messaging.models.queue_names import EtmfaQueues
from etmfa.messaging.models.compare_request import CompareRequest
from etmfa.db.feedback_utils import get_latest_file_path
# Added for OMOP
import os
from etmfa.server.config import Config


def msg_listening_worker(app, listener):
    with app.app_context():
        listener.run()


def initialize_msg_listeners(app, connection_str, exchange_name, logger):
    with Connection(connection_str) as conn:
        # consume
        consumer = MessageListener(conn, connection_str, exchange_name, logger=logger)
        consumer = build_queue_callbacks(consumer)

        daemon_handle = threading.Thread(
            name='msg_listener_daemon',
            target=msg_listening_worker,
            args=(app, consumer,))

        daemon_handle.setDaemon(True)
        daemon_handle.start()
        logger.info("Consuming queues...")

    return daemon_handle


def build_queue_callbacks(queue_worker):
    queue_worker.add_listener(EtmfaQueues.TRIAGE.complete, on_triage_complete)
    queue_worker.add_listener(EtmfaQueues.DIGITIZER1.complete,
                              partial(on_generic_complete_event, status=ProcessingStatus.DIGITIZER2_STARTED,
                                      dest_queue_name=EtmfaQueues.DIGITIZER2.request))
    # added for i2e omop update
    queue_worker.add_listener(EtmfaQueues.DIGITIZER2.complete,
                              partial(on_digitizer2_complete_event, status=ProcessingStatus.I2E_OMOP_UPDATE_STARTED,
                                      dest_queue_name=EtmfaQueues.I2E_OMOP_UPDATE.request))
    queue_worker.add_listener(EtmfaQueues.I2E_OMOP_UPDATE.complete,
                              partial(on_i2e_omop_update_complete_event,
                                      status=ProcessingStatus.DIGITIZER2_OMOPUPDATE_STARTED,
                                      dest_queue_name=EtmfaQueues.DIGITIZER2_OMOPUPDATE.request))
    queue_worker.add_listener(EtmfaQueues.DIGITIZER2_OMOPUPDATE.complete,
                              partial(on_generic_complete_event, status=ProcessingStatus.EXTRACTION_STARTED,
                                      dest_queue_name=EtmfaQueues.EXTRACTION.request))

    queue_worker.add_listener(EtmfaQueues.EXTRACTION.complete,
                              partial(on_generic_complete_event, status=ProcessingStatus.FINALIZATION_STARTED,
                                      dest_queue_name=EtmfaQueues.FINALIZATION.request))

    queue_worker.add_listener(EtmfaQueues.FINALIZATION.complete, on_finalization_complete)

    queue_worker.add_listener(EtmfaQueues.COMPARE.complete, on_compare_complete)

    # Feedback Run
    queue_worker.add_listener(EtmfaQueues.FEEDBACK.complete,
                              partial(on_feedback_complete, status=ProcessingStatus.I2E_OMOP_UPDATE_STARTED,
                                      dest_queue_name=EtmfaQueues.I2E_OMOP_UPDATE.request))

    queue_worker.add_listener(EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value, on_documentprocessing_error)

    return queue_worker


def on_generic_complete_event(msg_proc_obj, message_publisher, status, dest_queue_name):
    # TODO: Resolve Circular Dependency
    from etmfa.db import update_doc_processing_status
    update_doc_processing_status(msg_proc_obj['id'], status)
    request = GenericRequest(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], msg_proc_obj['FeedbackRunId'],
                             msg_proc_obj['OutputFilePrefix'])

    message_publisher.send_dict(asdict(request), dest_queue_name)


# omap update
def on_digitizer2_complete_event(msg_proc_obj, message_publisher, status, dest_queue_name):
    from etmfa.db import update_doc_processing_status
    update_doc_processing_status(msg_proc_obj['id'], status)
    try:
        IQVXMLPath = os.path.join(Config.DFS_UPLOAD_FOLDER, msg_proc_obj['id'])
        file = get_latest_file_path(IQVXMLPath, prefix="*.omop", suffix="*.xml*")
    except Exception as e:
        file = None

    request = DIG2OMAPRequest(msg_proc_obj['id'], file, msg_proc_obj['FeedbackRunId'], msg_proc_obj['OutputFilePrefix'])

    message_publisher.send_dict(asdict(request), dest_queue_name)


def on_i2e_omop_update_complete_event(msg_proc_obj, message_publisher, status, dest_queue_name):
    from etmfa.db import get_doc_resource_by_id
    try:
        IQVXMLPath = os.path.join(Config.DFS_UPLOAD_FOLDER, msg_proc_obj['id'])
        Dig_file_path = get_latest_file_path(IQVXMLPath, prefix="D2_", suffix="*.xml*")
        if Dig_file_path:
            file = Dig_file_path
    except Exception as e:
        file = None

    metadata_resource = get_doc_resource_by_id(msg_proc_obj['id'])
    feedback_run_id = metadata_resource.runId
    if feedback_run_id == 0:
        output_file_prefix = ""
    else:
        output_file_prefix = "R" + str(feedback_run_id).zfill(2)

    request = OmapRequest(msg_proc_obj['id'], msg_proc_obj['updated_omop_xml_path'], file, feedback_run_id,
                          output_file_prefix, dest_queue_name)

    message_publisher.send_dict(asdict(request), dest_queue_name)


def on_triage_complete(msg_proc_obj, message_publisher):
    if msg_proc_obj['ocr_required']:
        dest_queue = EtmfaQueues.DIGITIZER1.request
        status = ProcessingStatus.DIGITIZER1_STARTED
    else:
        dest_queue = EtmfaQueues.DIGITIZER2.request
        status = ProcessingStatus.DIGITIZER2_STARTED

    return on_generic_complete_event(msg_proc_obj, message_publisher, status, dest_queue)


def on_finalization_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_finalizationcomplete_event, update_doc_processing_status
    ids_compare_protocol = received_finalizationcomplete_event(msg_proc_obj['id'], msg_proc_obj, message_publisher)

    if ids_compare_protocol:
        dest_queue_name = EtmfaQueues.COMPARE.request
        for row in ids_compare_protocol:
            if row['IQVXMLPath2'] == '':
                import logging
                from etmfa.consts import Consts as consts
                logger = logging.getLogger(consts.LOGGING_NAME)
                logger.info("FIN_ file does not exist for ID {}".format(row['id2']))
                continue
            request = CompareRequest(row['compareId'], row['id1'], row['IQVXMLPath1'], row['id2'], row['IQVXMLPath2'],
                                     row['redact_profile'], dest_queue_name)
            message_publisher.send_dict(asdict(request), dest_queue_name)


def on_feedback_complete(msg_proc_obj, message_publisher, dest_queue_name, status):

    from etmfa.db import update_doc_processing_status, get_doc_resource_by_id
    update_doc_processing_status(msg_proc_obj['id'], status)

    try:
        dfs_folder_path = os.path.join(Config.DFS_UPLOAD_FOLDER, msg_proc_obj['id'])
        IQVXMLPath = get_latest_file_path(dfs_folder_path, prefix="*.omop", suffix="*.xml*")
    except Exception as e:
        IQVXMLPath = None

    request = DIG2OMAPRequest(msg_proc_obj['id'], IQVXMLPath, msg_proc_obj['FeedbackRunId'], msg_proc_obj['OutputFilePrefix'])

    message_publisher.send_dict(asdict(request), dest_queue_name)


def on_compare_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_comparecomplete_event, update_doc_processing_status
    received_comparecomplete_event(msg_proc_obj, message_publisher)


def on_documentprocessing_error(error_obj, message_publisher):
    from etmfa.db import received_documentprocessing_error_event
    received_documentprocessing_error_event(error_obj)
