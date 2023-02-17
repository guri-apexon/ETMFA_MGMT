from typing import Dict
import os
import os
from enum import Enum
from .message_handler_interface import MessageHandler
from ..models import ServiceMessage, CompositeServiceMessage, TriageRequest, GenericRequest, Dig2XMLPathRequest
from ..models.generic_request import I2eOmapRequest, DIG2OMAPRequest
from ...default_workflows import DEFAULT_SERVICE_FLOW_MAP
from ..models.queue_names import EtmfaQueues
from ..models.processing_status import ProcessingStatus
from ...db.db_utils import update_doc_processing_status, get_work_flow_name_by_id, get_work_flow_info_by_id, get_session_obj
from etmfa.db.feedback_utils import get_latest_file_path


class DigitizationGenericMessageHandler(MessageHandler):
    def __init__(self, dfs_path=None):
        self.dfs_path = dfs_path

    def update_dfs_path(self, dfs_path):
        self.dfs_path = dfs_path

    def on_msg(self, service_name: str, message: ServiceMessage, meta_info: Dict) -> ServiceMessage:
        """
        Status update and db handling to be done here,on end of service
        """
        msg_proc_obj = message.params
        work_flow_name = message.flow_name
        update_doc_processing_status(
            msg_proc_obj['flow_id'], service_name,False,work_flow_name)

        return message

    def _get_msg_obj(self, msg):
        flow_name = msg.flow_name  # not used by triage now
        _id = msg.flow_id
        service_info = msg.services_param[0]
        msg_proc_obj = service_info.params
        return msg_proc_obj

    def on_input_message_adapter(self, service_name, msg_proc_obj) -> ServiceMessage:
        """
        incoming message after generic digitization step complete.This wont be of serviceMessage type
        triage uses older format,there wont be flow_id etc,add compatiblity here..
        """
        _id = msg_proc_obj.get('flow_id', None)
        request_params={}
        if msg_proc_obj.get('params',None):
            request_params=msg_proc_obj['params']
        else:
            request_params = msg_proc_obj
        # only full pipeline will run if flow_id missing,for now its for compatibility
        if not _id:
            _id = msg_proc_obj['id']
            request_params['flow_id'] = _id

        flow_name = msg_proc_obj.get('flow_name', None)
        if not flow_name:
            flow_name = get_work_flow_name_by_id(_id)
            request_params['flow_name'] = flow_name
        if not flow_name:
            raise Exception("Unknown workflow cant process further ")
        in_service_message = ServiceMessage(
            flow_name=flow_name, flow_id=_id, params=request_params)

        return in_service_message

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to generic digitization service
        """
        work_flow_name = msg.flow_name
        msg_proc_obj = self._get_msg_obj(msg)
        update_doc_processing_status(
            msg_proc_obj['id'], service_name,True,work_flow_name)
        return msg_proc_obj


class TriageMessageHandler(DigitizationGenericMessageHandler):

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to Triage Service
        """
        # from etmfa.db import update_doc_processing_status

        service_param = self._get_msg_obj(msg)
        _id = service_param['id']
        filepath, source_filename, version_number = service_param[
            'filepath'], service_param['sourceFileName'], service_param['version_number']
        protocol, document_status, environment = service_param[
            'protocol'], service_param['document_status'], service_param['environment']
        source_system, study_status, amendment_number = service_param[
            'source_system'], service_param['study_status'], service_param['amendment_number']
        project_id, indication, molecule_device = service_param[
            'project_id'], service_param['indication'], service_param['molecule_device']
        sponsor, user_id, feedback_run_id = service_param[
            'sponsor'], service_param['user_id'], service_param['FeedbackRunId']

        triage_request = TriageRequest(_id, str(filepath), source_filename, version_number, protocol, document_status,
                                       environment, source_system, sponsor, study_status, amendment_number, project_id,
                                       indication, molecule_device, user_id, feedback_run_id)

        work_flow_name = msg.flow_name
        update_doc_processing_status(_id, service_name,True,work_flow_name)
        return triage_request.__dict__


class Digitizer1MessageHandler(DigitizationGenericMessageHandler):

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        check if we can skip digitization
        """
        msg_obj = self._get_msg_obj(msg)
        if not msg_obj.get('ocr_required', True):
            return None

        return super().on_output_message_adapter(service_name, msg)


class I2eOmopMessageHandler(DigitizationGenericMessageHandler):

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to I2eOmopService
        """
        service_param = self._get_msg_obj(msg)
        _id, xml_path = service_param['id'], service_param['IQVXMLPath']
        flow_name, flow_id = msg.flow_name, msg.flow_id
        omop_xml_path = None
        if not service_param.get('OMOPPath', None):
            xml_path = xml_path[:xml_path.rfind('\\')]
            omop_xml_path = get_latest_file_path(
                xml_path, prefix="", suffix="*omop.xml")
        else:
            omop_xml_path = service_param['OMOPPath']
        feedback_run_id, output_file_prefix = service_param[
            'FeedbackRunId'], service_param['OutputFilePrefix']
        file = None
        try:
            IQVXMLPath = os.path.join(self.dfs_path, _id)
            file = get_latest_file_path(
                IQVXMLPath, prefix="*.omop", suffix="*.xml*")
        except Exception as e:
            file = None

        request = DIG2OMAPRequest(
            _id, flow_id, flow_name, omop_xml_path, feedback_run_id, output_file_prefix)
        update_doc_processing_status(_id, service_name,True,flow_name)
        return request.__dict__


