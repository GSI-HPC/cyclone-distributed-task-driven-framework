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


import time
import logging
import signal

from multiprocessing import Process
from ctrl.critical_section import CriticalSection


class OstListProcessor(Process):

    def __init__(self, active_ost_queue, measure_interval, lock_ost_queue):

        super(OstListProcessor, self).__init__()

        self.active_ost_queue = active_ost_queue
        self.measure_interval = measure_interval
        self.lock_ost_queue = lock_ost_queue

        self.run_flag = False

    def start(self):

        self.run_flag = True

        super(OstListProcessor, self).start()

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

        logging.debug("OST Processor finished!")
        exit(0)

    def signal_handler_shutdown(self, signal, frame):
        self.run_flag = False

    def get_ost_lists(self):

        active_ost_list = list()
        active_ost_list.append('nyx-OST0000')
        active_ost_list.append('nyx-OST0001')
        active_ost_list.append('nyx-OST0002')
        active_ost_list.append('nyx-OST0003')


        inactive_ost_list = list()
        inactive_ost_list.append('nyx-OST11ef')
        inactive_ost_list.append('nyx-OST11ff')

        return tuple((active_ost_list, inactive_ost_list))
