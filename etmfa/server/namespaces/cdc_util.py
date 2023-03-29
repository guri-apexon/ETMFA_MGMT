
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

    def run(self):
        from etmfa.server import app
        engine = db_context.get_engine(app)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        try:
            pattern = r'^postgresql\+psycopg2:\/\/(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)\/(?P<database>[^\/]+)$'
            match = re.match(pattern, Config.SQLALCHEMY_DATABASE_URI)
            username = match.group('username')
            password = match.group('password')
            host = match.group('host')
            port = match.group('port')
            database = match.group('database')
            with session_local() as session:
                latest_work = session.query(WorkFlowStatus).filter_by(work_flow_id=self.w_id).first()
                try:
                    run_cdc('audit', username, password, host, port, database)
                    latest_work.status = "COMPLETED"
                    session.commit()
                    session.close()
                except Exception as _:
                    latest_work.status = "ERROR"
                    session.commit()
                    session.close()

        except Exception as exp:
            logger.error(
                "Loading Defaults due to exception when reading yaml from server_config {0}"+str(exp))

