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
import time
import sys
import os

from multiprocessing import Process

from ctrl.critical_section import CriticalSection
from task.ost_migrate_task import OstMigrateTask
from task.empty_task import EmptyTask


class LustreOstMigrateItem:

    def __init__(self, ost, filename):

        self.ost = ost
        self.filename = filename


class LustreOstFileMigrationTaskGenerator(Process):

    def __init__(self,
                 task_queue,
                 lock_task_queue,
                 result_queue,
                 lock_result_queue,
                 config_file):

        super(LustreOstFileMigrationTaskGenerator, self).__init__()

        self.task_queue = task_queue
        self.lock_task_queue = lock_task_queue

        self.result_queue = result_queue
        self.lock_result_queue = lock_result_queue

        config = configparser.ConfigParser()
        config.read_file(open(config_file))

        self.target = config.get('lustre', 'target')

        ost_targets = config.get('lustre.migration', 'ost_targets')
        self.ost_target_list = ost_targets.strip().split(",")

        # TODO: Process all files file by file in a given directory.
        self.input_file = config.get('lustre.migration', 'input_file')

        self.ost_source_free_dict = dict()

        self.ost_target_free_dict = dict()

        for ost in self.ost_target_list:
            self.ost_target_free_dict[ost] = True

        self.ost_cache_dict = dict()

        self.run_flag = False

    def start(self):
        super(LustreOstFileMigrationTaskGenerator, self).start()

    def run(self):

        self.run_flag = True

        signal.signal(signal.SIGTERM, self._signal_handler_terminate)
        signal.siginterrupt(signal.SIGTERM, True)

        logging.info(f"{self.__class__.__name__} started!")

        # Do not forget to clear the OST cache/free dict for each initialization run
        self.ost_cache_dict.clear()
        self.ost_source_free_dict.clear()

        self.load_input_file(self.input_file)

        for key in self.ost_cache_dict.keys():
            self.ost_source_free_dict[key] = True

        ost_target_keys = list(self.ost_target_free_dict.keys())
        ost_target_keys_len = len(ost_target_keys)
        ost_target_keys_index = 0

        print_caches_threshold = 900
        print_caches_next_time = int(time.time()) + print_caches_threshold

        while self.run_flag:

            try:

                for ost_idx, ost_cache in self.ost_cache_dict.items():

                    ost_cache = self.ost_cache_dict[ost_idx]

                    if len(ost_cache):

                        if self.ost_source_free_dict[ost_idx]:

                            logging.debug("Free slot for source OST: %s" % ost_idx)

                            for i in range(ost_target_keys_index, ost_target_keys_len):

                                target_ost = ost_target_keys[i]
                                free = self.ost_target_free_dict[target_ost]

                                if free:

                                    logging.debug("Found free target OST: %s" % target_ost)

                                    tid = f"{ost_idx}:{target_ost}"

                                    logging.debug("New TID: %s" % tid)

                                    item = ost_cache.pop()

                                    ## task = EmptyTask()    # Testing
                                    task = OstMigrateTask(ost_idx, target_ost, item.filename)
                                    task.tid = tid

                                    logging.debug(f"Pushing task with TID to task queue: {task.tid}")

                                    with CriticalSection(self.lock_task_queue):
                                        self.task_queue.push(task)

                                    self.ost_source_free_dict[ost_idx] = False
                                    self.ost_target_free_dict[target_ost] = False

                                    ost_target_keys_index += 1

                                    if ost_target_keys_index == ost_target_keys_len:
                                        ost_target_keys_index = 0

                                    break

                    else:
                        logging.debug("Cache is empty for OST: %s" % ost_idx)

                while not self.result_queue.is_empty():

                    with CriticalSection(self.lock_result_queue):

                        finished_tid = self.result_queue.pop()

                        logging.debug(f"Popped TID from result queue: {finished_tid}")

                        source_ost, target_ost = finished_tid.split(":")

                        self.ost_source_free_dict[source_ost] = True
                        self.ost_target_free_dict[target_ost] = True

                last_run_time = int(time.time())

                if last_run_time >= print_caches_next_time:

                    print_caches_next_time = last_run_time + print_caches_threshold

                    logging.info("### Dump - OST Cache Sizes ###")

                    for ost_idx, ost_cache in self.ost_cache_dict.items():
                        logging.info(f"OST: {ost_idx} - Size: {len(ost_cache)}")

                # TODO: adaptive sleep...
                time.sleep(0.5)

            except InterruptedError as e:
                logging.error("Caught InterruptedError exception.")

            except Exception as e:

                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

                logging.error(f"Exception in {filename} (line: {exc_tb.tb_lineno}): {e}")
                logging.info(f"{self.__class__.__name__} exited!")
                os._exit(1)

        logging.info(f"{self.__class__.__name__} finished!")
        os._exit(0)

    def _signal_handler_terminate(self, signum, frame):

        self.run_flag = False

        msg = f"{self.__class__.__name__} retrieved signal to terminate."
        logging.debug(msg)
        raise InterruptedError(msg)

    def load_input_file(self, input_file):

        with open(input_file, "r") as file:

            for line in file:

                try:

                    ost, filename = line.strip().split()

                    migrate_item = LustreOstMigrateItem(ost, filename)

                    if ost not in self.ost_cache_dict:
                        self.ost_cache_dict[ost] = list()

                    self.ost_cache_dict[ost].append(migrate_item)

                except Exception as e:

                    logging.warning(f"Skipped line: {line}")

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

                    logging.error(f"Exception in {filename} (line: {exc_tb.tb_lineno}): {e}")

            logging.info(f"Loaded input file: {filename}")

