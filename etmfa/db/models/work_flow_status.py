from etmfa.db.db import db_context
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum
from etmfa.db.db import db_context
from datetime import datetime


class WorkFlowState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSE = "PAUSE"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class WorkFlowStatus(db_context.Model):
    __tablename__ = 'work_flow_status'
    work_flow_id = db_context.Column(db_context.String, primary_key=True)
    doc_id = db_context.Column(db_context.String)
    protocol_name = db_context.Column(db_context.String, nullable=False)
    doc_uid = db_context.Column(db_context.String)
    work_flow_name = db_context.Column(db_context.String)
    documentFilePath = db_context.Column(db_context.String(500))
    status = db_context.Column(
        db_context.String, default=WorkFlowState.PENDING.value)
    all_services = db_context.Column(ARRAY(db_context.String), default=[])
    running_services = db_context.Column(
        ARRAY(db_context.String), default=[])  # name of service
    finished_services = db_context.Column(ARRAY(db_context.String), default=[])
    percent_complete = db_context.Column(db_context.Integer(), default=0)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.utcnow,
                                    onupdate=datetime.utcnow)
    timeCreated = db_context.Column(db_context.DateTime(
        timezone=True), default=datetime.utcnow)
    isProcessing = db_context.Column(db_context.Boolean, default=True)
    errorCode = db_context.Column(db_context.Integer(), default=0)
    errorReason = db_context.Column(db_context.String, default='')
    errorMessageDetails = db_context.Column(db_context.String, default='')
