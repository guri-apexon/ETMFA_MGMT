from etmfa.consts import Consts as consts
class ErrorCodes:
    UNKNOWN_ERROR = 600
    ERROR_PROCESSING_STATUS = 601
    ERROR_DOCUMENT_ATTRIBUTES = 602
    ERROR_DOCUMENT_PROCESS_ERROR = 603
    ERROR_DOCUMENT_FEEDBACK = 604
    ERROR_DOCUMENT_DUPLICATE = 605
    ERROR_UPDATING_ATTRIBUTES = 606
    ERROR_DOCUMENT_SAVING = 607


ERRORS = {
    ErrorCodes.UNKNOWN_ERROR: "Unknown error",
    ErrorCodes.ERROR_PROCESSING_STATUS: "Error while updating processing status to etmfa_document_process file in DB",
    ErrorCodes.ERROR_DOCUMENT_ATTRIBUTES: "Error while writing record to etmfa_document_attributes file in DB",
    ErrorCodes.ERROR_DOCUMENT_PROCESS_ERROR: "Error while writing record to document_processing_error_event file in DB",
    ErrorCodes.ERROR_DOCUMENT_FEEDBACK: "Error while writing record to etmfa_document_feedback file in DB",
    ErrorCodes.ERROR_DOCUMENT_DUPLICATE: "Error while writing record to etmfa_document_duplicate file in DB",

    ErrorCodes.ERROR_UPDATING_ATTRIBUTES: "Error while updating attribute to etmfa_document_attributes to DB ",
    ErrorCodes.ERROR_DOCUMENT_SAVING: "Error while saving attributes to DB"
}


class ManagementException:

    def __init__(self, id, error_code):
        self.service_name = consts.LOGGING_NAME
        self.id = id
        self.error_code = error_code
        self.error_message = ERRORS[error_code]

    def __str__(self):
        return f'({self.service_name}, {self.id}, {self.error_code}, {self.error_message})'
