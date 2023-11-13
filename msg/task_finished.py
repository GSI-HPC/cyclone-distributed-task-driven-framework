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

class TaskFinished(BaseMessage):
    """Controller sends this message to the master when a task is finished."""

    def __init__(self, sender, tid):

        if not sender:
            raise RuntimeError('No sender is set!')

        if not tid:
            raise RuntimeError('No tid is set!')

        body = sender + self.field_separator + tid

        super().__init__(MessageType.TASK_FINISHED(), body)

    def _validate(self):

        if not self.body:
            raise RuntimeError('No body is set!')

    @property
    def sender(self):
        return self.body.split(BaseMessage.field_separator)[0]

    @property
    def tid(self):
        return self.body.split(BaseMessage.field_separator)[1]
