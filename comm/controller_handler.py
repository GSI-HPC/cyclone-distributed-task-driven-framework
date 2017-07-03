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


import zmq

from base_handler import BaseHandler


REQUEST_TIMEOUT = 1000


class ControllerCommHandler(BaseHandler):

    def __init__(self, target, port):
        BaseHandler.__init__(self, target, port)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):

        self.context = zmq.Context()

        if not self.context:
            raise RuntimeError('Failed to create ZMQ context!')

        self.socket = self.context.socket(zmq.REQ)

        if not self.socket:
            raise RuntimeError('Failed to create ZMQ socket!')

        self.socket.connect(self.endpoint)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.is_connected = True

    def disconnect(self):

        if self.is_connected:

            if self.socket:

                self.socket.setsockopt(zmq.LINGER, 0)

                if self.poller:
                    self.poller.unregister(self.socket)

                self.socket.close()

            if self.context:
                self.context.term()

            self.is_connected = False

    def reconnect(self):

        self.disconnect()
        self.connect()

    def recv(self):

        events = dict(self.poller.poll(REQUEST_TIMEOUT))

        if events.get(self.socket) == zmq.POLLIN:

            message = self.socket.recv()

            if message:
                return message

        return None
