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
import socket
import zmq


class BaseHandler(object):

    def __init__(self, target, port, poll_timeout):
        
        super(BaseHandler, self).__init__()
        
        __metaclass__ = abc.ABCMeta

        if not target:
            raise RuntimeError('No target set!')

        if not port:
            raise RuntimeError('No communication port set!')

        if not (port in range(1024, 65535)):
            raise RuntimeError('Communication port must be a number between 1024 and 65535!')

        if not poll_timeout:
            raise RuntimeError('No poll timeout is set!')

        self.target = target
        self.port = port
        self.poll_timeout = poll_timeout

        self.endpoint = "tcp://" + self.target + ":" + str(self.port)
        self.context = None
        self.socket = None
        self.poller = None

        self.is_connected = False

        self.fqdn = socket.getfqdn()

        if self.fqdn == 'localhost':
            raise RuntimeError("Fully qualified domain name is not meaningful!")

    @abc.abstractmethod
    def connect(self):
        return None

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

        events = dict(self.poller.poll(self.poll_timeout))

        if events.get(self.socket) == zmq.POLLIN:

            message = self.socket.recv()

            if message:
                return message

        return None

    def send(self, message):
        self.socket.send(message)
