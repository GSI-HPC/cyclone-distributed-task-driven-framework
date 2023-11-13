#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import logging
import multiprocessing

from task.base_task import BaseTask

class PoisonPill(BaseTask):
    """PoisonPill is used to push a pseudo task into the task queue for the workers to be freed from blocking access."""

    def __init__(self):

        super().__init__()

        self.tid = 'POISON_PILL'

    def execute(self):
        logging.debug("Worker retrieved poison pill: %s", multiprocessing.current_process().name)
