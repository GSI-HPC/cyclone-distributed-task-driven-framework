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


class SocketHandler():

    def __init__(object, target, port):

        __metaclass__ = abc.ABCMeta

        if not target:
            raise RuntimeError('No target set!')

        if not port:
            raise RuntimeError('No communication port set!')

        if not (port in range(1024, 65535)):
            raise RuntimeError('Communication port must be a number between 1024 and 65535!')

        object.target = target
        object.port = port

        object.endpoint = "tcp://" + object.target + ":" + str(object.port)
        object.context = None
        object.socket = None
        object.poller = None

        object.is_connected = False

    @abc.abstractmethod
    def connect(self):
        return None

    @abc.abstractmethod
    def disconnect(self):
        return None

    @classmethod
    def reconnect(self):

        self.disconnect()
        self.connect()
