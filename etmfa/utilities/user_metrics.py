from datetime import datetime
from etmfa.db import PDUserProtocols
from etmfa.db.models.pd_users import User
from etmfa.db.models.pd_user_metrics import UserMetrics
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.consts.constants import LAST_PROTOCOL_ACCESS
from sqlalchemy import desc
from etmfa.db.db import db_context


def create_or_update_user_metrics(user_id: str, aidoc_id: str):
    if user_id:
        user_filter = (user_id, 'u' + user_id, 'q' + user_id)
        user = db_context.session.query(User).filter(
            User.username.in_(user_filter)).first()
        protocol_obj = db_context.session.query(PDProtocolMetadata).filter(
            PDProtocolMetadata.id == aidoc_id).first()
        user_protocol = db_context.session.query(PDUserProtocols).filter(
            PDUserProtocols.userId.in_(user_filter),
            PDUserProtocols.protocol == protocol_obj.protocol).first()
        user_role = user_protocol.userRole if user_protocol else ''
        if user and protocol_obj:
            user_metrics = db_context.session.query(UserMetrics).filter(
                UserMetrics.userid.in_(user_filter),
                UserMetrics.aidoc_id == aidoc_id,
                UserMetrics.user_type == user.user_type,
                UserMetrics.document_version == protocol_obj.versionNumber).first()
            if user_metrics:
                viewed_count = int(user_metrics.viewed_count)
                # If obj of user metrics already exists update viewed count
                try:
                    user_metrics.viewed_count = str(viewed_count+1)
                    user_metrics.accesstime = datetime.utcnow()
                    db_context.session.add(user_metrics)
                    db_context.session.commit()
                except Exception as ex:
                    db_context.session.rollback()
                    return ex
            else:
                # create new record with view count one
                try:
                    db_obj = UserMetrics(userid=user_id,
                                         protocol=protocol_obj.protocol,
                                         user_type=user.user_type,
                                         userrole=user_role,
                                         viewed_count=1,
                                         timecreated=datetime.utcnow(),
                                         accesstime=datetime.utcnow(),
                                         isactive=True,
                                         aidoc_id=aidoc_id,
                                         document_version=protocol_obj.versionNumber)
                    db_context.session.add(db_obj)
                    db_context.session.commit()
                    db_context.session.refresh(db_obj)
                except Exception as ex:
                    db_context.session.rollback()
                    return ex

        # To maintain only last N protocol access by user into database
        user_metrics = db_context.session.query(UserMetrics).filter(
            UserMetrics.userid.in_(user_filter),
            UserMetrics.aidoc_id == aidoc_id,
            UserMetrics.isactive == True).order_by(
            desc(UserMetrics.accesstime)).all()
        if user_metrics and len(user_metrics) > LAST_PROTOCOL_ACCESS:
            del user_metrics[:LAST_PROTOCOL_ACCESS]
            try:
                for obj in user_metrics:
                    obj.isactive = False
                    db_context.session.add(obj)
                db_context.session.commit()
            except Exception as ex:
                db_context.session.rollback()
                return ex
