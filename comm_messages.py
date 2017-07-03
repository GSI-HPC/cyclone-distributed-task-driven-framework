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


import abc


class BaseMessage:

    field_separator = ';'

    def __init__(self, header, body):

        __metaclass__ = abc.ABCMeta

        if not header:
            raise RuntimeError('No Message header is set!')

        if not body:
            raise RuntimeError('No Message body is set!')

        self.header = header
        self.body = body
        self.message = self.header + BaseMessage.field_separator + self.body

        self.validate()

    def __str__(self):
        return self.message

    def to_string(self):
        return self.message

    @abc.abstractmethod
    def validate(self):
        return None


class TaskRequest(BaseMessage):

    def __init__(self, sender):

        if not sender:
            raise RuntimeError('No sender is set!')

        BaseMessage.__init__(self, 'TASK_REQ', sender)

    def validate(self):

        if not self.message:
            raise RuntimeError("Retrieved empty message!")

        if self.message.count(BaseMessage.field_separator) != 1:
            raise RuntimeError("Bad message format detected!")
