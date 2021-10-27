import datetime

from etmfa.db import db_context


class PDProtocolQCSummaryData(db_context.Model):
    __tablename__ = "pd_protocol_qc_summary_data"

    aidocId = db_context.Column(db_context.String(128), primary_key=True)
    source = db_context.Column(db_context.String(32), primary_key=True)
    runId = db_context.Column(db_context.String(50), primary_key=True)
    sponsor = db_context.Column(db_context.String(256))
    protocolName = db_context.Column(db_context.String(256))
    protocolNumber = db_context.Column(db_context.String(64))
    trialPhase = db_context.Column(db_context.String(16))
    versionNumber = db_context.Column(db_context.String(64))
    isAmendment = db_context.Column(db_context.String(8))
    amendmentNumber = db_context.Column(db_context.String(64))
    approvalDate = db_context.Column(db_context.Date)
    versionDate = db_context.Column(db_context.Date)
    protocolTitle = db_context.Column(db_context.String(1024))
    protocolShortTitle = db_context.Column(db_context.String(512))
    indications = db_context.Column(db_context.String(1024))
    moleculeDevice = db_context.Column(db_context.String(128))
    investigator = db_context.Column(db_context.String(128))
    blinded = db_context.Column(db_context.String(64))
    drug = db_context.Column(db_context.String(256))
    compoundNumber = db_context.Column(db_context.String(256))
    control = db_context.Column(db_context.String(512))
    endPoints = db_context.Column(db_context.String(None))
    trialTypeRandomized = db_context.Column(db_context.String(2048))
    regulatoryIdNctId = db_context.Column(db_context.String(256))
    sponsorAddress = db_context.Column(db_context.String(512))
    numberOfSubjects = db_context.Column(db_context.String(32))
    participantAge = db_context.Column(db_context.String(64))
    participantSex = db_context.Column(db_context.String(16))
    studyPopulation = db_context.Column(db_context.String(1024))
    inclusionCriteria = db_context.Column(db_context.String(None))
    exclusionCriteria = db_context.Column(db_context.String(None))
    primaryObjectives = db_context.Column(db_context.String(None))
    secondaryObjectives = db_context.Column(db_context.String(None))

    isActive = db_context.Column(db_context.Boolean(), default=True)
    qcApprovedBy = db_context.Column(db_context.String(16))
    userCreated = db_context.Column(db_context.String(64))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    userUpdated = db_context.Column(db_context.String(64))
    timeUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

