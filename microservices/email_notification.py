
from mq_service import MicroServiceWrapper, ExecutionContext, Config
from multiprocessing import Process
from .common import GenericException

class EmailNotification(ExecutionContext):
    def __init__(self, config):
        self.config = config
        ExecutionContext.__init__(self, config.CONTEXT_MAX_ACTIVE_TIME)

    def on_init(self):
        """
        intialization if any needed
        """
        return True

    def on_callback(self, msg_data):
        """
        return: original response or what should be sent next.
        """
        msg = list(msg_data.values())[0]
        key = 'docId' if 'docId' in msg else 'doc_id'
        aidoc_id = msg[key]

        #dont change return value
        return msg_data

    def on_release(self):
        """
        resource if any needs to be released
        """
        return True


class EmailNotificationRunner(Process):
    def __init__(self, service_name="email_notification"):
        self.service_name = service_name
        Process.__init__(self)

    def run(self):
        config = Config(self.service_name)
        mw = MicroServiceWrapper(config)
        mw.run(EmailNotification)
