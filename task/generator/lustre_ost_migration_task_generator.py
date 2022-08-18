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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""Module for task generator"""

from datetime import datetime
from enum import Enum, unique
import operator
import logging
import random
import copy
import time
import sys
import re
import os
from typing import Dict

from clush.RangeSet import RangeSet

from conf.config_value_error import ConfigValueError, ConfigValueOutOfRangeError
from lfs.lfs_utils import LfsUtils
from msg.base_message import BaseMessage
from ctrl.shared_queue import SharedQueue
from ctrl.shared_queue_str import SharedQueueStr
from task.generator.base_task_generator import BaseTaskGenerator
from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory

class LustreOstMigrateItem:

    def __init__(self, ost: int, filename: str) -> None:

        self.ost = ost
        self.filename = filename

@unique
class OSTState(Enum):

    READY        = 1
    LOCKED       = 2
    BLOCKED      = 3
    PENDING_LOCK = 4

class LustreOstMigrationTaskGenerator(BaseTaskGenerator):
    """Class for LustreOSTMigrationTaskGenerator"""

    MIN_THRESHOLD_SEC = 1
    MAX_THRESHOLD_SEC = 3600

    MIN_OST_FILL_THRESHOLD_SOURCE = 0
    MIN_OST_FILL_THRESHOLD_TARGET = 0
    MAX_OST_FILL_THRESHOLD        = 90

    def __init__(self, task_queue: SharedQueue, result_queue: SharedQueueStr, config_file: str) -> None:

        super().__init__(task_queue, result_queue, config_file)

        self.local_mode = self._config.getboolean('control', 'local_mode')

        if self.local_mode:
            self.num_osts = self._config.getint('control.local_mode', 'num_osts')
        else:
            self.lfs_utils = LfsUtils()

        self.threshold_update_fill_level = self._config.getint('control.threshold', 'update_fill_level')
        self.threshold_reload_files = self._config.getint('control.threshold', 'reload_files')
        self.threshold_print_caches = self._config.getint('control.threshold', 'print_caches')

        self.task_file = self._config.get('task', 'task_file')
        self.task_name = self._config.get('task', 'task_name')

        self.input_dir = self._config.get('migration', 'input_dir')

        self.ost_fill_level_threshold_source = self._config.getint('migration', 'ost_fill_level_threshold_source')
        self.ost_fill_level_threshold_target = self._config.getint('migration', 'ost_fill_level_threshold_target')

        ost_targets = self._config.get('migration', 'ost_targets')

        self.ost_target_list = []

        for ost_target in RangeSet(ost_targets).striter():
            self.ost_target_list.append(int(ost_target))

        self.lfs_path = self._config.get('lustre', 'fs_path')

        self._regex = rf"^(\d+) ({self.lfs_path}.*)$"
        self.pattern = re.compile(self._regex)

        self.ost_cache_dict        = {}
        self.ost_source_state_dict = {}
        self.ost_target_state_dict = {}
        self.ost_fill_level_dict   = {}
        self.source_ost_key_list   = []

    def validate_config(self) -> None:

        if self.local_mode:

            if not LfsUtils.MIN_OST_INDEX < self.num_osts <= LfsUtils.MAX_OST_INDEX:
                raise ConfigValueOutOfRangeError("num_osts", LfsUtils.MIN_OST_INDEX, LfsUtils.MAX_OST_INDEX)

        else:
            if not os.path.isdir(self.lfs_path):
                raise ConfigValueError(f"lfs_path does not point to a directory: {self.lfs_path}")

        if not self.MIN_THRESHOLD_SEC <= self.threshold_update_fill_level <= self.MAX_THRESHOLD_SEC:
            raise ConfigValueOutOfRangeError("update_fill_level", self.MIN_THRESHOLD_SEC, self.MAX_THRESHOLD_SEC)

        if not self.MIN_THRESHOLD_SEC <= self.threshold_reload_files <= self.MAX_THRESHOLD_SEC:
            raise ConfigValueOutOfRangeError("reload_files", self.MIN_THRESHOLD_SEC, self.MAX_THRESHOLD_SEC)

        if not self.MIN_THRESHOLD_SEC <= self.threshold_print_caches <= self.MAX_THRESHOLD_SEC:
            raise ConfigValueOutOfRangeError("print_caches", self.MIN_THRESHOLD_SEC, self.MAX_THRESHOLD_SEC)

        if not os.path.isdir(self.input_dir):
            raise ConfigValueError(f"input_dir does not point to a directory: {self.input_dir}")

        if not self.MIN_OST_FILL_THRESHOLD_SOURCE <= self.ost_fill_level_threshold_source <= self.MAX_OST_FILL_THRESHOLD:
            raise ConfigValueOutOfRangeError("ost_fill_level_threshold_source",
                                             self.MIN_OST_FILL_THRESHOLD_SOURCE,
                                             self.MAX_OST_FILL_THRESHOLD)

        if not self.MIN_OST_FILL_THRESHOLD_TARGET <= self.ost_fill_level_threshold_target <= self.MAX_OST_FILL_THRESHOLD:
            raise ConfigValueOutOfRangeError("ost_fill_level_threshold_target",
                                             self.MIN_OST_FILL_THRESHOLD_TARGET,
                                             self.MAX_OST_FILL_THRESHOLD)

        if not LfsUtils.MIN_OST_INDEX <= int(self.ost_target_list[0]) <= LfsUtils.MAX_OST_INDEX:
            raise ConfigValueOutOfRangeError("min(ost_targets)", LfsUtils.MIN_OST_INDEX, LfsUtils.MAX_OST_INDEX)

        if len(self.ost_target_list) > 1 and \
            not LfsUtils.MIN_OST_INDEX <= int(self.ost_target_list[-1]) <= LfsUtils.MAX_OST_INDEX:
            raise ConfigValueOutOfRangeError("max(ost_targets)", LfsUtils.MIN_OST_INDEX, LfsUtils.MAX_OST_INDEX)

    def run(self) -> None:

        logging.info("%s active!", self._name)

        try:

            task_xml_info = TaskXmlReader.read_task_definition(self.task_file, self.task_name)

            logging.debug("Loaded task information from XML: %s.%s",
                           task_xml_info.class_module, task_xml_info.class_name)

            task_skeleton = TaskFactory().create_from_xml_info(task_xml_info)

            self._update_ost_fill_level_dict()
            self._init_ost_target_state_dict()
            self._process_input_files()

            next_time_update_fill_level = int(time.time()) + self.threshold_update_fill_level
            next_time_reload_files = int(time.time()) + self.threshold_reload_files
            next_time_print_caches = int(time.time()) + self.threshold_print_caches

            # CAUTION: If target ost list changes, this must be recognized.
            target_ost_key_list = list(self.ost_target_state_dict)
            len_target_ost_key_list = len(target_ost_key_list)

            next_target_ost_key_index = 0
            next_source_ost_key_index = 0

            while self._run_flag:

                try:

                    counter_checked_target_osts = 0

                    if next_source_ost_key_index >= len(self.source_ost_key_list):
                        next_source_ost_key_index = 0

                    while next_source_ost_key_index < len(self.source_ost_key_list):

                        if counter_checked_target_osts == len_target_ost_key_list:
                            break

                        source_ost = self.source_ost_key_list[next_source_ost_key_index]
                        next_source_ost_key_index += 1

                        if self.ost_source_state_dict[source_ost] == OSTState.READY:

                            ost_cache = self.ost_cache_dict[source_ost]

                            if ost_cache:

                                while next_target_ost_key_index < len_target_ost_key_list:

                                    target_ost = target_ost_key_list[next_target_ost_key_index]
                                    next_target_ost_key_index +=1
                                    counter_checked_target_osts += 1

                                    target_state = self.ost_target_state_dict[target_ost]

                                    if target_state == OSTState.READY:

                                        item = ost_cache.pop()

                                        task = copy.copy(task_skeleton)
                                        task.tid = f"{source_ost}:{target_ost}"

                                        # Could provice an interface for initialization of different migrate tasks
                                        # e.g. task.initialize(...)
                                        if not self.local_mode:

                                            task.source_ost = source_ost
                                            task.target_ost = target_ost
                                            task.filename = item.filename

                                        logging.debug("Pushing task with TID to task queue: %s", task.tid)
                                        self._task_queue.push(task)

                                        self.ost_source_state_dict[source_ost] = OSTState.BLOCKED
                                        self.ost_target_state_dict[target_ost] = OSTState.BLOCKED

                                        break

                                if next_target_ost_key_index == len_target_ost_key_list:
                                    next_target_ost_key_index = 0

                    while not self._result_queue.is_empty():

                        finished_tid = self._result_queue.pop()
                        logging.debug("Popped TID from result queue: %s", finished_tid)

                        split_result = finished_tid.split(":")
                        source_ost = int(split_result[0])
                        target_ost = int(split_result[1])

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
                                logging.info("OST: %i - Fill Level: %i", ost, fill_level)

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

                    if self.ost_cache_dict:
                        self._interruptable_sleep.sleep(0.001)
                    else:
                        self._interruptable_sleep.sleep(1)

                except InterruptedError:
                    logging.error("Caught InterruptedError exception.")

        except Exception:
            logging.exception("Caught exception in %s", self._name)
            logging.info("%s exited!", self._name)
            sys.exit(1)

        logging.info("%s finished!", self._name)
        sys.exit(0)

    def _process_input_files(self) -> None:

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

    def _load_input_file(self, file_path: str) -> None:

        loaded_counter = 0
        error_counter = 0

        try:

            logging.debug("Loading input file: %s", file_path)

            with open(file_path, mode="rb") as reader:

                for raw_line in reader:

                    try:

                        if not raw_line:
                            continue

                        line = raw_line.decode(errors='strict')

                        if BaseMessage.field_separator in line:
                            raise RuntimeError('File separator found')

                        match = self.pattern.search(line)

                        if not match:
                            raise RuntimeError(f"Regex '{self._regex}' did not match")

                        ost      = int(match.group(1))
                        filename = match.group(2)

                        migrate_item = LustreOstMigrateItem(ost, filename)

                        if ost not in self.ost_cache_dict:
                            self.ost_cache_dict[ost] = []

                        self.ost_cache_dict[ost].append(migrate_item)

                        loaded_counter += 1

                    except UnicodeDecodeError:
                        line = raw_line.decode(errors='replace')
                        logging.error("Decoding failed for line: %s", line)
                        error_counter += 1
                        continue

                    except RuntimeError as error:
                        logging.error("Failed line - %s: %s", error, line)
                        error_counter += 1

        except Exception as error:
            logging.error("Aborted loading of input file %s:\n%s", file_path, error)

        logging.info("Input file: %s - Loaded: %i - Failed: %i", file_path, loaded_counter, error_counter)

    def _allocate_ost_caches(self) -> None:

        for ost, cache in self.ost_cache_dict.items():

            if cache:
                if ost not in self.ost_source_state_dict:
                    self._update_ost_source_state_dict(ost)

        self.source_ost_key_list = list(self.ost_source_state_dict)

    def _deallocate_empty_ost_caches(self) -> None:

        empty_ost_cache_ids = None

        for ost, cache in self.ost_cache_dict.items():

            if len(cache) == 0:

                if self.ost_source_state_dict[ost] == OSTState.READY \
                        or self.ost_source_state_dict[ost] == OSTState.LOCKED:

                    if not empty_ost_cache_ids:
                        empty_ost_cache_ids = []

                    empty_ost_cache_ids.append(ost)

        if empty_ost_cache_ids:

            for ost in empty_ost_cache_ids:

                del self.ost_cache_dict[ost]
                del self.ost_source_state_dict[ost]

        self.source_ost_key_list = list(self.ost_source_state_dict)

    def _init_ost_target_state_dict(self) -> None:

        for ost in self.ost_target_list:
            self._update_ost_target_state_dict(ost)

    def _update_ost_fill_level_dict(self) -> None:

        if self.local_mode:

            self.ost_fill_level_dict.clear()

            for ost_idx in range(self.num_osts):
                fill_level = random.randint(40, 60)

                self.ost_fill_level_dict[ost_idx] = fill_level

        else:
            self.ost_fill_level_dict = self.lfs_utils.retrieve_ost_disk_usage(self.lfs_path)

    def _update_ost_source_state_dict(self, ost: int) -> None:
        self._update_ost_state_dict(ost, self.ost_source_state_dict, operator.gt)

    def _update_ost_target_state_dict(self, ost: int) -> None:
        self._update_ost_state_dict(ost, self.ost_target_state_dict, operator.lt)

    def _update_ost_state_dict(self, ost: int, ost_state_dict: Dict[int, int], operator_func = None) -> None:

        if operator_func:

            if ost not in self.ost_fill_level_dict:
                raise RuntimeError(f"OST not found in ost_fill_level_dict: {ost}")

            if operator_func is operator.gt:
                ost_fill_level_threshold = self.ost_fill_level_threshold_source
            elif operator_func is operator.lt:
                ost_fill_level_threshold = self.ost_fill_level_threshold_target
            else:
                raise RuntimeError(f"operator_func is not supported: {operator_func}")

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
