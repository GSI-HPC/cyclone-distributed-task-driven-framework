#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020 Gabriele Iannetti <g.iannetti@gsi.de>
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
    """Base message of all messages send over the message passing interface."""

    field_separator = ';'

    def __init__(self, header, body):

        __metaclass__ = abc.ABCMeta

        super(BaseMessage, self).__init__()

        if not header:
            raise RuntimeError('No header is set!')

        self.header = header
        self.body = body

        self._validate()

    # Optional.
    def _validate(self):
        pass

    def type(self):

        if self.header.find(BaseMessage.field_separator):
            return filter(None, self.header.split(BaseMessage.field_separator))[0]
        else:
            return self.header

    def to_string(self):

        if self.body:
            return self.header + BaseMessage.field_separator + self.body
        else:
            return self.header

