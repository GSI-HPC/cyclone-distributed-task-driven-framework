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
from task_response import TaskResponse
from exit_response import ExitResponse


class MessageFactory:

    def __init__(self):
        __metaclass__ = ABCMeta

    @staticmethod
    def create_message(message):

        if not message:
            raise RuntimeError('Message is not set!')

        header = None

        if message.find(BaseMessage.field_separator) >= 0:
            header, body = message.split(BaseMessage.field_separator)
        else:
            header = message

        if header == MessageType.TASK_REQUEST():
            return TaskRequest(body)

        if header == MessageType.TASK_RESPONSE():
            return TaskResponse(body)

        if header == MessageType.EXIT_RESPONSE():
            return ExitResponse()

        raise RuntimeError("No message type recognized: " + message)

    # TODO: Check if Introspection could be used to create objects instead.
    @staticmethod
    def create_task_request(sender):
        return TaskRequest(sender)

    @staticmethod
    def create_task_response(ost_name):
        return TaskResponse(ost_name)

    @staticmethod
    def create_exit_response():
        return ExitResponse()
