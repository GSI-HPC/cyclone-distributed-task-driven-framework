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


import configparser
import logging
import signal
import copy
import time
import sys
import os

from multiprocessing import Process

from ctrl.critical_section import CriticalSection
from task.print_task import PrintTask


class BenchmarkTaskGenerator(Process):

    def __init__(self,
                 task_queue,
                 lock_task_queue,
                 result_queue,
                 config_file):

        super(BenchmarkTaskGenerator, self).__init__()

        self.task_queue = task_queue
        self.lock_task_queue = lock_task_queue

        self.result_queue = result_queue

        config = configparser.ConfigParser()
        config.read_file(open(config_file))

        self.num_tasks = config.getint('control', 'num_tasks')
        self.poll_time_ms = config.getint('control', 'poll_time_ms') / 1000.0

        self.run_flag = False

    def start(self):
        super(BenchmarkTaskGenerator, self).start()

    def run(self):

        self.run_flag = True

        signal.signal(signal.SIGTERM, self._signal_handler_terminate)
        signal.siginterrupt(signal.SIGTERM, True)

        logging.info("BenchmarkTaskGenerator started!")

        try:

            logging.debug("BenchmarkTaskGenerator active!")

            task_list = self._create_task_list()
            len_task_list = len(task_list)
            completed_tasks = 0

            with CriticalSection(self.lock_task_queue):

                if not self.task_queue.is_empty():
                    self.task_queue.clear()

                if task_list:
                    self.task_queue.fill(task_list)

            start_time = time.time() * 1000.0

            while self.run_flag:

                if completed_tasks < len_task_list:

                    if not self.result_queue.is_empty():

                            # TODO: pop as long as result items are available.
                            tid = self.result_queue.pop()
                            completed_tasks += 1
                            logging.debug("Task completed with TID: %s" % tid)

                    else:

                        logging.debug("Polling (%fs)" % self.poll_time_ms)
                        time.sleep(self.poll_time_ms)
                else:
                    self.run_flag = False

            end_time = time.time() * 1000.0
            duration = (end_time - start_time) / 1000.0

            logging.info("It took: %fs" % duration)

        except InterruptedError as e:
            logging.error("Caught InterruptedError exception.")

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error("Exception in %s (line: %s): %s", filename, exc_tb.tb_lineno, e)
            logging.info("BenchmarkTaskGenerator exited!")
            os._exit(1)

        logging.info("BenchmarkTaskGenerator finished!")
        os._exit(0)

    def _signal_handler_terminate(self, signum, frame):

        self.run_flag = False

        msg = "BenchmarkTaskGenerator retrieved signal to terminate."
        logging.debug(msg)

        # TODO: Handle not as an error.
        raise InterruptedError(msg)

    def _create_task_list(self):

        task_list = list()

        logging.debug("Creating task list...")
        logging.debug("Number of tasks to generate: %i", self.num_tasks)

        for i in range(self.num_tasks):

            # TODO: Add optional/mandatory parameter for TID on the BaseTask class?
            task = PrintTask()
            task.tid = str(i)
            task_list.append(task)

        if logging.root.level <= logging.DEBUG:
            logging.debug("Number of tasks generated: %i", len(task_list))

        if self.num_tasks != len(task_list):
            raise RuntimeError("Number of tasks to generate is not equal to length of task list!")

        return task_list
