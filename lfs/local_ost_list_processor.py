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
import signal
import time
import os

from multiprocessing import Process
from ctrl.critical_section import CriticalSection
from ctrl.ost_info import OSTInfo


class LocalOstListProcessor(Process):

    def __init__(self, ost_info_queue, lock_ost_queue, config_file_reader):

        super(LocalOstListProcessor, self).__init__()

        self.measure_interval = config_file_reader.measure_interval
        self.ost_select_list = config_file_reader.ost_select_list

        self.ost_info_queue = ost_info_queue
        self.lock_ost_queue = lock_ost_queue

        self.run_flag = False

    def start(self):
        super(LocalOstListProcessor, self).start()

    def run(self):

        self.run_flag = True

        signal.signal(signal.SIGTERM, self._signal_handler_terminate)
        signal.siginterrupt(signal.SIGTERM, True)

        while self.run_flag:

            try:

                logging.debug("LocalOstListProcessor active!")

                ost_info_list = self._create_ost_info_list()

                logging.debug("Length of OST info list: %s" % len(ost_info_list))

                with CriticalSection(self.lock_ost_queue):

                    if not self.ost_info_queue.is_empty():
                        self.ost_info_queue.clear()

                    if ost_info_list:
                        self.ost_info_queue.fill(ost_info_list)

                time.sleep(self.measure_interval)

            except InterruptedError as exception:
                logging.debug("Caught InterruptedError exception.")

            except Exception as exception:
                logging.error("Caught exception in LocalOstListProcessor: %s" %
                              exception)
                os._exit(1)

        logging.debug("LocalOstListProcessor finished!")
        os._exit(0)

    def _signal_handler_terminate(self, signum, frame):

        self.run_flag = False
        logging.debug("LocalOstListProcessor retrieved terminate signal!")

        raise InterruptedError("Received signal to terminate...")

    def _create_ost_info_list(self):

        ost_info_list = list()

        for ost_idx in LocalOstListProcessor._create_active_ost_idx_list(100):
            ost_info_list.append(OSTInfo(str(ost_idx), "OSS-IGNORED"))

        if len(self.ost_select_list):

            select_ost_info_list = list()

            for select_ost_name in self.ost_select_list:

                found_select_ost_name = False

                for ost_info in ost_info_list:

                    if select_ost_name == ost_info.ost_name:

                        logging.debug("Found OST from selected list: %s" %
                                      select_ost_name)

                        if not found_select_ost_name:
                            found_select_ost_name = True

                        select_ost_info_list.append(ost_info)

                        break

                if not found_select_ost_name:
                    raise RuntimeError("OST to select was not found "
                                       "in ost_info_list: %s" % select_ost_name)

            return select_ost_info_list

        else:
            return ost_info_list

    @staticmethod
    def _create_active_ost_idx_list(max_ost_idx=329):

        idx_list = list()

        for i in range(max_ost_idx):
            idx_list.append(i)

        return idx_list


