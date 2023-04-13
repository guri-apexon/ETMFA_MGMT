
import logging
import re
from threading import Thread
from etmfa.db.models.work_flow_status import WorkFlowStatus
from etmfa.db.db import db_context
from etmfa.db import db_context, WorkFlowStatus
from sqlalchemy.orm import sessionmaker
from etmfa.server.config import Config
from etmfa_core.cdc import run_cdc
from etmfa.consts import Consts
logger = logging.getLogger(Consts.LOGGING_NAME)


class CdcThread(Thread):
    def __init__(self, w_id):
        Thread.__init__(self)
        self.w_id = w_id
        self._is_running = True


    def run(self):
        while (self._is_running):
            from etmfa.server import app
            engine = db_context.get_engine(app)
            session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            try:
                db_url = Config.SQLALCHEMY_DATABASE_URI

                with session_local() as session:
                    latest_work = session.query(WorkFlowStatus).filter_by(work_flow_id=self.w_id).first()
                    try:
                        run_cdc('audit',db_url)
                        latest_work.status = "COMPLETED"
                        session.commit()
                        session.close()
                        logger.info("CDC enabled successfully.")
                    except Exception as err:
                        latest_work.status = "ERROR"
                        session.commit()
                        session.close()
                        logger.error(f"Error in running CDC function - {err}.")

            except Exception as exp:
                logger.error(
                    "Loading Defaults due to exception when reading yaml from server_config {0}"+str(exp))

            self.stop()

    def stop(self):
        self._is_running = False