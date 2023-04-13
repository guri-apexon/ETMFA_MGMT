
from etmfa.workflow.wf_manager import WorkFlowManager,WorkFlowClient,WorkFlowThreadRunner
from etmfa.workflow.db.db_utils import create_doc_processing_status
from etmfa.server.config import Config
from etmfa.consts import Consts as consts
from .pseudo_ms_utils import RunMicroservices
from etmfa.workflow.db.db_utils import DbMixin
from etmfa.workflow.db.schemas import WorkFlowStatus
from etmfa.workflow.messaging import MsqType
from etmfa.workflow.messaging.models import EtmfaQueues
from .pseudo_ms_utils import FakeGeneric
import time


def test_wf_manager_run():
    import logging
    from etmfa.workflow.messaging.models import TriageRequest
    from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test")

    work_flow_id='12490569623511'
    work_flow_name='full_flow'
    protocol_name=''
    msg = TriageRequest(work_flow_id, 'tmp.pdf', 'tmp.pdf', '1', 'xyz', '', '', '',\
                        '', '', '', '', '', '', '123', 0).__dict__
    mixin=DbMixin()
    meta_data=PDProtocolMetadata(id=work_flow_id,userId='12345')
    mixin.write_unique(meta_data)
    create_doc_processing_status(work_flow_id,None,None,work_flow_name,'',protocol_name)
    ms_runner=RunMicroservices()
    ms_runner.run()
    wf_manager=WorkFlowManager(Config.MESSAGE_BROKER_EXCHANGE,Config.MESSAGE_BROKER_ADDR,
                    Config.DFS_UPLOAD_FOLDER,logger)
    wf_manager.wait_until_listener_ready()
    wf_manager.delete_channel_ids([(work_flow_name,work_flow_id)])
    wf_manager.run_work_flow(work_flow_name,work_flow_id,msg)
    ms_runner.wait_for_microservices_to_finish()
    mixin.delete_by_key(PDProtocolMetadata,PDProtocolMetadata.id,work_flow_id)
    mixin.delete_by_key(WorkFlowStatus,WorkFlowStatus.work_flow_id,work_flow_id)


def test_client_and_controller():
    conf = {"ZMQ_PORT": Config.ZMQ_PORT,
            "MESSAGE_BROKER_EXCHANGE": Config.MESSAGE_BROKER_EXCHANGE,
            "LOGSTASH_HOST": Config.LOGSTASH_HOST,
            "LOGSTASH_PORT": Config.LOGSTASH_PORT,
            "MESSAGE_BROKER_ADDR": Config.MESSAGE_BROKER_ADDR,
            "DFS_UPLOAD_FOLDER": Config.DFS_UPLOAD_FOLDER,
            "DEBUG": False
            }
    runner = WorkFlowThreadRunner(conf)
    runner.start_process()
    while(not runner.wfc):
        time.sleep(3)
    runner.wfc.wfm.wait_until_listener_ready()
    cid='12x8976'
    work_flow_name='custom_test_eg'
    wf_client = WorkFlowClient(Config.ZMQ_PORT)
    work_flow_list = [
        {
            "work_flow_name": "meta_extraction",
            "dependency_graph": [
                {"service_name": "meta_tagging", "depends": []}
            ]
        }]
    wf_client.send_msg(work_flow_name, cid, "", {"work_flow_list": work_flow_list,
                                                                            "doc_id": cid},
                                                    MsqType.ADD_CUSTOM_WORKFLOW.value)
    wf_client.send_msg(work_flow_name,cid,"",{"work_flow_id":cid,"doc_id":cid})
    time.sleep(10)
    

    