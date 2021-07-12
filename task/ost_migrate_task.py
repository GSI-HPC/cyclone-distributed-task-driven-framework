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


import os
import sys
import logging
import distutils.util

from lfs.lfs_utils import LFSUtils
from task.base_task import BaseTask


class OstMigrateTask(BaseTask):

    def __init__(self, filename, source_ost, target_ost, block, skip):

        super().__init__()

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

        self.block = block
        self.skip = skip

        self._lfs_utils = LFSUtils('/usr/bin/lfs')

    def execute(self):

        try:
            self._lfs_utils.migrate_file(self.filename, self.source_ost, self.target_ost, self.block, self.skip)
        except Exception as err:
            logging.error("[OstMigrateTask] Failed to migrate file: %s - Error: %s", self._filename, err)

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
