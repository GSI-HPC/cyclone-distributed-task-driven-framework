#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import zmq

from comm.base_handler import BaseHandler

class TaskCommHandler(BaseHandler):

    def connect(self) -> None:

        self.context = zmq.Context()

        self.socket = self.context.socket(zmq.PUSH)
        self.socket.setsockopt(zmq.LINGER, self.timeout)
        self.socket.SNDTIMEO = self.timeout
        self.socket.connect(self.endpoint)

    def disconnect(self) -> None:
        """
            Do not disconnect directly on asynchronous communication handler.\n
            This is left to the ZMQ library for the global context and socket handling.\n
        """
        raise RuntimeError('Operation not supported')

    def recv_string(self):
        raise RuntimeError('Operation not supported')
