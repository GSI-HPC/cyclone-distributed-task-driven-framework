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


from base_message import BaseMessage
from message_type import MessageType
from task_request import TaskRequest

from abc import ABCMeta


class MessageFactory:

    def __init__(self):
        __metaclass__ = ABCMeta

    @staticmethod
    def create_message(message):

        if not message:
            raise RuntimeError('Message text is not set!')

        header, body = message.split(BaseMessage.field_separator)

        if header == MessageType.TASK_REQUEST():
            task_request = TaskRequest(body)
            return task_request
        else:
            raise RuntimeError("No message type recognized: " + message)