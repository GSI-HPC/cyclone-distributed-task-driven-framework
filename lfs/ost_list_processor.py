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
import datetime
import logging
import signal
import time
import os

from multiprocessing import Process
from ctrl.critical_section import CriticalSection
from ctrl.ost_info import OSTInfo
from db.ost_perf_result import OSTPerfResult
from db.ost_perf_history_table_handler import OSTPerfHistoryTableHandler


class OSTListProcessor(Process):

    def __init__(self, active_ost_queue, lock_ost_queue, config_file_reader):

        super(OSTListProcessor, self).__init__()

        self.active_ost_queue = active_ost_queue
        self.lock_ost_queue = lock_ost_queue

        self.measure_interval = config_file_reader.measure_interval
        self.lctl_bin = config_file_reader.lctl_bin
        self.lfs_bin = config_file_reader.lfs_bin
        self.lfs_target = config_file_reader.lfs_target

        self.ost_reg_ex = config_file_reader.ost_reg_ex
        self.ip_reg_ex = config_file_reader.ip_reg_ex

        self.total_size_bytes = config_file_reader.total_size_bytes

        self.run_flag = False

        self.history_table_handler = \
            OSTPerfHistoryTableHandler(config_file_reader.host,
                                       config_file_reader.user,
                                       config_file_reader.passwd,
                                       config_file_reader.db,
                                       config_file_reader.table)

    def start(self):

        self.run_flag = True

        super(OSTListProcessor, self).start()

    def run(self):

        signal.signal(signal.SIGUSR1, self.signal_handler_shutdown)
        signal.siginterrupt(signal.SIGUSR1, True)

        while self.run_flag:

            try:
                logging.debug("OST List Processor active!")

                active_ost_info_list, inactive_ost_info_list = self._create_ost_info_lists()

                with CriticalSection(self.lock_ost_queue):

                    if not self.active_ost_queue.is_empty():
                        self.active_ost_queue.clear()

                    if active_ost_info_list:
                        self.active_ost_queue.fill(active_ost_info_list)

                if inactive_ost_info_list:

                    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    for ost_info in inactive_ost_info_list:

                        ost_perf_result = \
                            OSTPerfResult(timestamp,
                                          timestamp,
                                          ost_info.name,
                                          ost_info.ip,
                                          self.total_size_bytes,
                                          0,
                                          0,
                                          0,
                                          0)

                        self.history_table_handler.insert(ost_perf_result)

                    if self.history_table_handler.count():

                        self.history_table_handler.store()
                        self.history_table_handler.clear()

                time.sleep(self.measure_interval)

            except Exception as e:
                logging.error("Caught exception in OST List Processor: %s" % e)
                exit(1)

        logging.debug("OST Processor finished!")
        exit(0)

    def signal_handler_shutdown(self, signal, frame):
        self.run_flag = False

    def _create_ost_info_lists(self):

        ost_ip_dict = self._create_ost_ip_dict()

        # Testing with a small set of OSTs...
        # active_ost_list, inactive_ost_list = self._create_ost_state_test_lists()

        active_ost_list, inactive_ost_list = self._create_ost_state_lists()

        active_ost_ip_dict = self._create_ost_info_list(active_ost_list, ost_ip_dict)
        inactive_ost_ip_dict = self._create_ost_info_list(inactive_ost_list, ost_ip_dict)

        return active_ost_ip_dict, inactive_ost_ip_dict

    def _create_ost_ip_dict(self):

        ost_ip_dict = dict()

        if not os.path.isfile(self.lctl_bin):
            raise RuntimeError("LCTL binary was not found under: %s" % self.lctl_bin)

        cmd = self.lctl_bin + " get_param 'osc." + self.lfs_target + "-*.ost_conn_uuid'"

        (status, output) = commands.getstatusoutput(cmd)

        if status > 0:
            raise RuntimeError("Error occurred during read of OST connection UUID information: %s" % output)

        if not output:
            raise RuntimeError("No OST connection UUID information retrieved!")

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

            ost_conn_ip = ost_info[idx_ost_conn_uuid + len(ost_conn_uuid_str):idx_ost_conn_uuid_term]

            ost_ip_dict[ost_name] = ost_conn_ip

        return ost_ip_dict

    def _create_ost_state_test_lists(self):

        active_ost_list = list()
        inactive_ost_list = list()

        active_ost_list.append('OST0000')
        active_ost_list.append('OST0001')
        active_ost_list.append('OST0002')
        active_ost_list.append('OST0003')
        active_ost_list.append('OST0004')
        active_ost_list.append('OST0005')
        active_ost_list.append('OST0006')
        active_ost_list.append('OST0007')
        active_ost_list.append('OST0008')
        active_ost_list.append('OST0009')
        active_ost_list.append('OST0010')
        active_ost_list.append('OST0011')
        active_ost_list.append('OST0012')
        active_ost_list.append('OST0013')
        active_ost_list.append('OST0014')
        active_ost_list.append('OST0015')
        active_ost_list.append('OST0016')
        active_ost_list.append('OST0017')

        return tuple((active_ost_list, inactive_ost_list))

    def _create_ost_state_lists(self):

        active_ost_list = list()
        inactive_ost_list = list()

        if not os.path.isfile(self.lfs_bin):
            raise RuntimeError("LFS binary was not found under: %s" % self.lfs_bin)

        cmd = self.lctl_bin + " get_param 'osc." + self.lfs_target + "-*.active'"

        (status, output) = commands.getstatusoutput(cmd)

        if status > 0:
            raise RuntimeError("Error occurred during check on OSTs: %s" % output)

        if not output:
            raise RuntimeError("Check OSTs returned an empty result!")

        ost_list = output.split('\n')

        for ost_info in ost_list:

            if ost_info.find(self.lfs_target) == -1:
                raise RuntimeError("Could not find file system in the OST info output line: %s" % ost_info)

            idx_ost_name = ost_info.find('OST')

            if idx_ost_name == -1:
                raise RuntimeError("No OST name found in output line: %s" % ost_info)

            idx_ost_name_term = ost_info.find('-', idx_ost_name)

            if idx_ost_name_term == -1:
                raise RuntimeError("Could not find end of OST name identified by '-' in: %s" % ost_info)

            ost_name = ost_info[idx_ost_name:idx_ost_name_term]

            re_match = self.ost_reg_ex.match(ost_name)

            if not re_match:
                raise RuntimeError("No valid OST name found in line: %s" % ost_info)

            if 'active=1' in ost_info:
                # logging.debug("Found active OST: %s" % ost_name)
                active_ost_list.append(ost_name)

            else:
                # logging.debug("Found inactive OST: %s" % ost_name)
                inactive_ost_list.append(ost_name)

        return tuple((active_ost_list, inactive_ost_list))

    def _create_ost_info_list(self, ost_list, ost_ip_dict):

        ost_info_list = list()

        for ost_name in ost_list:

            if ost_name in ost_ip_dict:

                ost_ip_adr = ost_ip_dict[ost_name]

                if ost_ip_adr:
                    ost_info_list.append(OSTInfo(ost_name, ost_ip_adr))
                else:
                    raise RuntimeError("No IP could be found for the OST: %s" % ost_name)
            else:
                raise RuntimeError("No entry could be found in the IP map for the OST: %s" % ost_name)

        return ost_info_list
