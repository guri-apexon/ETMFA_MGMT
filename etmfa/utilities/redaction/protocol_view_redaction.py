import logging
from etmfa.utilities.redact import Redactor
from etmfa.utilities.pd_table_redaction import TableRedaction
from etmfa.consts import Consts as consts, constants

logger = logging.getLogger(consts.LOGGING_NAME)


class ProtocolViewRedaction:
    def __init__(self, db, user_id: str, protocol: str):
        """
        Protocol view redaction with user id and protocal

        **Parameters**

        * user_id: user id requested for document to get reduct profile
        * `protocol`: document protocol
        """
        self.user_id = user_id
        self.protocol = protocol

        redactor = Redactor(db)
        profile_name, profile_details, profile_genre = redactor.get_current_redact_profile(
            current_db=db, user_id=self.user_id, protocol=self.protocol)
        self.profile_name = profile_name
        self.profile_details = profile_details
        self.entity_profile_genre = profile_genre

        self.table_redaction = TableRedaction(
            redact_flag=constants.REDACTION_FLAG[self.profile_name],
            hide_table_json_flag=
            constants.HIDE_TABLE_JSON_FLAG[self.profile_name],
            return_refreshed_table_html=constants.RETURN_REFRESHED_TABLE_HTML_FLAG[
                self.profile_name], redact_text=constants.REDACT_PARAGRAPH_STR,
            redact_profile_entities=self.entity_profile_genre)