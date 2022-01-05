#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import multiprocessing

from task.base_task import BaseTask

class PoisonPill(BaseTask):
    """PoisonPill is used to push a pseudo task into the task queue for the workers to be freed from blocking access."""

    def __init__(self):

        super().__init__()

        self.tid = "POISON_PILL"

    def execute(self):
        logging.debug("Worker retrieved poison pill: %s", multiprocessing.current_process().name)
