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
"""Module for task generator"""

import configparser
import logging
import signal
import time
import sys
import os

from ctrl.critical_section import CriticalSection
from task.benchmark_task import BenchmarkTask
from task.generator.base_task_generator import BaseTaskGenerator


class BenchmarkTaskGenerator(BaseTaskGenerator):
    """Class for Benchmark Task Generator"""

    def __init__(self, task_queue, result_queue, config_file):

        super().__init__(task_queue, result_queue, config_file)

        self._num_tasks = self._config.getint('control', 'num_tasks')
        self._poll_time_ms = self._config.getint('control', 'poll_time_ms') / 1000.0

    def run(self):

        logging.info(f"{self._name} active!")

        try:

            task_list = self._create_task_list()
            len_task_list = len(task_list)
            completed_tasks = 0

            with CriticalSection(self._task_queue.lock):

                if not self._task_queue.is_empty():
                    self._task_queue.clear()

                if task_list:
                    self._task_queue.fill(task_list)

            start_time = None

            while self._run_flag:

                if completed_tasks < len_task_list:

                    # No synchronization with controller required, just wait until first task is popped.
                    # This approach is simple and to a certain extend reproducible,
                    # but not totally accurate in the runtime, since the startup time is not measured.
                    if completed_tasks == 1:
                        start_time = time.time() * 1000.0

                    if not self._result_queue.is_empty():

                        tid = self._result_queue.pop()
                        completed_tasks += 1
                        logging.debug("Task completed with TID: %s", tid)
                    else:

                        logging.debug("Polling (%ss)", self._poll_time_ms)
                        time.sleep(self._poll_time_ms)
                else:
                    self._run_flag = False

            if start_time:

                end_time = time.time() * 1000.0
                duration = (end_time - start_time) / 1000.0
                logging.info(f"Count of completed tasks: {len_task_list} - It took: {duration}s")

        except InterruptedError:
            logging.error("Caught InterruptedError exception.")

        except Exception as err:

            _, _, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error(f"Exception in {filename} (line: {exc_tb.tb_lineno}): {err}")
            logging.info(f"{self._name} exited!")
            os._exit(1)

        logging.info(f"{self._name} finished!")
        os._exit(0)

    def _create_task_list(self):

        task_list = list()

        logging.debug("Creating task list...")
        logging.debug("Number of tasks to generate: %i", self._num_tasks)

        for i in range(self._num_tasks):

            # TODO: Add optional/mandatory parameter for TID on the BaseTask class?
            task = BenchmarkTask()
            task.tid = str(i)
            task_list.append(task)

        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Number of tasks generated: %i", len(task_list))

        if self._num_tasks != len(task_list):
            raise RuntimeError("Number of tasks to generate is not equal to length of task list.")

        return task_list
