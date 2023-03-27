import time
import zmq
import json
from enum import Enum, auto
from dataclasses import dataclass
import os
from multiprocessing import Process


class MqStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"


class MsqType(Enum):
    ADD_CUSTOM_WORKFLOW = "add_custom_workflow"
    INFO = "info"
    COMMAND = "command"
    REGISTER = "register"


@dataclass
class MqReplyMsg():
    status: str
    msg: dict


@dataclass
class MqReqMsg():
    type: str
    msg: dict


class MqReceiver():
    def __init__(self, port, callback=None):
        self.callback = callback
        context = zmq.Context()
        self.keep_running = True
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{port}")

    def stop(self):
        self.keep_running = False

    def _recv(self):
        message = self.socket.recv()
        msg_obj = json.loads(message)
        reply_data = None
        if self.callback:
            reply_data = self.callback(msg_obj)
        reply_data = '' if not reply_data else reply_data
        return reply_data

    def _send(self, reply):
        msg_obj = json.dumps(reply)
        self.socket.send_string(msg_obj)

    def run(self):
        while (self.keep_running):
            reply_msg = {}
            try:
                reply = self._recv()
                reply_msg = MqReplyMsg(
                    status=MqStatus.OK.value, msg=reply).__dict__
            except Exception as e:
                reply_msg = MqReplyMsg(
                    status=MqStatus.ERROR.value, msg=str(e)).__dict__
            finally:
                self._send(reply_msg)
                time.sleep(0.5)


class MqSender():
    def __init__(self, port):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f"tcp://localhost:{port}")

    def send(self, msg):
        msg_obj = json.dumps(msg)
        self.socket.send_string(msg_obj)
        reply = self.socket.recv()
        msg_obj = json.loads(reply)
        return msg_obj
