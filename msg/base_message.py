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


class BaseMessage(object):

    field_separator = ';'

    def __init__(self, header, body):

        super(BaseMessage, self).__init__()

        __metaclass__ = abc.ABCMeta

        self.header = header
        self.body = body

        if not self.header:
            raise RuntimeError('No message type is set!')

        self.validate_body()

    def to_string(self):

        message = self.header + BaseMessage.field_separator

        if self.body:
            message += self.body

        return message

    #TODO: Raise EXCEPTION?
    @abc.abstractmethod
    def validate_body(self):
        return None
