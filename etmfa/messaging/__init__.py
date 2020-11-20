import threading
from dataclasses import asdict
from functools import partial

from kombu import Connection

from etmfa.messaging.messagelistener import MessageListener
from etmfa.messaging.models.generic_request import GenericRequest
from etmfa.messaging.models.processing_status import ProcessingStatus, FeedbackStatus
from etmfa.messaging.models.queue_names import EtmfaQueues


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
    queue_worker.add_listener(EtmfaQueues.DIGITIZER2.complete,
                              partial(on_generic_complete_event, status=ProcessingStatus.EXTRACTION_STARTED,
                                      dest_queue_name=EtmfaQueues.EXTRACTION.request))
    queue_worker.add_listener(EtmfaQueues.EXTRACTION.complete,
                                  partial(on_generic_complete_event, status=ProcessingStatus.FINALIZATION_STARTED,
                                          dest_queue_name=EtmfaQueues.FINALIZATION.request))

    queue_worker.add_listener(EtmfaQueues.FINALIZATION.complete, on_finalization_complete)
    queue_worker.add_listener(EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value, on_documentprocessing_error)

    return queue_worker



def on_generic_complete_event(msg_proc_obj, message_publisher, status, dest_queue_name):
    # TODO: Resolve Circular Dependency
    from etmfa.db import update_doc_processing_status
    update_doc_processing_status(msg_proc_obj['id'], status)
    request = GenericRequest(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'])
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
    from etmfa.db import received_finalizationcomplete_event
    received_finalizationcomplete_event(msg_proc_obj['id'], msg_proc_obj, message_publisher)


def on_feedback_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_feedbackcomplete_event
    received_feedbackcomplete_event(msg_proc_obj['id'], FeedbackStatus.FEEDBACK_COMPLETED)


def on_documentprocessing_error(error_obj, message_publisher):
    from etmfa.db import received_documentprocessing_error_event
    received_documentprocessing_error_event(error_obj)
