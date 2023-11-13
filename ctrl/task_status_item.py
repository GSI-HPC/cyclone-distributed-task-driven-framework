#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

class TaskState(object):

    @staticmethod
    def assigned():
        return 1

    @staticmethod
    def finished():
        return 2

class TaskStatusItem:

    def __init__(self, tid, state, controller, timestamp):

        self.tid = tid
        self.state = state
        self.controller = controller
        self.timestamp = timestamp
