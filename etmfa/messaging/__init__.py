import threading, logging, sys, traceback, json

from kombu import Connection, Exchange, Queue

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
<<<<<<< HEAD
from .models.feedback_complete import feedbackComplete
=======
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
from .models.documentprocessing_error import documentprocessingerror
from ..db import db_context


def msg_listening_worker(app, listener):
    with app.app_context():
        listener.run()

def initialize_msg_listeners(app, connection_str, exchange_name, logger):
    """
    """

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
<<<<<<< HEAD
=======
        print("listening to triage complete queue from listener daemon")
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
    return daemon_handle


def build_queue_callbacks(queue_worker):
    queue_worker.add_listener(TriageComplete.QUEUE_NAME, on_triage_complete)
    queue_worker.add_listener(ocrcomplete.QUEUE_NAME, on_ocr_complete)
    queue_worker.add_listener(classificationComplete.QUEUE_NAME, on_classification_complete)
    queue_worker.add_listener(attributeextractionComplete.QUEUE_NAME, on_attributeextraction_complete)
    queue_worker.add_listener(finalizationComplete.QUEUE_NAME, on_finalization_complete)
<<<<<<< HEAD
    queue_worker.add_listener(feedbackComplete.QUEUE_NAME, on_feedback_complete)
=======
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
    queue_worker.add_listener(documentprocessingerror.QUEUE_NAME, on_documentprocessing_error)

    #queue_worker.add_listener(FormattingError.QUEUE_NAME, on_formatting_error)

    return queue_worker

<<<<<<< HEAD
def on_triage_complete(msg_proc_obj, message_publisher):
=======
def on_triage_complete(format_decon_obj, message_publisher):
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
    from ..db import received_triagecomplete_event
    from ..db import received_ocrcomplete_event
    from ..db import get_doc_resource_by_id
    db_context.session.commit()

<<<<<<< HEAD
    if msg_proc_obj['OCR_Required'] == True:
        print("message received from traiage complete", msg_proc_obj)
        received_triagecomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)
    else:
        print("message received from OCR complete", str(msg_proc_obj))
        received_ocrcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_ocr_complete(msg_proc_obj, message_publisher):
    from ..db import received_ocrcomplete_event

    print("message received from OCR complete", str(msg_proc_obj))
    received_ocrcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_classification_complete(msg_proc_obj, message_publisher):
    from ..db import received_classificationcomplete_event

    print("message received from classification complete",str(msg_proc_obj))
    received_classificationcomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_attributeextraction_complete(msg_proc_obj, message_publisher):
    from ..db import received_attributeextractioncomplete_event

    print("message received from Attribute Extraction complete", str(msg_proc_obj))
    received_attributeextractioncomplete_event(msg_proc_obj['id'], msg_proc_obj['IQVXMLPath'], message_publisher)

def on_finalization_complete(msg_proc_obj, message_publisher):
    from ..db import received_finalizationcomplete_event

    print("message received from Finalization complete", str(msg_proc_obj))
    received_finalizationcomplete_event(msg_proc_obj['id'], msg_proc_obj, message_publisher)

def on_feedback_complete(msg_proc_obj, message_publisher):
    from ..db import received_feedbackcomplete_event

    print("message received from feedback complete", str(msg_proc_obj))
    received_feedbackcomplete_event(msg_proc_obj['id'])
=======
    if format_decon_obj['OCR_Required'] == 'YES':
        received_triagecomplete_event(format_decon_obj['id'], format_decon_obj['IQVXMLPath'], message_publisher)
    else:
        received_ocrcomplete_event(format_decon_obj['id'], format_decon_obj['IQVXMLPath'], message_publisher)
        print(str(format_decon_obj))

def on_ocr_complete(format_decon_obj, message_publisher):
    from ..db import received_ocrcomplete_event
    received_ocrcomplete_event(format_decon_obj['id'], format_decon_obj['IQVXMLPath'], message_publisher)

def on_classification_complete(format_decon_obj, message_publisher):
    from ..db import received_classificationcomplete_event
    print(str(format_decon_obj))
    received_classificationcomplete_event(format_decon_obj['id'], format_decon_obj['IQVXMLPath'], message_publisher)

def on_attributeextraction_complete(format_decon_obj, message_publisher):
    from ..db import received_attributeextractioncomplete_event
    received_attributeextractioncomplete_event(format_decon_obj['id'], format_decon_obj['IQVXMLPath'], message_publisher)

def on_finalization_complete(format_decon_obj, message_publisher):
    from ..db import received_finalizationcomplete_event
    #received_finalizationcomplete_event(format_decon_obj['id'], format_decon_obj['IQVXMLPath'], message_publisher)
    received_finalizationcomplete_event(format_decon_obj['id'], format_decon_obj, message_publisher)
>>>>>>> f358b797bf9629368279861b4828b78985d499f8

def on_documentprocessing_error(error_obj, message_publisher):
    from ..db import received_documentprocessing_error_event
    received_documentprocessing_error_event(error_obj)




<<<<<<< HEAD
=======
# def on_deconstruction_complete(format_decon_obj, message_publisher):
#     from ..db import received_deconstruction_event
#     received_deconstruction_event(format_decon_obj['id'], format_decon_obj['xliffPath'], message_publisher)
#
# def on_translation_complete(translation_complete_obj, message_publisher):
#     from ..db import received_translated_complete_event
#     received_translated_complete_event(translation_complete_obj['id'], translation_complete_obj['xliff_path'], translation_complete_obj['metrics'])
#
# def on_reconstruction_complete(format_recon_obj, message_publisher):
#     from ..db import received_reconstruction_complete_event
#     received_reconstruction_complete_event(format_recon_obj['id'], format_recon_obj['finalDocumentPath'])
#
# def on_formatting_error(error_obj, message_publisher):
#     from ..db import received_formatting_error_event
#     received_formatting_error_event(error_obj)
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
