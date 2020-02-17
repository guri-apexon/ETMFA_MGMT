import threading

from etmfa.db import db_context
from etmfa.messaging.messagelistener import MessageListener
from etmfa.messaging.models.Triage_Request import TriageRequest
from etmfa.messaging.models.Triage_complete import TriageComplete
from etmfa.messaging.models.attributeextraction_complete import attributeextractionComplete
from etmfa.messaging.models.attributeextraction_request import attributeextractionRequest
from etmfa.messaging.models.classification_complete import classificationComplete
from etmfa.messaging.models.classification_request import classificationRequest
from etmfa.messaging.models.documentprocessing_error import documentprocessingerror
from etmfa.messaging.models.feedback_complete import feedbackComplete
from etmfa.messaging.models.finalization_complete import finalizationComplete
from etmfa.messaging.models.finalization_request import finalizationRequest
from etmfa.messaging.models.ocr_complete import ocrcomplete
from etmfa.messaging.models.ocr_request import ocrrequest
from kombu import Connection


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
    queue_worker.add_listener(TriageComplete.QUEUE_NAME, on_triage_complete)
    queue_worker.add_listener(ocrcomplete.QUEUE_NAME, on_ocr_complete)
    queue_worker.add_listener(classificationComplete.QUEUE_NAME, on_classification_complete)
    queue_worker.add_listener(attributeextractionComplete.QUEUE_NAME, on_attributeextraction_complete)
    queue_worker.add_listener(finalizationComplete.QUEUE_NAME, on_finalization_complete)
    queue_worker.add_listener(feedbackComplete.QUEUE_NAME, on_feedback_complete)
    queue_worker.add_listener(documentprocessingerror.QUEUE_NAME, on_documentprocessing_error)

    return queue_worker


def on_triage_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_triagecomplete_event
    from etmfa.db import received_ocrcomplete_event
    db_context.session.commit()

    if msg_proc_obj['OCR_Required'] == True:
        received_triagecomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)
    else:
        received_ocrcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)


def on_ocr_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_ocrcomplete_event

    received_ocrcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)


def on_classification_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_classificationcomplete_event

    received_classificationcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)


def on_attributeextraction_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_attributeextractioncomplete_event

    received_attributeextractioncomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)


def on_finalization_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_finalizationcomplete_event

    received_finalizationcomplete_event(msg_proc_obj['id'], msg_proc_obj, message_publisher)


def on_feedback_complete(msg_proc_obj, message_publisher):
    from etmfa.db import received_feedbackcomplete_event

    received_feedbackcomplete_event(msg_proc_obj['id'])


def on_documentprocessing_error(error_obj, message_publisher):
    from etmfa.db import received_documentprocessing_error_event

    received_documentprocessing_error_event(error_obj)
