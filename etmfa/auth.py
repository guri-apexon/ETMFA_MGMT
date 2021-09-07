from functools import wraps
from etmfa.server.config import Config
import logging
from etmfa.consts import Consts as consts
from flask import request, abort
from passlib.hash import pbkdf2_sha256

logger = logging.getLogger(consts.LOGGING_NAME)
ERROR_USER_AUTH_MSG = f"Credential validation: Authentication failed for given username and password"

def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pbkdf2_sha256.using(rounds=8000, salt_size=10).hash(password)


def valid_credentials(received_user, received_pwd):
    """
    If userid or password is missing, then authentication fails
    Creates hash based on received userid/password and compares with auth hash
    """
    if not received_user or not received_pwd:
        return False

    auth_hash = Config.AUTH_DETAILS.get(received_user)
    if auth_hash is None:
        logger.debug(f"Received username {received_user} is not valid")
        return False
    else:
        return verify_password(received_pwd, auth_hash)

def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            user_name = None
            password = None
            auth = request.authorization

            if 'X-API-KEY' in request.headers:
                uid_pwd_dict = request.headers['X-API-KEY']
                user_name, _, password = uid_pwd_dict.partition(':')
            elif auth is not None:            
                user_name = auth.username
                password = auth.password
            else:
                return abort(401, ERROR_USER_AUTH_MSG)
            
            if not valid_credentials(user_name, password):
                return abort(401, ERROR_USER_AUTH_MSG)
        except Exception as exc:
            logger.warning(f"User validation exception: {str(exc)}")
            return abort(401, ERROR_USER_AUTH_MSG)

        return f(*args, **kwargs)
    return wrapper