class Digitizer2OmopGenerateHandler(DigitizationGenericMessageHandler):
    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to document compare
        """
        service_param = self._get_msg_obj(msg)
        _id = service_param['id']
        doc_id = service_param.get('doc_id', None)
        if not doc_id:
            doc_id = _id
        FeedbackRunId = service_param.get('FeedbackRunId', 0)
        flow_name = msg.flow_name
        flow_id = msg.flow_id
        IQVXMLPath = os.path.join(self.dfs_path, doc_id)
        dig_file_path = get_latest_file_path(
            IQVXMLPath, prefix="D2_", suffix="*.xml*")
        return Dig2XMLPathRequest(_id, doc_id, FeedbackRunId, flow_name, flow_id, dig_file_path, '').__dict__


class Digitizer2OmopUpdateHandler(DigitizationGenericMessageHandler):

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to I2eOmopService
        """
        service_param = self._get_msg_obj(msg)
        flow_id=service_param['flow_id']
        flow_name=service_param['flow_name']
        _id, updated_omop_xml_path = service_param['id'], service_param['updated_omop_xml_path']
        feedback_run_id = service_param['FeedbackRunId']
        file = None
        try:
            IQVXMLPath = os.path.join(self.dfs_path, _id)
            dig_file_path = get_latest_file_path(
                IQVXMLPath, prefix="D2_", suffix="*.xml*")
            if dig_file_path:
                file = dig_file_path
        except Exception as e:
            file = None

        if feedback_run_id == 0:
            output_file_prefix = ""
        else:
            output_file_prefix = "R" + str(feedback_run_id).zfill(2)
        out_queue_name = EtmfaQueues.DIGITIZER2_OMOPUPDATE.request
        request = I2eOmapRequest(_id,flow_id,flow_name, updated_omop_xml_path, file,
                                 feedback_run_id, output_file_prefix, out_queue_name)
        update_doc_processing_status(_id, service_name,True,msg.flow_name)
        return request.__dict__


class Digitizer2CompareHandler(DigitizationGenericMessageHandler):

    def on_msg(self, service_name: str, message: ServiceMessage, meta_info: Dict) -> ServiceMessage:
        """
        Status update and db handling to be done here,on end of service
        """
        from etmfa.db import received_comparecomplete_event
        msg_proc_obj = message.params
        work_flow_name = message.flow_name
        session = get_session_obj()
        received_comparecomplete_event(session, msg_proc_obj)
        update_doc_processing_status(
            msg_proc_obj['flow_id'], service_name,False,work_flow_name)
        return message

    def _get_document_pair_info(self, id1, id2):
        info1 = get_work_flow_info_by_id(id1)
        protocol_name_1, doc_file_path_1 = info1['protocol_name'], info1['documentFilePath']
        info2 = get_work_flow_info_by_id(id2)
        protocol_name_2, doc_file_path_2 = info2['protocol_name'], info2['documentFilePath']
        if protocol_name_1 != protocol_name_2:
            raise Exception('protocol name is not same for two documents')
        return protocol_name_1, doc_file_path_1, doc_file_path_2

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to document compare
        """
        from etmfa.db import document_compare_all_permutations, document_compare_tuple
        service_param = self._get_msg_obj(msg)
        flow_name = msg.flow_name
        _id = service_param['id']

        id1 = service_param.get('compare_id1', None)
        id2 = service_param.get('compare_id2', None)

        compare_request_list = []
        session = get_session_obj()
        if not id1:
            compare_request_list = document_compare_all_permutations(
                session, _id, flow_name)
        else:
            protocol_name, doc_file_path_1, doc_file_path_2 = self._get_document_pair_info(
                id1, id2)
            compare_request_list = document_compare_tuple(
                session, _id, flow_name, id1, id2, doc_file_path_1, doc_file_path_2, protocol_name)
        session.close()
        update_doc_processing_status(
            _id, service_name, True,flow_name,len(compare_request_list))
        if not compare_request_list:
            return {}
        return compare_request_list


class Digitizer2NormSOAHandler(DigitizationGenericMessageHandler):

    def on_output_message_adapter(self, service_name, msg: CompositeServiceMessage) -> Dict:
        """
        message to be sent to document compare
        """
        service_param = self._get_msg_obj(msg)
        _id = service_param['id']
        doc_id = service_param['doc_id']
        FeedbackRunId = service_param.get('FeedbackRunId', 0)
        flow_name = msg.flow_name
        flow_id = msg.flow_id
        IQVXMLPath = os.path.join(self.dfs_path, doc_id)
        dig_file_path = get_latest_file_path(
            IQVXMLPath, prefix="D2_", suffix="*.xml*")

        return Dig2XMLPathRequest(_id, doc_id, FeedbackRunId, flow_name, flow_id, dig_file_path, '').__dict__
