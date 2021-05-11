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

import operator
import logging
import random
import time
import sys
import os

from datetime import datetime
from enum import Enum, unique

from clush.RangeSet import RangeSet
from conf.config_value_error import ConfigValueError, ConfigValueOutOfRangeError
from lfs.lfs_utils import LFSUtils
from msg.base_message import BaseMessage
from task.ost_migrate_task import OstMigrateTask
from task.empty_task import EmptyTask
from task.generator.base_task_generator import BaseTaskGenerator


class LustreOstMigrateItem:

    def __init__(self, ost, filename):

        self.ost = ost
        self.filename = filename


# TODO: Add description!
@unique
class OSTState(Enum):

    READY = 1
    LOCKED = 2
    BLOCKED = 3
    PENDING_LOCK = 4


class LustreOstMigrationTaskGenerator(BaseTaskGenerator):
    """Class for LustreOSTMigrationTaskGenerator"""

    def __init__(self, task_queue, result_queue, config_file):

        super().__init__(task_queue, result_queue, config_file)

        self.local_mode = self._config.getboolean('control', 'local_mode')

        if self.local_mode:
            self.num_osts = self._config.getint('control.local_mode', 'num_osts')
        else:
            self.lfs_utils = LFSUtils("/usr/bin/lfs")
            self.lfs_path = self._config.get('lustre', 'fs_path')

        self.threshold_update_fill_level = self._config.getint('control.threshold', 'update_fill_level')
        self.threshold_reload_files = self._config.getint('control.threshold', 'reload_files')
        self.threshold_print_caches = self._config.getint('control.threshold', 'print_caches')

        ost_targets = self._config.get('migration', 'ost_targets')
        self.ost_target_list = list(RangeSet(ost_targets).striter())

        self.input_dir = self._config.get('migration', 'input_dir')

        self.ost_fill_level_threshold_source = self._config.getint('migration', 'ost_fill_level_threshold_source')
        self.ost_fill_level_threshold_target = self._config.getint('migration', 'ost_fill_level_threshold_target')

        self.ost_cache_dict = dict()

        self.ost_source_state_dict = dict()
        self.ost_target_state_dict = dict()

        self.ost_fill_level_dict = dict()

    def validate_config(self):

        if self.local_mode:

            min_num_osts = 1
            max_num_osts = 1000

            if not min_num_osts <= self.num_osts <= max_num_osts:
                raise ConfigValueOutOfRangeError("num_osts", min_num_osts, max_num_osts)

        else:
            if not os.path.isdir(self.lfs_path):
                raise ConfigValueError("lfs_path does not point to a directory: %s" % self.lfs_path)

        min_threshold_seconds = 1
        max_threshold_seconds = 3600

        if not min_threshold_seconds <= self.threshold_update_fill_level <= max_threshold_seconds:
            raise ConfigValueOutOfRangeError("update_fill_level", min_threshold_seconds, max_threshold_seconds)

        if not min_threshold_seconds <= self.threshold_reload_files <= max_threshold_seconds:
            raise ConfigValueOutOfRangeError("reload_files", min_threshold_seconds, max_threshold_seconds)

        if not min_threshold_seconds <= self.threshold_print_caches <= max_threshold_seconds:
            raise ConfigValueOutOfRangeError("print_caches", min_threshold_seconds, max_threshold_seconds)

        if not os.path.isdir(self.input_dir):
            raise ConfigValueError("input_dir does not point to a directory: %s" % self.input_dir)

        min_ost_fill_threshold_source = 0
        min_ost_fill_threshold_target = 0
        max_ost_fill_threshold = 90

        if not min_ost_fill_threshold_source <= self.ost_fill_level_threshold_source <= max_ost_fill_threshold:
            raise ConfigValueOutOfRangeError("ost_fill_level_threshold_source",
                                             min_ost_fill_threshold_source,
                                             max_ost_fill_threshold)

        if not min_ost_fill_threshold_target <= self.ost_fill_level_threshold_target <= max_ost_fill_threshold:
            raise ConfigValueOutOfRangeError("ost_fill_level_threshold_target",
                                             min_ost_fill_threshold_target,
                                             max_ost_fill_threshold)

        min_ost_target_index = 0
        max_ost_target_index = 1000

        if not min_ost_target_index <= int(self.ost_target_list[0]) <= max_ost_target_index:
            raise ConfigValueOutOfRangeError("min(ost_targets)", min_ost_target_index, max_ost_target_index)

        if len(self.ost_target_list) > 1 and \
            not min_ost_target_index <= int(self.ost_target_list[-1]) <= max_ost_target_index:
            raise ConfigValueOutOfRangeError("max(ost_targets)", min_ost_target_index, max_ost_target_index)

    def run(self):

        logging.info("%s active!", self._name)

        try:

            self._update_ost_fill_level_dict()
            self._init_ost_target_state_dict()
            self._process_input_files()

            next_time_update_fill_level = int(time.time()) + self.threshold_update_fill_level
            next_time_reload_files = int(time.time()) + self.threshold_reload_files
            next_time_print_caches = int(time.time()) + self.threshold_print_caches

            while self._run_flag:

                try:

                    for source_ost in self.ost_source_state_dict:

                        if self.ost_source_state_dict[source_ost] == OSTState.READY:

                            ost_cache = self.ost_cache_dict[source_ost]

                            if ost_cache:

                                for target_ost, target_state in self.ost_target_state_dict.items():

                                    if target_state == OSTState.READY:

                                        item = ost_cache.pop()

                                        # TODO: Use one initialized task instead.
                                        if not self.local_mode:
                                            task = OstMigrateTask(source_ost, target_ost, item.filename)
                                        else:
                                            task = EmptyTask()

                                        task.tid = f"{source_ost}:{target_ost}"

                                        logging.debug("Pushing task with TID to task queue: %s", task.tid)
                                        self._task_queue.push(task)

                                        self.ost_source_state_dict[source_ost] = OSTState.BLOCKED
                                        self.ost_target_state_dict[target_ost] = OSTState.BLOCKED

                                        break

                    while not self._result_queue.is_empty():

                        finished_tid = self._result_queue.pop()
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

                        logging.info("Elapsed time: %s - Number of OSTs: %i", elapsed_time, len(self.ost_fill_level_dict))

                        if logging.root.isEnabledFor(logging.DEBUG):

                            for ost, fill_level in self.ost_fill_level_dict.items():
                                logging.info("OST: %s - Fill Level: %i", ost, fill_level)

                        for ost in self.ost_source_state_dict:
                            self._update_ost_source_state_dict(ost)

                        for ost in self.ost_target_state_dict:
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
                                logging.info("OST: %s - Size: %i", source_ost, len(self.ost_cache_dict[source_ost]))
                        else:
                            logging.info("All OST caches empty")

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

            logging.error("Exception in %s (line: %i): %s", filename, exc_tb.tb_lineno, exc_value)
            logging.info("%s exited!", self._name)
            sys.exit(1)

        logging.info("%s finished!", self._name)
        sys.exit(0)

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

        logging.info("Count of processed input files: %i", file_counter)

    def _load_input_file(self, file_path):

        loaded_counter = 0
        skipped_counter = 0

        try:

            logging.debug("Loading input file: %s", file_path)

            with open(file_path, mode="r", errors="replace") as file_:

                # Test with file encoding="ascii" and content "ẞ"

                # TODO: Catch error lines and do not skip whole file.
                #       Probably use file descriptor directly instead...
                #       Also then remove errors="replace" in open.

                # while(cond)
                #     try:
                #         file_.readline()
                #     except UnicodeDecodeError as error

                for line in file_:

                    try:

                        stripped_line = line.strip()

                        if BaseMessage.field_separator in stripped_line:
                            logging.warning("Skipped line: %s", line)
                            skipped_counter += 1
                            continue

                        ost, filename = stripped_line.split()
                        migrate_item = LustreOstMigrateItem(ost, filename)

                        if ost not in self.ost_cache_dict:
                            self.ost_cache_dict[ost] = list()

                        self.ost_cache_dict[ost].append(migrate_item)

                        loaded_counter += 1

                    except ValueError as error:
                        logging.warning("Skipped line: %s (%s)", line, error)
                        skipped_counter += 1

        except Exception as error:
            logging.error("Aborted loading of input file %s:\n%s", file_path, error)

        logging.info("Input file: %s - Loaded: %i - Skipped: %i", file_path, loaded_counter, skipped_counter)

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

            for i in range(self.num_osts):

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
                raise RuntimeError("OST not found in ost_fill_level_dict: %s" % ost)

            if operator_func is operator.gt:
                ost_fill_level_threshold = self.ost_fill_level_threshold_source
            elif operator_func is operator.lt:
                ost_fill_level_threshold = self.ost_fill_level_threshold_target
            else:
                raise RuntimeError("operator_func is not supported: %s" % operator_func)

            ost_fill_level = self.ost_fill_level_dict[ost]

            if operator_func(ost_fill_level, ost_fill_level_threshold):

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
