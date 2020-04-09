from etmfa.db import db_context


class Processing(db_context.Model):
    __tablename__ = "etmfa_document_processing"

    id = db_context.Column(db_context.Integer, primary_key=True)
    processing_dir = db_context.Column(db_context.String(1000))

    def __init__(self, id, processing_dir):
        self.id = id
        self.processing_dir = processing_dir

    def __repr__(self):
        return '<Processing dto. Processing Directory: {}.>'.format(self.processing_dir)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
