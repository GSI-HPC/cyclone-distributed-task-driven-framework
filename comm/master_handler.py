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


class MasterCommHandler(BaseHandler):

    def __init__(self, target, port, poll_timeout):
        super(MasterCommHandler, self).__init__(target, port, poll_timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):

        self.context = zmq.Context()

        if not self.context:
            raise RuntimeError('Failed to create ZMQ context!')

        self.socket = self.context.socket(zmq.REP)

        if not self.socket:
            raise RuntimeError('Failed to create ZMQ socket!')

        self.socket.bind(self.endpoint)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.is_connected = True
