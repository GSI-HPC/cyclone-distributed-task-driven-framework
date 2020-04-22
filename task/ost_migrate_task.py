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

from task.base_task import BaseTask


class OstMigrateTask(BaseTask):

    def __init__(self, source_ost, target_ost, filename):

        super(OstMigrateTask, self).__init__()

        self.source_ost = source_ost
        self.target_ost = target_ost
        self.filename = filename

    def execute(self):

        try:
            logging.info(f"{self.source_ost} : {self.target_ost} : {self.filename}")
        except Exception as e:
            logging.error(f"Caught exception in {self.__class__.__name__}: {e}")
