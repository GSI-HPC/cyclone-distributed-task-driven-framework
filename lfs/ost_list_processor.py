#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti <g.iannetti@gsi.de>
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


import commands
import logging
import signal
import time
import os

from multiprocessing import Process
from ctrl.critical_section import CriticalSection
from ctrl.ost_info import OSTInfo


class OSTListProcessor(Process):

    def __init__(self, ost_info_queue, lock_ost_queue, config_file_reader, ost_filter_list=None):

        super(OSTListProcessor, self).__init__()

        self.ost_reg_ex = config_file_reader.ost_reg_ex
        self.ip_reg_ex = config_file_reader.ip_reg_ex

        self.lctl_bin = config_file_reader.lctl_bin
        self.lfs_bin = config_file_reader.lfs_bin
        self.lfs_target = config_file_reader.lfs_target

        self.measure_interval = config_file_reader.measure_interval
        self.ost_filter_list = ost_filter_list

        self.ost_info_queue = ost_info_queue
        self.lock_ost_queue = lock_ost_queue

        self.run_flag = False

    def start(self):

        self.run_flag = True

        super(OSTListProcessor, self).start()

    def run(self):

        signal.signal(signal.SIGUSR1, self.signal_handler_shutdown)
        signal.siginterrupt(signal.SIGUSR1, True)

        while self.run_flag:

            try:
                logging.debug("OSTListProcessor active!")

                ost_info_list = self._create_ost_info_list()

                with CriticalSection(self.lock_ost_queue):

                    if not self.ost_info_queue.is_empty():
                        self.ost_info_queue.clear()

                    if ost_info_list:
                        self.ost_info_queue.fill(ost_info_list)

                time.sleep(self.measure_interval)

            except Exception as e:
                logging.error("Caught exception in OSTListProcessor: %s" % e)
                exit(1)

        logging.debug("OSTListProcessor finished!")
        exit(0)

    def signal_handler_shutdown(self, signal, frame):
        self.run_flag = False

    def _create_ost_info_list(self):

        if not os.path.isfile(self.lctl_bin):
            raise RuntimeError("LCTL binary was not found under: %s" % self.lctl_bin)

        cmd = self.lctl_bin + " get_param 'osc." + self.lfs_target + "-*.ost_conn_uuid'"

        (status, output) = commands.getstatusoutput(cmd)

        if status > 0:
            raise RuntimeError("Error occurred during read of OST connection UUID information: %s" % output)

        if not output:
            raise RuntimeError("No OST connection UUID information retrieved!")

        ost_info_list = list()

        ost_list = output.split('\n')

        for ost_info in ost_list:

            idx_ost_name = ost_info.find('OST')

            if idx_ost_name == -1:
                raise RuntimeError("No OST name found in output line: %s" % ost_info)

            idx_ost_name_term = ost_info.find('-', idx_ost_name)

            if idx_ost_name_term == -1:
                raise RuntimeError("Could not find end of OST name identified by '-' in: %s" % ost_info)

            ost_name = ost_info[idx_ost_name:idx_ost_name_term]

            re_match = self.ost_reg_ex.match(ost_name)

            if not re_match:
                raise RuntimeError("No valid OST name found in output line: %s" % ost_info)

            ost_conn_uuid_str = 'ost_conn_uuid='

            idx_ost_conn_uuid = ost_info.find(ost_conn_uuid_str)

            if idx_ost_conn_uuid == -1:
                raise RuntimeError("Could not find '%s' in line: %s" % (ost_conn_uuid_str, ost_info))

            idx_ost_conn_uuid_term = ost_info.find('@', idx_ost_conn_uuid)

            if idx_ost_conn_uuid_term == -1:
                raise RuntimeError("Could not find terminating '@' for ost_conn_uuid identification: %s" % ost_info)

            oss_ip = ost_info[idx_ost_conn_uuid + len(ost_conn_uuid_str):idx_ost_conn_uuid_term]

            ost_info_list.append(OSTInfo(ost_name, oss_ip))

        if len(ost_info_list) == 0:
            raise RuntimeError("No OST information could be retrieved!")

        if self.ost_filter_list is None:
            return ost_info_list

        else:

            filter_ost_info_list = list()

            for filter_ost_name in self.ost_filter_list:

                found_filter_ost_name = False

                for ost_info in ost_info_list:

                    if filter_ost_name == ost_info.name:

                        filter_ost_info_list.append(ost_info)

                        found_filter_ost_name = True

                        logging.debug("Found OST name to filter: %s" % filter_ost_name)

                        break

                if found_filter_ost_name is False:
                    raise RuntimeError("OST name to filter was not found in ost_info_list: %s" % filter_ost_name)

            return filter_ost_info_list

