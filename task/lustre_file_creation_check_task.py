#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from datetime import datetime

import logging
import os

from clush.RangeSet import RangeSet
from comm.task_handler import TaskCommHandler

from lfsutils import LfsUtils
from prometheus.lustre_file_creation_check import LustreFileCreationCheckResult, LustreFileCreationCheckState
from util.auto_remove_file import AutoRemoveFile
from task.base_task import BaseTask
from util.type_conv_with_none import conv_int

class LustreFileCreationCheckTask(BaseTask):

    def __init__(self, ost_idx: str,
                 lfs_target: str,
                 target_base_dir: str,
                 target_mdt_sub_dir: str,
                 mdt_index_rangeset: str,
                 pushgateway_client_name: str,
                 pushgateway_client_port: str,
                 pushgateway_client_timeout: str) -> None:

        super().__init__()

        self.ost_idx                    = conv_int(ost_idx)
        self.lfs_target                 = lfs_target
        self.target_base_dir            = target_base_dir
        self.target_mdt_sub_dir         = target_mdt_sub_dir
        self.mdt_index_rangeset         = mdt_index_rangeset
        self.pushgateway_client_name    = pushgateway_client_name
        self.pushgateway_client_port    = int(pushgateway_client_port)
        self.pushgateway_client_timeout = int(pushgateway_client_timeout)

        self._lfs_utils         = LfsUtils()
        self._mdt_index_list    = []

        for mdt_idx in RangeSet(mdt_index_rangeset).striter():
            self._mdt_index_list.append(int(mdt_idx))

    def execute(self) -> None:

        try:

            str_ost_idx = str(self.ost_idx)

            if self._lfs_utils.is_ost_idx_active(self.lfs_target, self.ost_idx):

                logging.debug("Found active OST-IDX: %s", str_ost_idx)

                comm_handler = TaskCommHandler(self.pushgateway_client_name, self.pushgateway_client_port, self.pushgateway_client_timeout)
                comm_handler.connect()

                # TODO: Could run in parallel for each MDT or be a seperate task for each MDT+OST...
                for mdt_idx in self._mdt_index_list:

                    try:

                        elapsed_time = None

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

                                logging.debug("%s|%s|%s|%s|%s|%s", self.lfs_target, state, file_path, str_mdt_idx, str_ost_idx, elapsed_time)

                                check_result = LustreFileCreationCheckResult(self.lfs_target, state, mdt_idx, self.ost_idx)

                            else:

                                state = LustreFileCreationCheckState.FAILED

                                logging.debug("%s|%s|%s|%s|%s|%s", self.lfs_target, state, file_path, str_mdt_idx, str_ost_idx, elapsed_time)

                                check_result = LustreFileCreationCheckResult(self.lfs_target, state, mdt_idx, self.ost_idx)

                    except Exception:

                        state = LustreFileCreationCheckState.ERROR

                        if file_path and str_mdt_idx:
                            logging.debug("%s|%s|%s|%s|%s|%s", self.lfs_target, state, file_path, str_mdt_idx, str_ost_idx, elapsed_time)

                        logging.exception('Caught exception in LustreFileCreationCheckTask during inner loop')

                        check_result = LustreFileCreationCheckResult(self.lfs_target, state)

                    logging.debug("Sending check result to pushgateway: %s", check_result)

                    comm_handler.send_string(check_result.to_string())

            else:
                logging.debug("%s|%s|%s", self.lfs_target, LustreFileCreationCheckState.IGNORED, str_ost_idx)

        except Exception:
            logging.exception('Caught exception during task execution')
