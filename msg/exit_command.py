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

class ExitCommand(BaseMessage):
    """Master sends this message to the controller when they are requesting a task and it is time to exit."""

    def __init__(self):
        super().__init__(MessageType.EXIT_COMMAND(), '')

    def _validate(self):
        pass
