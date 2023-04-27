from etmfa.db.generate_email import send_event_based_mail
from mq_service import MicroServiceWrapper, ExecutionContext, Config
from multiprocessing import Process
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



from etmfa.consts import Consts as consts
import logging

logger = logging.getLogger(consts.LOGGING_NAME)


class EmailNotification(ExecutionContext):
    def __init__(self, config):
        self.config = config
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True,
                                    pool_size=1, max_overflow=-1, echo=False,
                                    pool_use_lifo=True, pool_recycle=1800)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)
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

        try:
            with self.SessionLocal() as session:
                _ = send_event_based_mail(doc_id=aidoc_id,
                                        event="NEW_DOCUMENT_VERSION",
                                        send_mail_flag=True, db=session, test_case=msg.get('test_case'))
                logger.info(f"for doc id {aidoc_id} event NEW_DOCUMENT_VERSION records create and mail send success")
        except Exception as ex:
            logger.exception(f"exception occured at NEW_DOCUMENT_VERSION event for doc_id {aidoc_id} as {str(ex)}")

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
