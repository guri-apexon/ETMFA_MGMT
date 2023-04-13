
import threading
import time
import logging
import ctypes
from typing import Dict
from mq_service import MicroServiceWrapper, ExecutionContext, Config
from etmfa.workflow.messaging.models import TriageRequest, GenericRequest
from etmfa.workflow.messaging.models import EtmfaQueues
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_WF)

class FakeTriage(ExecutionContext):
    def __init__(self, config):
        self.config = config
        super().__init__(config.CONTEXT_MAX_ACTIVE_TIME)

    def on_init(self):
        return True

    def on_adapt_msg(self, msg):
        service_msg = {'service_name': 'triage', 'params': msg}
        return {"flow_name": "full_flow", "flow_id": msg['id'], "services_param": [service_msg]}

    def on_callback(self, msg):
        """
        composite Message will be received and ServiceMsg will be sent
        """
        logger.info('got message on triage ')
        curr_msg = list(msg.values())[0]
        triage_msg = TriageRequest(**curr_msg)
        _id = triage_msg.id
        iqv_xml_path = 'local/file.xml'
        feedback_run_id = triage_msg.FeedbackRunId
        output_file_prefix = 'out_prefix'
        out_msg = GenericRequest(
            _id, iqv_xml_path, feedback_run_id, output_file_prefix).__dict__
        out_msg['flow_id'] = _id
        return out_msg

    def on_release(self):
        return True


class FakeDigGeneric(ExecutionContext):
    def __init__(self, config):
        self.config = config
        logger.info("fake dig is running")
        super().__init__(config.CONTEXT_MAX_ACTIVE_TIME)

    def on_init(self):
        return True

    def on_adapt_msg(self, msg):
        service_msg = {'service_name': 'dig1', 'params': msg}
        return {"flow_name": "full_flow", "flow_id": msg['id'], "services_param": [service_msg]}

    def on_callback(self, msg):
        print(f'got message on generic dig - {msg}')
        msg = list(msg.values())[0]
        curr_msg = {'flow_name': 'full_flow', 'flow_id': msg['flow_id'], 'id': msg['id'], 'doc_id': msg['id'],
                    'FeedbackRunId': 0, 'IQVXMLPath': 'tmp.xml', 'OMOPPath': 'tmp_omop.xml',
                    'OutputFilePrefix': '.xml', 'updated_omop_xml_path': 'tmp_update.xml'}
        return curr_msg

    def on_release(self):
        return True


class FakeGeneric(ExecutionContext):
    def __init__(self, config):
        self.config = config
        logger.info("fake generic is running")
        super().__init__(config.CONTEXT_MAX_ACTIVE_TIME)

    def on_adapt_msg(self, msg):
        return msg

    def on_init(self):
        return True

    def on_callback(self, msg):
        return msg

    def on_release(self):
        return True


def wait_threads_to_finish(th_list, min_count=1):
    """
    wait for all threads to finish
    """
    total_execution = 0
    while (total_execution != len(th_list)):
        total_execution = 0
        for th in th_list:
            run_context = th.get_running_context()
            if run_context and run_context.num_executions >= min_count:
                th.stop()
                th.join()
                total_execution += 1
            time.sleep(1)


class ThreadWrapper(threading.Thread):
    def __init__(self, ms, context, config):
        self.config = config
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.ms = ms
        self.ms_instance = None
        self.context = context
        self.start()

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self.get_id()
        resu = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                          ctypes.py_object(SystemExit))
        if resu > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)

    def get_running_context(self):
        if self.ms_instance:
            return self.ms_instance.execution_context
        return None

    def run(self):
        logger.info(f'running service -- {self.config.SERVICE_NAME}')
        self.ms_instance = self.ms(self.config)
        self.ms_instance.run(self.context)
        logger.info('exit from thread wrapper')


DEFAULT_SERVICES_LIST = [{'service_name': 'triage', 'input_queue_name': EtmfaQueues.TRIAGE.request,
                          'output_queue_name': EtmfaQueues.TRIAGE.complete, 'fun': FakeTriage},
                         {'service_name': 'digitizer1', 'input_queue_name': EtmfaQueues.DIGITIZER1.request,
                          'output_queue_name': EtmfaQueues.DIGITIZER1.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'digitizer2', 'input_queue_name': EtmfaQueues.DIGITIZER2.request,
                          'output_queue_name': EtmfaQueues.DIGITIZER2.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'extraction', 'input_queue_name': EtmfaQueues.EXTRACTION.request,
                          'output_queue_name': EtmfaQueues.EXTRACTION.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'digitizer2_omopgenerate', 'input_queue_name': EtmfaQueues.DIGITIZER2_OMOP_GENERATE.request,
                          'output_queue_name': EtmfaQueues.DIGITIZER2_OMOP_GENERATE.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'digitizer2_omopupdate', 'input_queue_name': EtmfaQueues.DIGITIZER2_OMOPUPDATE.request,
                          'output_queue_name': EtmfaQueues.DIGITIZER2_OMOPUPDATE.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'i2e_omop_update', 'input_queue_name': EtmfaQueues.I2E_OMOP_UPDATE.request,
                          'output_queue_name': EtmfaQueues.I2E_OMOP_UPDATE.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'analyzer', 'input_queue_name': EtmfaQueues.PB_ANALYZER.request,
                          'output_queue_name': EtmfaQueues.PB_ANALYZER.complete, 'fun': FakeDigGeneric},
                         {'service_name': 'meta_tagging', 'input_queue_name': EtmfaQueues.META_TAGGING.request,
                          'output_queue_name': EtmfaQueues.META_TAGGING.complete, 'fun': FakeGeneric}
                         ]


class RunMicroservices():
    def __init__(self, services_list):
        self.th_list = []
        self.services_list = services_list if services_list else DEFAULT_SERVICES_LIST

    def run(self):

        for vals in self.services_list:
            cc_config = Config(
                vals['service_name'], input_queue_name=vals['input_queue_name'], output_queue_name=vals['output_queue_name'])
            cc_config.ERROR_QUEUE_NAME = 'documentprocessing_error_dummy'
            th = ThreadWrapper(MicroServiceWrapper, vals['fun'], cc_config)
            while (not (th.ms_instance and th.ms_instance.is_listener_ready)):
                time.sleep(2)
            self.th_list.append(th)

    def wait_for_microservices_to_finish(self):
        wait_threads_to_finish(self.th_list)
