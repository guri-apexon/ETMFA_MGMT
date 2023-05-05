import glob
import logging
import os
from dataclasses import asdict

from etmfa.consts import Consts as consts
from etmfa.workflow.messaging.messagepublisher import MessagePublisher
from etmfa.workflow.messaging.models.generic_request import FeedbackRun
from etmfa.workflow.messaging.models.queue_names import EtmfaQueues
from flask import current_app

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"

def get_latest_file_path(dfs_folder_path, prefix, suffix="*.xml*"):
    """
    Get latest file amound digitized and feedback run
    """
    feedback_pattern = "R??"+prefix+suffix
    digitization_pattern = prefix+suffix

    full_feedback_pattern = os.path.join(dfs_folder_path, feedback_pattern)
    feedback_files = glob.glob(full_feedback_pattern)

    if feedback_files:
        sorted_feedback_files = sorted(feedback_files, reverse=True)
        return sorted_feedback_files[0]

    full_digitization_pattern = os.path.join(dfs_folder_path, digitization_pattern)
    digitization_files = glob.glob(full_digitization_pattern)
    if digitization_files:
        return sorted(digitization_files)[0]

