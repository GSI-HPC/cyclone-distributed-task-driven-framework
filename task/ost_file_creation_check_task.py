#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Gabriele Iannetti <g.iannetti@gsi.de>
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
import os

from lfs.lfs_utils import LfsUtils
from util.auto_remove_file import AutoRemoveFile
from task.base_task import BaseTask


class OstFileCreationCheckTask(BaseTask):

    def __init__(self, lfs_target: str, target_dir: str, ost_idx: str) -> None:

        super().__init__()

        self.lfs_target = lfs_target
        self.target_dir = target_dir
        self.ost_idx    = ost_idx

        self._lfs_utils = LfsUtils()

    @property
    def ost_idx(self) -> int:
        return self._ost_idx

    @ost_idx.setter
    def ost_idx(self, ost_idx: str):

        type_ost_idx = type(ost_idx)

        if type_ost_idx is int:
            self._ost_idx = ost_idx
        elif type_ost_idx is str and ost_idx:
            self._ost_idx = int(ost_idx)
        else:
            self._ost_idx = None

    def execute(self) -> None:

        try:

            if self._lfs_utils.is_ost_idx_active(self.lfs_target, self.ost_idx):

                str_ost_idx = str(self.ost_idx)

                logging.debug("Found active OST-IDX: %s", str_ost_idx)

                file_path = f"{self.target_dir}{os.path.sep}{str_ost_idx}_file_creation_check.tmp"

                with AutoRemoveFile(file_path):

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    self._lfs_utils.set_ost_file_stripe(file_path, self.ost_idx)

                    current_ost_idx = int(self._lfs_utils.stripe_info(file_path).index)

                    if self.ost_idx == current_ost_idx:
                        logging.info(f"OK|{file_path}|{str_ost_idx}")
                    else:
                        logging.info(f"FAILED|{file_path}|{str_ost_idx}|{current_ost_idx}")

            else:
                logging.debug("Found non-active OST: %s", str_ost_idx)

        except Exception as err:
            logging.info(f"ERROR|{file_path}|{str_ost_idx}|{err}")
            logging.exception("Caught exception in OstFileCreationCheckTask")
