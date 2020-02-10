import threading, logging, sys, traceback, json

from kombu import Connection, Exchange, Queue

from etmfa.messaging.models.processing_status import ProcessingStatus
from .messagelistener import MessageListener

from .models.Triage_complete import TriageComplete
from .models.Triage_Request import TriageRequest
from .models.ocr_complete import ocrcomplete
from .models.ocr_request import ocrrequest
from .models.classification_complete import classificationComplete
from .models.classification_request import classificationRequest
from .models.attributeextraction_complete import attributeextractionComplete
from .models.attributeextraction_request import attributeextractionRequest
from .models.finalization_complete import finalizationComplete
from .models.finalization_request import finalizationRequest
from .models.feedback_complete import feedbackComplete
from .models.documentprocessing_error import documentprocessingerror
from ..db import db_context


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
    # Refactor here:
    # Possible simplification could be:
    
    from functools import partial
    # This is just a helper - should be stored in a proper config enum/obj similar as was defined in
    # https://gitlabrnds.quintiles.com/etmf-group/etmfa-management-service/blob/933d7a4f2eaee30804d0455c5f8ad8038eef0bb5/etmfa/messaging/models/queue_names.py
    destionation_queue_name = 'attributeextraction_request'

    queue_worker.add_listener(TriageComplete.QUEUE_NAME, on_triage_complete)
    queue_worker.add_listener(ocrcomplete.QUEUE_NAME, on_ocr_complete)
    queue_worker.add_listener(classificationComplete.QUEUE_NAME, partial(on_generic_complete_event, status=ProcessingStatus.ATTRIBUTEEXTRACTION_STARTED, dest_queue_name=destionation_queue_name))
    queue_worker.add_listener(attributeextractionComplete.QUEUE_NAME, on_attributeextraction_complete)
    queue_worker.add_listener(finalizationComplete.QUEUE_NAME, on_finalization_complete)
    queue_worker.add_listener(feedbackComplete.QUEUE_NAME, on_feedback_complete)
    queue_worker.add_listener(documentprocessingerror.QUEUE_NAME, on_documentprocessing_error)
    return queue_worker

def on_generic_complete_event(msg_proc_obj, message_publisher, status, dest_queue_name):
    from ..db import update_processing_status

    # update db status
    update_processing_status(msg_proc_obj['id'], status['perentual_status'], status['status'])            
    required_fields = ['id', 'IQVXMLPath']
    msg_proc_filtered = {key:value for key, value in msg_proc_obj.items() if key in required_fields}
    message_publisher.send_dict(msg_proc_filtered, dest_queue_name)



def on_triage_complete(msg_proc_obj, message_publisher):
    # Possible refactor could be:
    from functools import partial
    if msg_proc_obj['OCR_Required'] == True:
        dest_queue = 'ocr_request'
        status = ProcessingStatus.OCR_STARTED
    else:
        dest_queue = 'classification_request'
        status = ProcessingStatus.CLASSIFICATION_STARTED
    return partial(on_generic_complete_event, status=status, dest_queue_name=dest_queue)

def on_ocr_complete(msg_proc_obj, message_publisher):
    from ..db import received_ocrcomplete_event

    received_ocrcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_classification_complete(msg_proc_obj, message_publisher):
    from ..db import received_classificationcomplete_event

    received_classificationcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_attributeextraction_complete(msg_proc_obj, message_publisher):
    from ..db import received_attributeextractioncomplete_event

    received_attributeextractioncomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_finalization_complete(msg_proc_obj, message_publisher):
    from ..db import received_finalizationcomplete_event

    received_finalizationcomplete_event(msg_proc_obj['id'], msg_proc_obj, message_publisher)

def on_feedback_complete(msg_proc_obj, message_publisher):
    from ..db import received_feedbackcomplete_event

    received_feedbackcomplete_event(msg_proc_obj['id'])

def on_documentprocessing_error(error_obj, message_publisher):
    from ..db import received_documentprocessing_error_event
    received_documentprocessing_error_event(error_obj)




