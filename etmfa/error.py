from etmfa.consts import Consts as consts
class ErrorCodes:
    UNKNOWN_ERROR = 600
    ERROR_PROCESSING_STATUS = 601
    ERROR_PROTOCOL_DATA = 602
    ERROR_DOCUMENT_PROCESS_ERROR = 603
    ERROR_DOCUMENT_FEEDBACK = 604
    ERROR_DOCUMENT_DUPLICATE = 605
    ERROR_UPDATING_ATTRIBUTES = 606
    ERROR_DOCUMENT_SAVING = 607
    ERROR_QC_SUMMARY_DATA = 608
    ERROR_ALERT_DATA = 609
    ERROR_EMAIL_GENERATION = 610

ERRORS = {
    ErrorCodes.UNKNOWN_ERROR: "Unknown error",
    ErrorCodes.ERROR_PROCESSING_STATUS: "Error while updating processing status to pd_protocol_metadata file in DB",
    ErrorCodes.ERROR_PROTOCOL_DATA: "Error while writing record to pd_protocol_data file in DB",
    ErrorCodes.ERROR_DOCUMENT_PROCESS_ERROR: "Error while writing record to document_processing_error_event file in DB",
    ErrorCodes.ERROR_UPDATING_ATTRIBUTES: "Error while updating attribute to pd_protocol_data to DB ",
    ErrorCodes.ERROR_DOCUMENT_SAVING: "Error while saving attributes to DB",
    ErrorCodes.ERROR_QC_SUMMARY_DATA: "Error while writing record to pd_protocol_qc_summary_data table",
    ErrorCodes.ERROR_ALERT_DATA: "Error while writing record to pd_protocol_alert file in DB",
    ErrorCodes.ERROR_EMAIL_GENERATION: "Error while generating email alert or updating record in pd_protocol_alert table.",
}


class ManagementException:

    def __init__(self, id, error_code):
        self.service_name = consts.LOGGING_NAME
        self.id = id
        self.error_code = error_code
        self.error_message = ERRORS[error_code]

    def __str__(self):
        return f'({self.service_name}, {self.id}, {self.error_code}, {self.error_message})'
