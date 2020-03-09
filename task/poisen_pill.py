#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020 Gabriele Iannetti <g.iannetti@gsi.de>
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

from base_task import BaseTask


class PoisenPill(BaseTask):

    def __init__(self):

        super(PoisenPill, self).__init__()

        # Since the monitoring is Lustre specific and a task is bound to an OST,
        # an ost_name has to be set even for a pseudo task like this one.
        # In more detail: The ost_name is pushed after executing a task into the result queue.
        # TODO: Check if the Poisen Pill might just be quit the worker anyway without accessing the result queue.
        self.ost_name = "POISEN_PILL_" + multiprocessing.current_process().name

    def execute(self):
        logging.debug("Worker retrieved poisen pill: '%s'" % multiprocessing.current_process().name)
