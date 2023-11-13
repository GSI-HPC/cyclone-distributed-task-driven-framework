#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from msg.base_message import BaseMessage
from msg.message_type import MessageType

class Heartbeat(BaseMessage):
    """
        Heartbeat message is send from the controller to the master to signalize that it is still alive.
        This will happen, when the worker of the controller are all busy for a longer time period.
    """

    def __init__(self, sender):

        if not sender:
            raise RuntimeError('No sender is set!')

        super().__init__(MessageType.HEARTBEAT(), sender)

    def _validate(self):

        if not self.body:
            raise RuntimeError('No body is set!')

    @property
    def sender(self):
        return self.body
