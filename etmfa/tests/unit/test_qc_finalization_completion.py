import ast
import datetime
import json
import logging

import pytest
from etmfa.consts import Consts as consts
from etmfa.db import config as summary_config
from etmfa.db import received_finalizationcomplete_event
from etmfa.db.db import db_context
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_protocol_summary_entities import ProtocolSummaryEntities
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.messaging.models.processing_status import QcStatus


# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize(
    "run_id, output_file_prefix, payload_path, comment",
    [(0, "", "./etmfa/tests/data/finalization_complete_payload.json",  "Normal Digitization"),
     (1, "R01", "./etmfa/tests/data/finalization_complete_payload.json",  "Feedback run 1"),
     ])
def test_qc_summary_insert(new_app_context, run_id, output_file_prefix, payload_path, comment):
    _, _app_context = new_app_context

    with _app_context:
        current_time = datetime.datetime.utcnow()
        finalizer_payload = json.load(open(payload_path))
        aidoc_id = finalizer_payload['id']
        finalizer_payload['FeedbackRunId'] = run_id
        finalizer_payload["OutputFilePrefix"] = output_file_prefix


        # Clear old test data
        src = summary_config.SRC_FEEDBACK_RUN if run_id > 0 else summary_config.SRC_EXTRACT
        test_qc_summary = PDProtocolQCSummaryData.query.filter(PDProtocolQCSummaryData.aidocId == aidoc_id,
                                                               PDProtocolQCSummaryData.source == src,
                                                               PDProtocolQCSummaryData.runId == run_id).delete()

        test_protocol_summary_entities = ProtocolSummaryEntities.query.filter(ProtocolSummaryEntities.aidocId == aidoc_id,
                                                                  ProtocolSummaryEntities.source == src,
                                                                  ProtocolSummaryEntities.runId == run_id).delete()

        test_protocol_qcdata = 0
        test_protocol_data = 0

        qc_status = QcStatus.COMPLETED.value if run_id > 0 else QcStatus.NOT_STARTED.value

        if run_id == 0:
            test_protocol_qcdata = Protocolqcdata.query.filter(Protocolqcdata.id == aidoc_id).delete()
            test_protocol_data = Protocoldata.query.filter(Protocoldata.id == aidoc_id).delete()

            protocolmetadata = PDProtocolMetadata.query.filter(PDProtocolMetadata.id == aidoc_id).first()
            protocolmetadata.qcStatus = qc_status
            protocolmetadata.runId = run_id
            db_context.session.merge(protocolmetadata)


        logging.info(f"Unit test {comment}: Cleared # of rows of [qc_summary: {test_qc_summary}]; [protocol_data: {test_protocol_data}]; [protocol_summary_entities: {test_protocol_summary_entities}]; [protocol_qcdata: {test_protocol_qcdata}]")
        db_context.session.commit()

        received_finalizationcomplete_event(id=aidoc_id, finalattributes=finalizer_payload,
                                            message_publisher=None)

        test_qc_summary = PDProtocolQCSummaryData.query.filter(PDProtocolQCSummaryData.aidocId == aidoc_id,
                                                               PDProtocolQCSummaryData.source == src,
                                                               PDProtocolQCSummaryData.runId == run_id).first()

        test_protocol_summary_entities = ProtocolSummaryEntities.query.filter(ProtocolSummaryEntities.aidocId == aidoc_id,
                                                                              ProtocolSummaryEntities.source == src,
                                                                              ProtocolSummaryEntities.runId == run_id).first()

        assert test_qc_summary and test_qc_summary.timeUpdated > current_time and test_qc_summary.source == src
        assert test_protocol_summary_entities and test_protocol_summary_entities.timeUpdated > current_time and test_protocol_summary_entities.source == src

        protocolmetadata = PDProtocolMetadata.query.filter(PDProtocolMetadata.id == aidoc_id).first()
        assert protocolmetadata and protocolmetadata.qcStatus == qc_status and protocolmetadata.runId == run_id
        if run_id == 0:
            test_protocol_qcdata = Protocolqcdata.query.filter(Protocolqcdata.id == aidoc_id).first()
            test_protocol_data = Protocoldata.query.filter(Protocoldata.id == aidoc_id).first()
            assert test_protocol_qcdata and test_protocol_qcdata.timeUpdated > current_time
            assert test_protocol_data and test_protocol_data.timeUpdated > current_time


