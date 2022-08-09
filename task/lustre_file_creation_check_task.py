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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from datetime import datetime

import logging
import os

from clush.RangeSet import RangeSet
from comm.task_handler import TaskCommHandler

from lfs.lfs_utils import LfsUtils
from prometheus.lustre_file_creation_check import LustreFileCreationCheckResult, LustreFileCreationCheckState
from util.auto_remove_file import AutoRemoveFile
from task.base_task import BaseTask

class LustreFileCreationCheckTask(BaseTask):

    def __init__(self, lfs_target: str, target_base_dir: str, target_mdt_sub_dir: str, mdt_index_rangeset: str, ost_idx: str, pushgateway_name: str, pushgateway_port: str) -> None:

        super().__init__()

        self.lfs_target         = lfs_target
        self.target_base_dir    = target_base_dir
        self.target_mdt_sub_dir = target_mdt_sub_dir
        self.mdt_index_rangeset = mdt_index_rangeset
        self.ost_idx            = ost_idx
        self.pushgateway_name   = pushgateway_name
        self.pushgateway_port   = pushgateway_port

        self._lfs_utils         = LfsUtils()
        self._mdt_index_list    = []

        for mdt_idx in RangeSet(mdt_index_rangeset).striter():
            self._mdt_index_list.append(int(mdt_idx))

    @property
    def ost_idx(self) -> int:
        return self._ost_idx

    @ost_idx.setter
    def ost_idx(self, ost_idx: str) -> None:

        type_ost_idx = type(ost_idx)

        if type_ost_idx is int:
            self._ost_idx = ost_idx
        elif type_ost_idx is str and ost_idx:
            self._ost_idx = int(ost_idx)
        else:
            self._ost_idx = None

    @property
    def pushgateway_port(self) -> int:
        return self._pushgateway_port

    @pushgateway_port.setter
    def pushgateway_port(self, pushgateway_port: str) -> None:

        type_pushgateway_port = type(pushgateway_port)

        if type_pushgateway_port is int:
            self._pushgateway_port = pushgateway_port
        elif type_pushgateway_port is str and pushgateway_port:
            self._pushgateway_port = int(pushgateway_port)
        else:
            self._pushgateway_port = None

    def execute(self) -> None:

        try:

            str_ost_idx = str(self.ost_idx)

            if self._lfs_utils.is_ost_idx_active(self.lfs_target, self.ost_idx):

                # TODO: Introduce different debug level... for internal framework and task specific messages.
                logging.debug("Found active OST-IDX: %s", str_ost_idx)

                comm_handler = None

                if self.pushgateway_name and self.pushgateway_port:
                    comm_handler = TaskCommHandler(self.pushgateway_name, self.pushgateway_port, 10000)
                    comm_handler.connect()

                # TODO: Could run in parallel for each MDT or be a seperate task for each MDT+OST...
                for mdt_idx in self._mdt_index_list:

                    try:

                        str_mdt_idx = str(mdt_idx)

                        file_path = f"{self.target_base_dir}{os.path.sep}{self.target_mdt_sub_dir}{str_mdt_idx}{os.path.sep}{str_ost_idx}_file_creation_check.tmp"

                        with AutoRemoveFile(file_path):
                            if os.path.exists(file_path):
                                os.remove(file_path)

                        start_time = datetime.now()
                        self._lfs_utils.set_ost_file_stripe(file_path, self.ost_idx)
                        elapsed_time = datetime.now() - start_time

                        current_ost_idx = int(self._lfs_utils.stripe_info(file_path).index)

                        if self.ost_idx == current_ost_idx:

                            state = LustreFileCreationCheckState.OK

                            # TODO task info level or internal debug messages are more verbose level?
                            logging.debug("%s|%s|%s|%s|%s|%s", self.lfs_target, state, file_path, str_mdt_idx, str_ost_idx, elapsed_time)

                            check_result = LustreFileCreationCheckResult(self.lfs_target, state, mdt_idx, self.ost_idx)

                        else:

                            state = LustreFileCreationCheckState.FAILED

                            # TODO task info level or internal debug messages are more verbose level?
                            logging.debug("%s|%s|%s|%s|%s|%s", self.lfs_target, state, file_path, str_mdt_idx, str_ost_idx, elapsed_time)

                            check_result = LustreFileCreationCheckResult(self.lfs_target, state, mdt_idx, self.ost_idx)

                    except Exception:

                        state = LustreFileCreationCheckState.ERROR

                        if file_path and str_mdt_idx:
                            logging.debug("%s|%s|%s|%s|%s|%s", self.lfs_target, state, file_path, str_mdt_idx, str_ost_idx, elapsed_time)

                        logging.exception('Caught exception in LustreFileCreationCheckTask during inner loop')

                        check_result = LustreFileCreationCheckResult(self.lfs_target, state)

                    # TODO task info level or internal debug messages are more verbose level?
                    logging.debug(check_result)

                    if comm_handler:
                        comm_handler.send_string(check_result.to_string())
                        logging.debug("Sent check result to pushgateway: %s", check_result)

            else:
                logging.debug("%s|%s|%s", self.lfs_target, LustreFileCreationCheckState.IGNORED, str_ost_idx)

        except Exception:
            logging.exception('Caught exception in LustreFileCreationCheckTask')
