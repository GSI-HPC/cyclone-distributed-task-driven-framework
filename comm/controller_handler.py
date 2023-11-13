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

class ControllerCommHandler(BaseHandler):

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
