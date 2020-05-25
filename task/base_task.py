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


class BaseTask(object):
    """Base task class to be implemented so a task can be executed by a worker."""

    def __init__(self):

        __metaclass__ = abc.ABCMeta

        super(BaseTask, self).__init__()

        # TODO: Should have no property and setter method,
        #       since the attribute is private.
        self._tid = None

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('Must be implemented in subclass!')

    @property
    def tid(self):
        return self._tid

    @tid.setter
    def tid(self, tid):

        if type(tid) is not str:
            raise ValueError('Argument tid must be str type!')

        if not tid:
            raise ValueError('Argument tid must be set!')

        self._tid = tid


