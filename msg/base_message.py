#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import abc

class BaseMessage(metaclass=abc.ABCMeta):
    """Base message of all messages send over the message passing interface."""

    # TODO global constant variable
    field_separator = '|'

    def __init__(self, header, body):

        super().__init__()

        if not header:
            raise RuntimeError('No header is set!')

        self.header = header
        self.body = body

        self._validate()

    # Optional.
    def _validate(self):
        pass

    def type(self):

        if self.header.find(BaseMessage.field_separator) > 0:
            return self.header.split(BaseMessage.field_separator)[0]
        else:
            return self.header

    def to_string(self):

        if self.body:
            return self.header + BaseMessage.field_separator + self.body
        else:
            return self.header

    # TODO add to_byte method?
