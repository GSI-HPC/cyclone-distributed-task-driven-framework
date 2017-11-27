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


class BaseTask(object):
    """
        Base task class to be implemented so a task can be executed by a worker.

        Required fields for Lustre monitoring:

            * name: Name of an given Object Store Target (OST)
            * ip: IP address of the proper Object Store Server (OSS).
    """

    def __init__(self, name, ip):

        __metaclass__ = abc.ABCMeta

        super(BaseTask, self).__init__()

        if not name:
            raise RuntimeError("Setting name property is required!")

        if not ip:
            raise RuntimeError("Setting ip property is required!")

        self.name = name
        self.ip = ip

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('This method has to be implemented by a subclass!')