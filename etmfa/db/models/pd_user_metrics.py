from datetime import datetime
from etmfa.db.db import db_context


class UserMetrics(db_context.Model):
    __tablename__ = "pd_user_metrics"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    userid = db_context.Column(db_context.String(100), nullable=False)
    protocol = db_context.Column(db_context.String(100), nullable=False)
    userrole = db_context.Column(db_context.String(100), nullable=True)
    viewed_count = db_context.Column(db_context.String(100), nullable=True)
    timecreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.utcnow)
    accesstime = db_context.Column(db_context.DateTime(timezone=True), default=datetime.utcnow)
    isactive = db_context.Column(db_context.Boolean(), default=True, nullable=False)
    aidoc_id = db_context.Column(db_context.String(100), nullable=False)
    document_version = db_context.Column(db_context.String(100), nullable=False)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
