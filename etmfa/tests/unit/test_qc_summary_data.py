import logging
import ast
import json
import pytest
import datetime
from etmfa.server.config import Config, app_config
from etmfa.consts import Consts as consts
from etmfa.db import pd_fetch_summary_data, received_finalizationcomplete_event
from etmfa.server import create_app
from gevent.pywsgi import WSGIServer
from etmfa.db.db import db_context
from etmfa.db import config as summary_config
from etmfa.db import utils
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

config_name = 'development'
_app_context = create_app(config_name).app_context()


@pytest.mark.parametrize("aidocid, userid",
                         [("66f3aef7-5b75-47bd-acf9-b17bceecd642", "ut_id1"),
                          ("b7fa3376-373c-4d7e-ace7-e882774fcd1a", "ut_id2"),
                          ("3da9c490-1a98-484c-b97b-a2c3ad65462c", "ut_id3"),
                          ("a89de6a0-fc10-4964-9364-fa20962d44ef", "ut_id4")
                          ])
def test_qc_summary_update(aidocid, userid):
    with _app_context:
        current_utctime = datetime.datetime.utcnow()
        _ = pd_fetch_summary_data(aidocid, userid)
        all_summary_records = utils.get_summary_records(aidocid, source=summary_config.SRC_QC)

        assert len(all_summary_records) == 1
        assert all_summary_records[0].timeUpdated > current_utctime


@pytest.mark.parametrize("protocol_num, assign_is_amendment_flg, expected_is_amendment_flg, assign_approval_date, expected_approval_date, comments", 
                        [("SSR_1002-043", "Y", "Y", "20210320", datetime.date(year=2021, month=3, day=20), "Normal"),
                         ("SSR_1002-043", "  larger text than target length", "larger t", "", datetime.date(year=1900, month=1, day=1), "Text truncation and empty date"),
                         ("SSR_1002-043", "larger text than target length", "larger t", "20210606", datetime.date(year=2021, month=6, day=6), "Valid approval date1"),
                         ("SSR_1002-043", "larger text than target length", "larger t", " 20210607  ", datetime.date(year=2021, month=6, day=7), "Valid approval date2"),
                         ("SSR_1002-043", "larger text than target length", "larger t", " A0210608  ", datetime.date(year=1900, month=1, day=1), "Invalid date check")
                        ])
def test_nonqc_summary_insert(finalizer_complete_payload_cached, protocol_num, assign_is_amendment_flg, expected_is_amendment_flg, assign_approval_date, expected_approval_date, comments):
    with _app_context:
        aidoc_id, finalattributes_dict = finalizer_complete_payload_cached[protocol_num]
        
        # Clear old test data
        test_qc_summary = PDProtocolQCSummaryData.query.filter(PDProtocolQCSummaryData.aidocId == aidoc_id, PDProtocolQCSummaryData.source == summary_config.SRC_EXTRACT, PDProtocolQCSummaryData.protocolNumber == protocol_num).delete()
        test_protocol_data = Protocoldata.query.filter(Protocoldata.id == aidoc_id).delete()
        test_protocol_qcdata = Protocolqcdata.query.filter(Protocolqcdata.id == aidoc_id).delete()
        logging.info(f"Unit test {comments}: Cleared # of rows of [qc_summary: {test_qc_summary}]; [protocol_data: {test_protocol_data}]; [protocol_qcdata: {test_protocol_qcdata}]")
        db_context.session.commit()

        # Setup test data
        summary_json_dict = ast.literal_eval(finalattributes_dict['summary'])
        summary_json_dict_data_updated = [[name, assign_is_amendment_flg, alias] if name == "is_amendment" else [name, value, alias] for name, value, alias in summary_json_dict['data']]
        summary_json_dict_data_updated = [[name, assign_approval_date, alias] if name == "approval_date" else [name, value, alias] for name, value, alias in summary_json_dict_data_updated]
        summary_json_dict['data'] = summary_json_dict_data_updated
        finalattributes_dict['summary'] = str(json.dumps(summary_json_dict))
        
        # Run test        
        _ = received_finalizationcomplete_event(id=aidoc_id, finalattributes={'db_data': finalattributes_dict}, message_publisher=None)
        all_summary_records = utils.get_summary_records(aidoc_id, source=summary_config.SRC_EXTRACT)

        # Validate result
        assert len(all_summary_records) == 1
        assert all_summary_records[0].isAmendment == expected_is_amendment_flg
        assert all_summary_records[0].approvalDate == expected_approval_date
