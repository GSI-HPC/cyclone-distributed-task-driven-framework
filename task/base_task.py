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

        # Lustre specific: Store the OST and OSS name for each Task.
        self._ost_name = None
        self._oss_name = None

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('This method has to be implemented by a subclass!')

    @property
    def ost_name(self):
        return self._ost_name

    @property
    def oss_name(self):
        return self._oss_name

    @ost_name.setter
    def ost_name(self, ost_name):

        if type(ost_name) is not str:
            raise ValueError('Argument ost_name must be str type!')

        if not ost_name:
            raise ValueError('Argument ost_name must be set!')

        self._ost_name = ost_name

    @oss_name.setter
    def oss_name(self, oss_name):

        if type(oss_name) is not str:
            raise ValueError('Argument oss_name must be str type!')

        if not oss_name:
            raise ValueError('Argument oss_name must be set!')

        self._oss_name = oss_name


