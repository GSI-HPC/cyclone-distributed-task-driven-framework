#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

"""Module for task generator"""

import logging
import time
import os

from conf.config_value_error import ConfigValueOutOfRangeError
from ctrl.critical_section import CriticalSection
from ctrl.shared_queue import SharedQueue
from ctrl.shared_queue_str import SharedQueueStr
from task.benchmark_task import BenchmarkTask
from task.generator.base_task_generator import BaseTaskGenerator

class BenchmarkTaskGenerator(BaseTaskGenerator):
    """Class for Benchmark Task Generator"""

    def __init__(self, task_queue: SharedQueue, result_queue: SharedQueueStr, config_file: str) -> None:

        super().__init__(task_queue, result_queue, config_file)

        self._num_tasks = self._config.getint('control', 'num_tasks')
        self._poll_time_ms = self._config.getint('control', 'poll_time_ms')

    def validate_config(self) -> None:

        min_num_tasks = 1
        max_num_tasks = 100000000

        if not min_num_tasks <= self._num_tasks <= max_num_tasks:
            raise ConfigValueOutOfRangeError("num_tasks", min_num_tasks, max_num_tasks)

        min_poll_time_ms = 1
        max_poll_time_ms = 1000

        if not min_poll_time_ms <= self._poll_time_ms <= max_poll_time_ms:
            raise ConfigValueOutOfRangeError("poll_time_ms", min_poll_time_ms, max_poll_time_ms)

    def run(self) -> None:

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

                        logging.debug("Polling (%ims)", self._poll_time_ms)
                        time.sleep(self._poll_time_ms / 1000.0)
                else:
                    self._run_flag = False

            if start_time:

                end_time = time.time() * 1000.0
                duration = (end_time - start_time) / 1000.0
                logging.info(f"Count of completed tasks: {len_task_list} - It took: {duration}s")

        except InterruptedError:
            logging.error('Caught InterruptedError exception')

        except Exception:
            logging.exception("Caught exception in %s", self._name)
            logging.info(f"{self._name} exited!")
            os._exit(1)

        logging.info(f"{self._name} finished!")
        os._exit(0)

    def _create_task_list(self) -> list[BenchmarkTask]:

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
