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

    def __init__(self, type, body):

        __metaclass__ = abc.ABCMeta

        self.type = type
        self.body = body

        if not self.type:
            raise RuntimeError('No message type is set!')

        if self.body:
            self.message = self.type + BaseMessage.field_separator + self.body
        else:
            if self.body:
                self.message = self.type

        self.validate_body()

    def __str__(self):
        return self.message

    def to_string(self):
        return self.message

    @abc.abstractmethod
    def validate_body(self):
        return None
