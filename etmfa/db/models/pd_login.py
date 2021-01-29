from etmfa.db import db_context


class Login(db_context.Model):
    __tablename__ = "login"

    id =db_context.Column(db_context.Integer(), primary_key=True)
    username = db_context.Column(db_context.String(100), unique=True)
    password = db_context.Column(db_context.String(100), nullable=True)
    system_pwd = db_context.Column(db_context.String(100), nullable=False)
    last_password_changed = db_context.Column(db_context.DateTime(timezone=True), nullable=False)
    internal_user = db_context.Column(db_context.Boolean(), nullable=False)
    active_user = db_context.Column(db_context.Boolean(), default=True, nullable=False)
    incorrect_attempts = db_context.Column(db_context.Integer(), default=0)
    user = db_context.relationship("User", back_populates="login")
    pwd_tracker = db_context.relationship("PwdTracker", back_populates="login")

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
