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


class TaskAssign(BaseMessage):
    """The Master sends this message to a controller to assign a task."""

    def __init__(self, ost_name, ost_ip, block_size_bytes, total_size_bytes):

        if not ost_name:
            raise RuntimeError('No OST name is set!')

        if not ost_ip:
            raise RuntimeError('No OST IP is set!')

        if not block_size_bytes:
            raise RuntimeError('No block size in bytes is set!')

        if not total_size_bytes:
            raise RuntimeError('No total size in bytes is set!')

        body = ost_name \
            + self.field_separator \
            + ost_ip \
            + self.field_separator \
            + str(block_size_bytes) \
            + self.field_separator \
            + str(total_size_bytes)

        super(TaskAssign, self).__init__(MessageType.TASK_ASSIGN(), body)

    def validate_body(self):

        if not self.body:
            raise RuntimeError('No body is set!')

    @property
    def ost_name(self):
        return self.body.split(BaseMessage.field_separator)[0]

    @property
    def ost_ip(self):
        return self.body.split(BaseMessage.field_separator)[1]

    @property
    def block_size_bytes(self):
        return self.body.split(BaseMessage.field_separator)[2]

    @property
    def total_size_bytes(self):
        return self.body.split(BaseMessage.field_separator)[3]
