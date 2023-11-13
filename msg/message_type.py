#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from abc import ABCMeta

class MessageType(metaclass=ABCMeta):

    def __init__(self):
        pass

    @staticmethod
    def TASK_REQUEST():
        return 'TASK_REQ'

    @staticmethod
    def TASK_ASSIGN():
        return 'TASK_ASS'

    @staticmethod
    def WAIT_COMMAND():
        return 'WAIT_CMD'

    @staticmethod
    def TASK_FINISHED():
        return 'TASK_FIN'

    @staticmethod
    def ACKNOWLEDGE():
        return 'ACK'

    @staticmethod
    def HEARTBEAT():
        return 'HEARTBEAT'

    @staticmethod
    def EXIT_COMMAND():
        return 'EXIT_CMD'
