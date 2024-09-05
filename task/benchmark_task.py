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
import os
import time

from task.base_task import BaseTask

class BenchmarkTask(BaseTask):

    def __init__(self):
        super().__init__()

    def execute(self):

        try:

            pid = os.getpid()
            outfile = f"/tmp/benchmark_task_{pid}.tmp"

            tid_num = int(self.tid)
            waittime = (tid_num % 101 / 1000) # Up to 100ms
            time.sleep(waittime)

            with open(outfile, "a") as myfile:
                myfile.write(f"TID: {tid_num} - PID: {pid} - Wait: {waittime}\n")

        except Exception:
            logging.exception('Caught exception during task execution')
