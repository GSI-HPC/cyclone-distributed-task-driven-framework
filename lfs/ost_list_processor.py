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


class OSTListProcessor(Process):

    def __init__(self, active_ost_queue, lock_ost_queue, measure_interval, lctl_bin, ost_reg_ex, ip_reg_ex):

        super(OSTListProcessor, self).__init__()

        self.active_ost_queue = active_ost_queue
        self.lock_ost_queue = lock_ost_queue

        self.measure_interval = measure_interval
        self.lctl_bin = lctl_bin
        self.ost_reg_ex = ost_reg_ex
        self.ip_reg_ex = ip_reg_ex

        self.run_flag = False

    def start(self):

        self.run_flag = True

        super(OSTListProcessor, self).start()

    def run(self):

        signal.signal(signal.SIGUSR1, self.signal_handler_shutdown)
        signal.siginterrupt(signal.SIGUSR1, True)

        while self.run_flag:

            try:
                logging.debug("OST Processor active...")

                active_list, inactive_list = self.get_ost_lists()

                with CriticalSection(self.lock_ost_queue):

                    if not self.active_ost_queue.is_empty():
                        self.active_ost_queue.clear()

                    self.active_ost_queue.fill(active_list)

                time.sleep(self.measure_interval)

            except Exception as e:
                logging.error("Caught exception in OST List Processor: " + str(e))
                exit(1)

        logging.debug("OST Processor finished!")
        exit(0)

    def signal_handler_shutdown(self, signal, frame):
        self.run_flag = False

    @staticmethod
    def test_get_ost_lists():

        active_ost_list = list()

        ost_name_prefix = "nyx-OST"

        for i in xrange(0, 10, 1):

            ost_name = None
            i_str = str(i)

            if len(i_str) == 1:
                ost_name = ost_name_prefix + "000" + i_str

            elif len(i_str) == 2:
                ost_name = ost_name_prefix + "00" + i_str

            elif len(i_str) == 3:
                ost_name = ost_name_prefix + "0" + i_str

            elif len(i_str) == 4:
                ost_name = ost_name_prefix + i_str

            else:
                raise RuntimeError('Not supported limit for creating OST test data!')

            active_ost_list.append(ost_name)

        inactive_ost_list = list()
        inactive_ost_list.append('nyx-OST11ef')
        inactive_ost_list.append('nyx-OST11ff')

        return tuple((active_ost_list, inactive_ost_list))

    def get_ost_lists(self):

        ost_ip_dict = self.get_ost_ip_dict()

        # active_ost_list, inactive_ost_list = get_ost_lists(LFS_BIN, OST_RE_PATTERN)

        # Testing only!
        return OSTListProcessor.test_get_ost_lists()

    def get_ost_ip_dict(self):

        ost_ip_dict = dict()

        if not os.path.isfile(self.lctl_bin):
            raise RuntimeError("LCTL binary was not found under: %s" % self.lctl_bin)

        cmd = self.lctl_bin + " get_param 'osc.*.ost_conn_uuid'"

        (status, output) = commands.getstatusoutput(cmd)

        if status > 0:
            raise RuntimeError("Error occurred during read of OST connection UUID information: %s" % output)

        if not output:
            raise RuntimeError("No OST connection UUID information retrieved!")

        # TODO Solve redundancy getting OST names!
        ost_list = output.split('\n')

        for ost_info in ost_list:

            idx_ost_name = ost_info.find('OST')

            if idx_ost_name == -1:
                raise RuntimeError("No OST name found in output line: %s" % ost_info)

            ost_name = ost_info[idx_ost_name: idx_ost_name + 7]
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

            ost_conn_ip = ost_info[idx_ost_conn_uuid + len(ost_conn_uuid_str): idx_ost_conn_uuid_term]

            ost_ip_dict[ost_name] = ost_conn_ip

        return ost_ip_dict


