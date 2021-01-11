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


import configparser
import operator
import logging
import signal
import random
import time
import sys
import os

from datetime import datetime
from enum import Enum, unique
from multiprocessing import Process

from lfs.lfs_utils import LFSUtils
from msg.base_message import BaseMessage
from task.ost_migrate_task import OstMigrateTask
from task.empty_task import EmptyTask


class LustreOstMigrateItem:

    def __init__(self, ost, filename):

        self.ost = ost
        self.filename = filename


@unique
class OSTState(Enum):

    READY = 1
    LOCKED = 2
    BLOCKED = 3
    PENDING_LOCK = 4


class LustreOstFileMigrationTaskGenerator(Process):

    def __init__(self, task_queue, lock_task_queue, result_queue, config_file):

        super().__init__()

        self.task_queue = task_queue
        self.lock_task_queue = lock_task_queue

        self.result_queue = result_queue

        config = configparser.ConfigParser()
        config.read_file(open(config_file))

        self.local_mode = config.getboolean('control', 'local_mode')

        self.threshold_update_fill_level = config.getint('control.threshold', 'update_fill_level')
        self.threshold_reload_files = config.getint('control.threshold', 'reload_files')
        self.threshold_print_caches = config.getint('control.threshold', 'print_caches')

        if not self.local_mode:

            self.lfs_utils = LFSUtils("/usr/bin/lfs")
            self.lfs_path = config.get('lustre', 'fs_path')

        ost_targets = config.get('lustre.migration', 'ost_targets')
        self.ost_target_list = ost_targets.strip().split(",")

        self.input_dir = config.get('lustre.migration', 'input_dir')

        self.ost_fill_threshold = config.getint('lustre.migration', 'ost_fill_threshold')

        self.ost_cache_dict = dict()

        self.ost_source_state_dict = dict()
        self.ost_target_state_dict = dict()

        self.ost_fill_level_dict = dict()

        self.run_flag = False

    def run(self):

        try:

            self.run_flag = True

            signal.signal(signal.SIGTERM, self._signal_handler_terminate)
            signal.siginterrupt(signal.SIGTERM, True)

            logging.info(f"{self.__class__.__name__} started!")

            self._update_ost_fill_level_dict()
            self._init_ost_target_state_dict()
            self._process_input_files()

            next_time_update_fill_level = int(time.time()) + self.threshold_update_fill_level
            next_time_reload_files = int(time.time()) + self.threshold_reload_files
            next_time_print_caches = int(time.time()) + self.threshold_print_caches

            while self.run_flag:

                try:

                    for source_ost in self.ost_source_state_dict:

                        if self.ost_source_state_dict[source_ost] == OSTState.READY:

                            ost_cache = self.ost_cache_dict[source_ost]

                            if ost_cache:

                                for target_ost, target_state in self.ost_target_state_dict.items():

                                    if target_state == OSTState.READY:

                                        item = ost_cache.pop()

                                        if self.local_mode:
                                            task = EmptyTask()
                                        else:
                                            task = OstMigrateTask(
                                                source_ost, target_ost, item.filename)

                                        task.tid = f"{source_ost}:{target_ost}"

                                        logging.debug("Pushing task with TID to task queue: %s", task.tid)
                                        self.task_queue.push(task)

                                        self.ost_source_state_dict[source_ost] = OSTState.BLOCKED
                                        self.ost_target_state_dict[target_ost] = OSTState.BLOCKED

                                        break

                    while not self.result_queue.is_empty():

                        finished_tid = self.result_queue.pop()
                        logging.debug("Popped TID from result queue: %s", finished_tid)

                        source_ost, target_ost = finished_tid.split(":")
                        self._update_ost_state_dict(source_ost, self.ost_source_state_dict)
                        self._update_ost_state_dict(target_ost, self.ost_target_state_dict)

                    last_run_time = int(time.time())

                    if last_run_time >= next_time_update_fill_level:

                        next_time_update_fill_level = \
                            last_run_time + self.threshold_update_fill_level

                        logging.info("###### OST Fill Level Update ######")

                        start_time = datetime.now()
                        self._update_ost_fill_level_dict()
                        elapsed_time = datetime.now() - start_time

                        logging.info(f"Elapsed time: {elapsed_time} - Number of OSTs: {len(self.ost_fill_level_dict)}")

                        if logging.root.isEnabledFor(logging.DEBUG):

                            for ost, fill_level in self.ost_fill_level_dict.items():
                                logging.debug("OST: %s - Fill Level: %i", ost, fill_level)

                        for ost in self.ost_source_state_dict.keys():
                            self._update_ost_source_state_dict(ost)

                        for ost in self.ost_target_state_dict.keys():
                            self._update_ost_target_state_dict(ost)

                    if last_run_time >= next_time_reload_files:

                        next_time_reload_files = last_run_time + self.threshold_reload_files

                        logging.info("###### Loading Input Files ######")

                        self._process_input_files()

                    if last_run_time >= next_time_print_caches:

                        next_time_print_caches = last_run_time + self.threshold_print_caches

                        logging.info("###### OST Cache Sizes ######")

                        ost_cache_ids = self.ost_cache_dict.keys()

                        if ost_cache_ids:

                            for source_ost in sorted(ost_cache_ids, key=int):

                                logging.info(f"OST: {source_ost} - Size: {len(self.ost_cache_dict[source_ost])}")
                        else:
                            logging.info("No OST caches available!")

                        self._deallocate_empty_ost_caches()

                    # TODO: adaptive sleep... ???
                    time.sleep(0.001)

                except InterruptedError:
                    logging.error("Caught InterruptedError exception.")

        except Exception:

            exc_info = sys.exc_info()
            exc_value = exc_info[1]
            exc_tb = exc_info[2]

            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error(f"Exception in {filename} (line: {exc_tb.tb_lineno}): {exc_value}")

            logging.info(f"{self.__class__.__name__} exited!")

            sys.exit(1)

        logging.info(f"{self.__class__.__name__} finished!")

        sys.exit(0)

    def _signal_handler_terminate(self, signum, frame):
        # pylint: disable=unused-argument

        self.run_flag = False

        msg = f"{self.__class__.__name__} retrieved signal to terminate."
        logging.debug(msg)
        raise InterruptedError(msg)

    def _process_input_files(self):

        file_counter = 0

        files = os.listdir(self.input_dir)

        for file in files:

            if file.endswith(".input"):

                file_path = self.input_dir + os.path.sep + file

                self._load_input_file(file_path)

                os.renames(file_path, file_path + ".done")

                file_counter += 1

        if file_counter:
            self._allocate_ost_caches()

        logging.info(f"Count of processed input files: {file_counter}")

    def _load_input_file(self, file_path):

        with open(file_path, mode="r", encoding="UTF-8") as file:

            loaded_counter = 0
            skipped_counter = 0

            for line in file:

                stripped_line = line.strip()

                if BaseMessage.field_separator in stripped_line:
                    logging.warning(f"Skipped line: {line}")
                    skipped_counter += 1
                    continue

                try:

                    ost, filename = stripped_line.split()
                    migrate_item = LustreOstMigrateItem(ost, filename)

                    if ost not in self.ost_cache_dict:
                        self.ost_cache_dict[ost] = list()

                    self.ost_cache_dict[ost].append(migrate_item)

                    loaded_counter += 1

                except ValueError as error:
                    logging.warning(f"Skipped line: {line} ({error})")
                    skipped_counter += 1
            else:
                logging.warning(f"Skipped empty file: {file_path}")

            logging.info(f"Loaded input file: {file_path} - Loaded: {loaded_counter} - Skipped: {skipped_counter}")

    def _allocate_ost_caches(self):

        for ost, cache in self.ost_cache_dict.items():

            if cache:

                if ost not in self.ost_source_state_dict:
                    self._update_ost_source_state_dict(ost)

    def _deallocate_empty_ost_caches(self):

        empty_ost_cache_ids = None

        for ost, cache in self.ost_cache_dict.items():

            if len(cache) == 0:

                if self.ost_source_state_dict[ost] == OSTState.READY \
                        or self.ost_source_state_dict[ost] == OSTState.LOCKED:

                    if not empty_ost_cache_ids:
                        empty_ost_cache_ids = list()

                    empty_ost_cache_ids.append(ost)

        if empty_ost_cache_ids:

            for ost in empty_ost_cache_ids:

                del self.ost_cache_dict[ost]
                del self.ost_source_state_dict[ost]

    def _init_ost_target_state_dict(self):

        for ost in self.ost_target_list:
            self._update_ost_target_state_dict(ost)

    def _update_ost_fill_level_dict(self):

        if self.local_mode:

            self.ost_fill_level_dict.clear()

            for i in range(10):

                ost_idx = str(i)
                fill_level = random.randint(40, 60)

                self.ost_fill_level_dict[ost_idx] = fill_level

        else:
            self.ost_fill_level_dict = \
                self.lfs_utils.retrieve_ost_fill_level(self.lfs_path)

    def _update_ost_source_state_dict(self, ost):
        self._update_ost_state_dict(ost, self.ost_source_state_dict, operator.gt)

    def _update_ost_target_state_dict(self, ost):
        self._update_ost_state_dict(ost, self.ost_target_state_dict, operator.lt)

    def _update_ost_state_dict(self, ost, ost_state_dict, operator_func=None):

        if operator_func:

            if ost not in self.ost_fill_level_dict:
                raise RuntimeError(f"OST not found in ost_fill_level_dict: {ost}")

            fill_level = self.ost_fill_level_dict[ost]

            # operator_func = operator.lt or operator.gt
            if operator_func(fill_level, self.ost_fill_threshold):

                if ost in ost_state_dict:

                    if ost_state_dict[ost] == OSTState.LOCKED:
                        ost_state_dict[ost] = OSTState.READY

                else:
                    ost_state_dict[ost] = OSTState.READY

            else:

                if ost in ost_state_dict:

                    if ost_state_dict[ost] == OSTState.READY:
                        ost_state_dict[ost] = OSTState.LOCKED
                    elif ost_state_dict[ost] == OSTState.BLOCKED:
                        ost_state_dict[ost] = OSTState.PENDING_LOCK

                else:
                    ost_state_dict[ost] = OSTState.LOCKED

        else:

            if ost_state_dict[ost] == OSTState.BLOCKED:
                ost_state_dict[ost] = OSTState.READY
            elif ost_state_dict[ost] == OSTState.PENDING_LOCK:
                ost_state_dict[ost] = OSTState.LOCKED
            else:
                raise RuntimeError("Inconsistency in OST state dictionaries found!")
