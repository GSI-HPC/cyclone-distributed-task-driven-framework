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

class Acknowledge(BaseMessage):
    """
        Master sends this message to the controller for acknowledging a previous message from the controller
        (e.g. a task is finished or heartbeat message),

        This is required for the request and response model to not cause inconsistency in the communication model!
    """

    def __init__(self):
        super().__init__(MessageType.ACKNOWLEDGE(), '')

    def _validate(self):
        pass
