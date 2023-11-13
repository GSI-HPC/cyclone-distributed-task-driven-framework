#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

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
