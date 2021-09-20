import datetime
from etmfa.db import db_context


class User(db_context.Model):
    __tablename__ = "user"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    # Alternative: https://docs.microsoft.com/en-us/sql/relational-databases/search/full-text-search?view=sql-server-ver15
    first_name = db_context.Column(db_context.String(200))
    last_name = db_context.Column(db_context.String(100))
    country = db_context.Column(db_context.String(100))
    email = db_context.Column(db_context.String(100))
    username = db_context.Column(db_context.String(100), unique=True)
    date_of_registration = db_context.Column(db_context.DateTime(timezone=True), nullable=False)
    login_id = db_context.Column(db_context.Integer(), db_context.ForeignKey("login.id"))
    user_type = db_context.Column(db_context.String(100))
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    login = db_context.relationship("Login", back_populates="user")

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj