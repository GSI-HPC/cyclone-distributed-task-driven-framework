#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


from abc import ABCMeta

from base_message import BaseMessage
from message_type import MessageType
from task_request import TaskRequest
from ost_task_response import OstTaskResponse
from wait_command import WaitCommand
from task_finished import TaskFinished
from acknowledge import Acknowledge
from heartbeat import Heartbeat
from exit_response import ExitResponse


class MessageFactory:

    def __init__(self):
        __metaclass__ = ABCMeta

    @staticmethod
    def create(message):

        if not message:
            raise RuntimeError('Message is not set!')

        message_items = None

        if message.find(BaseMessage.field_separator) >= 1:
            message_items = filter(None, message.split(BaseMessage.field_separator))

        header = None
        len_message_items = 0

        if message_items:

            header = message_items[0]
            len_message_items = len(message_items)

        if header == MessageType.TASK_REQUEST() \
                and len_message_items == 2:
            return TaskRequest(message_items[1])

        if header == MessageType.OST_TASK_RESPONSE() \
                and len_message_items == 2:
            return OstTaskResponse(message_items[1])

        if header == MessageType.TASK_FINISHED() \
                and len_message_items == 3:
            return TaskFinished(message_items[1], message_items[2])

        if header == MessageType.ACKNOWLEDGE() \
                and len_message_items == 1:
            return Acknowledge()

        if header == MessageType.WAIT_COMMAND() \
                and len_message_items == 2:
            return WaitCommand(message_items[1])

        if header == MessageType.HEARTBEAT() \
                and len_message_items == 2:
            return Heartbeat(message_items[1])

        if header == MessageType.EXIT_RESPONSE() \
                and len_message_items == 1:
            return ExitResponse()

        raise RuntimeError("No message could be created from: " + message)
