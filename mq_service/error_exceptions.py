
from enum import Enum


class ErrorCodes(Enum):
    UNKNOWN_ERROR = 500


ERRORS = {
    ErrorCodes.UNKNOWN_ERROR: "Unknown error"

}


class GenericError(Exception):

    def __init__(self, error_code, error_message_details):
        self.error_code = error_code if error_code in ErrorCodes else ErrorCodes.UNKNOWN_ERROR
        self.error_message = ERRORS[error_code]
        self.error_message_details = error_message_details

    def __str__(self):
        return f'({self.error_code}, {self.error_message}, {self.error_message_details})'
