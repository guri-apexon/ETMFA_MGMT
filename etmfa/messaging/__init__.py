import threading
from dataclasses import asdict
from functools import partial

from kombu import Connection

from etmfa.messaging.messagelistener import MessageListener
from etmfa.messaging.models.generic_request import GenericRequest
from etmfa.messaging.models.processing_status import ProcessingStatus
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
    # TODO : Triage_Complete will be replaced with EtmfaQueues queue names
    queue_worker.add_listener("Triage_Complete", on_triage_complete)
    queue_worker.add_listener(EtmfaQueues.OCR.complete,
                              partial(on_generic_complete_event, status=ProcessingStatus.CLASSIFICATION_STARTED,
                                      dest_queue_name=EtmfaQueues.CLASSIFICATION.request))
    queue_worker.add_listener(EtmfaQueues.CLASSIFICATION.complete,
                              partial(on_generic_complete_event,
                                      status=ProcessingStatus.ATTRIBUTEEXTRACTION_STARTED,
                                      dest_queue_name=EtmfaQueues.ATTRIBUTEEXTRACTION.request))
    queue_worker.add_listener(EtmfaQueues.ATTRIBUTEEXTRACTION.complete,
                              partial(on_generic_complete_event, status=ProcessingStatus.FINALIZATION_STARTED,
                                      dest_queue_name=EtmfaQueues.FINALIZATION.request))
    queue_worker.add_listener(EtmfaQueues.FINALIZATION.complete, on_finalization_complete)
    queue_worker.add_listener(EtmfaQueues.FEEDBACK.complete, on_feedback_complete)
    queue_worker.add_listener(EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value, on_documentprocessing_error)

    return queue_worker


def on_generic_complete_event(msg_proc_obj, message_publisher, status, dest_queue_name):
    # TODO: Resolve Circular Dependency
    from etmfa.db import update_doc_processing_status
    update_doc_processing_status(msg_proc_obj['id'], status)
    request = GenericRequest(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'])
    message_publisher.send_dict(asdict(request), dest_queue_name)


def on_triage_complete(msg_proc_obj, message_publisher):
    if msg_proc_obj['OCR_Required']:
        dest_queue = EtmfaQueues.OCR.request
        status = ProcessingStatus.OCR_STARTED
    else:
        dest_queue = EtmfaQueues.CLASSIFICATION.request
        status = ProcessingStatus.CLASSIFICATION_STARTED

    return on_generic_complete_event(msg_proc_obj, message_publisher, status, dest_queue)


def on_finalization_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_finalizationcomplete_event
    received_finalizationcomplete_event(msg_proc_obj['id'], msg_proc_obj, message_publisher)


def on_feedback_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_feedbackcomplete_event
    received_feedbackcomplete_event(msg_proc_obj['id'])


def on_documentprocessing_error(error_obj, message_publisher):
    from etmfa.db import received_documentprocessing_error_event
    received_documentprocessing_error_event(error_obj)
