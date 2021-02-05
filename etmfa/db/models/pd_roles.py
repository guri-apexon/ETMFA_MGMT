import datetime

from etmfa.db import db_context


class PDRoles(db_context.Model):
    __tablename__ = "pd_roles"

    id = db_context.Column(db_context.String(50), primary_key=True)
    roleName = db_context.Column(db_context.String(100))
    roleDescription = db_context.Column(db_context.String(1000))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
