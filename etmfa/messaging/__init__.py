import threading, logging, sys, traceback, json

from kombu import Connection, Exchange, Queue

from .messagelistener import MessageListener

from .models.formatting_deconstruction_complete import FormattingDeconstructionComplete
from .models.formatting_deconstruction_request import FormattingDeconstructionRequest
from .models.translation_complete import TranslationComplete
from .models.formatting_reconstruction_complete import FormattingReconstructionComplete
from .models.formatting_error import FormattingError

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
        
    return daemon_handle


def build_queue_callbacks(queue_worker):
    queue_worker.add_listener(FormattingDeconstructionComplete.QUEUE_NAME, on_deconstruction_complete)
    queue_worker.add_listener(TranslationComplete.QUEUE_NAME, on_translation_complete)
    queue_worker.add_listener(FormattingReconstructionComplete.QUEUE_NAME, on_reconstruction_complete)
    queue_worker.add_listener(FormattingError.QUEUE_NAME, on_formatting_error)

    return queue_worker


def on_deconstruction_complete(format_decon_obj, message_publisher):
    from ..db import received_deconstruction_event
    received_deconstruction_event(format_decon_obj['id'], format_decon_obj['xliffPath'], message_publisher)

def on_translation_complete(translation_complete_obj, message_publisher):
    from ..db import received_translated_complete_event
    received_translated_complete_event(translation_complete_obj['id'], translation_complete_obj['xliff_path'], translation_complete_obj['metrics'])

def on_reconstruction_complete(format_recon_obj, message_publisher):
    from ..db import received_reconstruction_complete_event
    received_reconstruction_complete_event(format_recon_obj['id'], format_recon_obj['finalDocumentPath'])

def on_formatting_error(error_obj, message_publisher):
    from ..db import received_formatting_error_event
    received_formatting_error_event(error_obj)