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

class WaitCommand(BaseMessage):
    """The Master sends this message to a controller to let the controller wait for a certain time in seconds."""

    def __init__(self, duration):
        super().__init__(MessageType.WAIT_COMMAND(), str(duration))

    def _validate(self):

        if not self.body:
            raise RuntimeError('No body is set!')

        # Validate duration as int value...
        # TODO: 0-...

    @property
    def duration(self):
        return int(self.body)
