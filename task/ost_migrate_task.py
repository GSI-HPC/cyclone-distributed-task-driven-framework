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


from lfs.lfs_utils import LfsUtils
from task.base_task import BaseTask

import distutils.util
import logging



class OstMigrateTask(BaseTask):

    def __init__(self, filename, source_ost, target_ost, block, skip):

        super().__init__()

        # TODO: Rethink about object creation by the task factory with empty XML fields...
        # Initialization here for empty files is a bit unhandy.

        # Set later during runtime before task dispatch
        if filename:
            self.filename = filename
        else:
            self._filename = ''

        if source_ost:
            self.source_ost = source_ost
        else:
            self._source_ost = ''

        if target_ost:
            self.target_ost = target_ost
        else:
            self._target_ost = ''

        # Set on initialization based on the XML file
        self.block = block
        self.skip = skip

        self._lfs_utils = LfsUtils()

    def execute(self):

        try:
            logging.info(self._lfs_utils.migrate_file(self.filename, self.source_ost, self.target_ost, self.block, self.skip))
        except Exception:
            logging.exception("[OstMigrateTask] Failed to migrate file: %s", self.filename)

    @property
    def block(self):
        return self._block

    @property
    def skip(self):
        return self._skip

    @property
    def source_ost(self):
        return self._source_ost

    @property
    def target_ost(self):
        return self._target_ost

    @property
    def filename(self):
        return self._filename

    @block.setter
    def block(self, block):

        if block is None:
            raise RuntimeError('block parameter must be a set.')

        if not isinstance(block, str):
            raise TypeError('block argument must be str type.')

        self._block = bool(distutils.util.strtobool(block))

    @skip.setter
    def skip(self, skip):

        if skip is None:
            raise RuntimeError('skip parameter must be a set.')

        if not isinstance(skip, str):
            raise TypeError('skip argument must be str type.')

        self._skip = bool(distutils.util.strtobool(skip))

    @source_ost.setter
    def source_ost(self, idx):
        self._source_ost = int(idx)

    @target_ost.setter
    def target_ost(self, idx):
        self._target_ost = int(idx)

    @filename.setter
    def filename(self, filename):

        if not filename:
            raise RuntimeError('filename not set.')

        if not isinstance(filename, str):
            raise RuntimeError('filename must be a string.')

        self._filename = filename
