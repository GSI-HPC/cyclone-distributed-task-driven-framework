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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import abc
import socket
import zmq

class BaseHandler(metaclass=abc.ABCMeta):

    def __init__(self, target: str, port: int, timeout: int) -> None:
        """
        Parameters
        ----------
        timeout : int
            Timeout is specified in milliseconds
        """
        super().__init__()

        if not target:
            raise RuntimeError('No target set!')

        if not port:
            raise RuntimeError('No communication port set!')

        if not port in range(1024, 65535):
            raise RuntimeError('Communication port must be a number between 1024 and 65535!')

        if timeout < 0:
            raise RuntimeError('No valid timeout is set!')

        self.target  = target
        self.port    = port
        self.timeout = timeout

        self.endpoint = "tcp://" + self.target + ":" + str(self.port)

        self.is_connected = False

        self.fqdn = socket.getfqdn()

        if self.fqdn == 'localhost':
            raise RuntimeError("Fully qualified domain name is not meaningful!")

        self.context : zmq.Context
        self.socket  : zmq.Socket
        self.poller  : zmq.Poller

    @abc.abstractmethod
    def connect(self) -> None:
        return None

    def disconnect(self) -> None:

        if self.is_connected:

            if self.socket:

                self.socket.setsockopt(zmq.LINGER, 0)

                if self.poller:
                    self.poller.unregister(self.socket)

                self.socket.close()

            if self.context:
                self.context.term()

            self.is_connected = False

    def reconnect(self) -> None:

        self.disconnect()
        self.connect()

    def recv_string(self):

        events = dict(self.poller.poll(self.timeout))

        if events.get(self.socket) == zmq.POLLIN:

            message = self.socket.recv_string()

            if message:
                return message

        return None

    def send_string(self, message: str) -> None:
        self.socket.send_string(message)
