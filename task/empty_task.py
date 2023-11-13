#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from task.base_task import BaseTask

class EmptyTask(BaseTask):

    def __init__(self):
        super().__init__()

    def execute(self):
        pass
