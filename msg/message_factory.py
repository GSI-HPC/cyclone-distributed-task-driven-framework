#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from abc import ABCMeta

from msg.base_message import BaseMessage
from msg.message_type import MessageType
from msg.task_request import TaskRequest
from msg.task_assign import TaskAssign
from msg.wait_command import WaitCommand
from msg.task_finished import TaskFinished
from msg.acknowledge import Acknowledge
from msg.heartbeat import Heartbeat
from msg.exit_command import ExitCommand

class MessageFactory(metaclass=ABCMeta):

    def __init__(self):
        pass

    @staticmethod
    def create(message):

        if not message:
            raise RuntimeError('Message is not set!')

        message_items = message.split(BaseMessage.field_separator)

        # TODO: len_message_items necessary?
        len_message_items = 0

        if message_items:

            msg_type = message_items[0]

            len_message_items = len(message_items)

        if msg_type == MessageType.TASK_REQUEST() and len_message_items == 2:
            return TaskRequest(message_items[1])

        if msg_type == MessageType.TASK_FINISHED() and len_message_items == 3:
            return TaskFinished(message_items[1], message_items[2])

        if msg_type == MessageType.ACKNOWLEDGE() and len_message_items == 1:
            return Acknowledge()

        if msg_type == MessageType.WAIT_COMMAND() and len_message_items == 2:
            return WaitCommand(message_items[1])

        if msg_type == MessageType.HEARTBEAT() and len_message_items == 2:
            return Heartbeat(message_items[1])

        if msg_type == MessageType.EXIT_COMMAND() and len_message_items == 1:
            return ExitCommand()

        if msg_type == MessageType.TASK_ASSIGN():
            return TaskAssign(message)

        raise RuntimeError(f"No message could be created from: {message}")
