import datetime

from etmfa.db import db_context


class PDUserProtocols(db_context.Model):
    __tablename__ = "pd_user_protocols"

    isActive = db_context.Column(db_context.Boolean(), default=False)
    id = db_context.Column(db_context.String(50), primary_key=True)
    userId = db_context.Column(db_context.String(200), primary_key=True)
    protocol = db_context.Column(db_context.String(200))
    follow = db_context.Column(db_context.Boolean(), default=False)
    userRole = db_context.Column(db_context.String(200), default="primary")
    
    userCreated = db_context.Column(db_context.String(100))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    userUpdated = db_context.Column(db_context.String(100))
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

    def from_post_request(request, _id, doc_path):   
        this = PDUserProtocols()
        this.id = _id

        return this


# post:

# id,
# userid,
# protocol,
# follow=True
# userRole=secondary
#configurable

# Delete:
# id
# userid