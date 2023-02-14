from etmfa.db.db import db_context

class PwdTracker(db_context.Model):
    __tablename__ = "pwdtracker"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    email = db_context.Column(db_context.String(100), unique=True)
    password1 = db_context.Column(db_context.String(100))
    password2 = db_context.Column(db_context.String(100))
    password3 = db_context.Column(db_context.String(100))
    login_id = db_context.Column(db_context.Integer(), db_context.ForeignKey("login.id"))
    login = db_context.relationship("Login", back_populates="pwd_tracker")