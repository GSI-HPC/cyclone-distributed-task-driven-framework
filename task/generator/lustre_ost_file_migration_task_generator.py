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
import random
import time
import sys
import os

from datetime import datetime
from enum import Enum, unique
from multiprocessing import Process

from ctrl.critical_section import CriticalSection
from globals import LOCAL_MODE
from lfs.lfs_utils import LFSUtils
from msg.base_message import BaseMessage
from task.ost_migrate_task import OstMigrateTask
from task.empty_task import EmptyTask


class LustreOstMigrateItem:

    def __init__(self, ost, filename):

        self.ost = ost
        self.filename = filename


@unique
class OSTCacheState(Enum):

    BLOCKED = 1
    LOCKED = 2
    READY = 3


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

        if not LOCAL_MODE:
            self.lfs_utils = LFSUtils("/usr/bin/lfs")
            self.lfs_path = config.get('lustre', 'fs_path')

        ost_targets = config.get('lustre.migration', 'ost_targets')
        self.ost_target_list = ost_targets.strip().split(",")

        self.input_dir = config.get('lustre.migration', 'input_dir')

        self.ost_fill_threshold = config.getint('lustre.migration', 'ost_fill_threshold')

        self.ost_source_cache_dict = dict()

        # TODO: Create class for managing state and capacity for OSTs.
        self.ost_source_state_dict = dict()
        self.ost_target_state_dict = dict()

        self.ost_fill_level_dict = dict()

        self.run_flag = False

    def start(self):
        super(LustreOstFileMigrationTaskGenerator, self).start()

    def run(self):

        try:

            self.run_flag = True

            signal.signal(signal.SIGTERM, self._signal_handler_terminate)
            signal.siginterrupt(signal.SIGTERM, True)

            logging.info("%s started!" % self.__class__.__name__)

            self._process_input_files()
            self._update_ost_fill_level_dict()
            self._reallocate_ost_source_caches()

            self._init_ost_target_cache_state_dict()

            threshold_print_caches = 5
            next_time_print_caches = int(time.time()) + threshold_print_caches

            threshold_reload_files = 45
            next_time_reload_files = int(time.time()) + threshold_reload_files

            threshold_update_fill_level = 30
            next_time_update_fill_level = int(time.time()) + threshold_update_fill_level

            while self.run_flag:

                try:

                    for source_ost, ost_cache in self.ost_source_cache_dict.items():

                        if self.ost_source_state_dict[source_ost] == OSTCacheState.READY:

                            if len(ost_cache):

                                for target_ost, target_state in self.ost_target_state_dict.items():

                                    if target_state == OSTCacheState.READY:

                                        item = ost_cache.pop()

                                        if LOCAL_MODE:
                                            task = EmptyTask()
                                        else:
                                            task = OstMigrateTask(source_ost, target_ost, item.filename)

                                        task.tid = f"{source_ost}:{target_ost}"

                                        logging.debug("Pushing task with TID to task queue: %s" % task.tid)

                                        with CriticalSection(self.lock_task_queue):
                                            self.task_queue.push(task)

                                        self.ost_source_state_dict[source_ost] = OSTCacheState.BLOCKED
                                        self.ost_target_state_dict[target_ost] = OSTCacheState.BLOCKED

                                        break

                    while not self.result_queue.is_empty():

                        with CriticalSection(self.lock_result_queue):

                            finished_tid = self.result_queue.pop()

                            logging.debug("Popped TID from result queue: %s " % finished_tid)

                            source_ost, target_ost = finished_tid.split(":")

                            if self.ost_source_state_dict[source_ost] == OSTCacheState.BLOCKED:
                                self.ost_source_state_dict[source_ost] = OSTCacheState.READY

                            if self.ost_target_state_dict[target_ost] == OSTCacheState.BLOCKED:
                                self.ost_target_state_dict[target_ost] = OSTCacheState.READY

                    last_run_time = int(time.time())

                    if last_run_time >= next_time_reload_files:

                        next_time_reload_files = last_run_time + threshold_reload_files

                        # TODO: just print if input files were loaded.
                        logging.info("###### Loading Input Files ######")

                        self._process_input_files()
                        self._reallocate_ost_source_caches()

                    if last_run_time >= next_time_print_caches:

                        next_time_print_caches = last_run_time + threshold_print_caches

                        logging.info("###### OST Cache Sizes ######")

                        for source_ost in sorted(self.ost_source_cache_dict.keys()):
                            logging.info("OST: %s - Size: %s"
                                         % (source_ost, len(self.ost_source_cache_dict[source_ost])))

                    if last_run_time >= next_time_update_fill_level:

                        next_time_update_fill_level = last_run_time + threshold_update_fill_level

                        logging.info("###### OST Fill Level Update ######")

                        start_time = datetime.now()
                        self._update_ost_fill_level_dict()
                        elapsed_time = datetime.now() - start_time

                        logging.info("Elapsed time: %s - Number of OSTs: %s"
                                     % (elapsed_time, len(self.ost_fill_level_dict)))

                        if logging.root.level <= logging.DEBUG:

                            for ost, fill_level in self.ost_fill_level_dict.items():
                                logging.debug("OST: %s - Fill Level: %s" % (ost, fill_level))

                    # TODO: adaptive sleep... ???
                    ##time.sleep(0.001)
                    time.sleep(1.001)

                except InterruptedError as e:
                    logging.error("Caught InterruptedError exception.")

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error("Exception in %s (line: %s): %s" % (filename, exc_tb.tb_lineno, e))
            logging.info("%s exited!" % self.__class__.__name__)
            os._exit(1)

        logging.info("%s finished!" % self.__class__.__name__)
        os._exit(0)

    def _signal_handler_terminate(self, signum, frame):

        self.run_flag = False

        msg = f"{self.__class__.__name__} retrieved signal to terminate."
        logging.debug(msg)
        raise InterruptedError(msg)

    def _process_input_files(self):

        files = os.listdir(self.input_dir)

        for f in files:

            if f.endswith(".input"):

                file_path = self.input_dir + os.path.sep + f

                self._load_input_file(file_path)

                os.renames(file_path, file_path + ".done")

    def _load_input_file(self, input_file):

        with open(input_file, mode="r", encoding="UTF-8") as file:

            loaded_counter = 0
            skipped_counter = 0

            for line in file:

                try:

                    stripped_line = line.strip()

                    if BaseMessage.field_separator in stripped_line:
                        logging.warning("Skipped line: %s" % line)
                        skipped_counter += 1
                        continue

                    ost, filename = stripped_line.split()

                    migrate_item = LustreOstMigrateItem(ost, filename)

                    if ost not in self.ost_source_cache_dict:
                        self.ost_source_cache_dict[ost] = list()

                    self.ost_source_cache_dict[ost].append(migrate_item)
                    loaded_counter += 1

                except Exception as e:

                    logging.warning("Skipped line: %s" % line)
                    skipped_counter += 1

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.error("Exception in %s (line: %s): %s" % (filename, exc_tb.tb_lineno, e))

            logging.info("Loaded input file: %s - Loaded: %s - Skipped: %s"
                         % (input_file, loaded_counter, skipped_counter))

    def _reallocate_ost_source_caches(self):

        # Iterate over copy of the keys to prevent:
        # "RuntimeError: dictionary changed size during iteration"
        keys_copy_list = list(self.ost_source_cache_dict.keys())

        for ost in keys_copy_list:

            ost_cache = self.ost_source_cache_dict[ost]

            if len(ost_cache):

                if ost in self.ost_source_state_dict:
                    pass
                else:
                    # Add new source OST to ost_source_free_dict.
                    self._update_ost_source_cache_state(ost)
            else:

                # Do not delete OST source data structure that is still in use.
                if self.ost_source_state_dict[ost] != OSTCacheState.BLOCKED:

                    del self.ost_source_state_dict[ost]
                    del self.ost_source_cache_dict[ost]

    def _init_ost_target_cache_state_dict(self):

        for ost in self.ost_target_list:
            self._update_ost_target_cache_state(ost)

    def _update_ost_fill_level_dict(self):

        if LOCAL_MODE:

            self.ost_fill_level_dict.clear()

            for i in range(10):

                ost_idx = str(i)
                fill_level = random.randint(40, 60)

                self.ost_fill_level_dict[ost_idx] = fill_level

        else:
            self.ost_fill_level_dict = \
                self.lfs_utils.retrieve_ost_fill_level(self.lustre_fs_path)

    def _update_ost_source_cache_state(self, ost):

        if ost in self.ost_fill_level_dict:

            fill_level = self.ost_fill_level_dict[ost]

            if fill_level > self.ost_fill_threshold:

                if ost in self.ost_source_state_dict:

                    if self.ost_source_state_dict[ost] == OSTCacheState.LOCKED:
                        self.ost_source_state_dict[ost] = OSTCacheState.READY

                else:
                    self.ost_source_state_dict[ost] = OSTCacheState.READY

            else:
                self.ost_source_state_dict[ost] = OSTCacheState.LOCKED

        else:
            raise RuntimeError("OST not found in ost_fill_level_dict: %s" % ost)

    def _update_ost_target_cache_state(self, ost):

        if ost in self.ost_fill_level_dict:

            fill_level = self.ost_fill_level_dict[ost]

            if fill_level < self.ost_fill_threshold:

                if ost in self.ost_target_state_dict:

                    if self.ost_target_state_dict[ost] == OSTCacheState.LOCKED:
                        self.ost_target_state_dict[ost] = OSTCacheState.READY

                else:
                    self.ost_target_state_dict[ost] = OSTCacheState.READY

            else:
                self.ost_target_state_dict[ost] = OSTCacheState.LOCKED

        else:
            raise RuntimeError("OST not found in ost_fill_level_dict: %s" % ost)

