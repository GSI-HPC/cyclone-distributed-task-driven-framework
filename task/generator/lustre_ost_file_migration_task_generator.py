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
import random
import signal
import time
import os

from multiprocessing import Process

from ctrl.critical_section import CriticalSection
from task.ost_migrate_task import OstMigrateTask


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

        ost_migrate_item_list = LustreOstFileMigrationTaskGenerator.create_ost_migrate_item_list()
        print(ost_migrate_item_list)

        # Do not forget to clear the OST cache/free dict for each initialization run
        self.ost_cache_dict.clear()
        self.ost_source_free_dict.clear()

        # Set up OST caches
        for ost_migrate_item in ost_migrate_item_list:

            if ost_migrate_item.ost not in self.ost_cache_dict:
                self.ost_cache_dict[ost_migrate_item.ost] = list()

            self.ost_cache_dict[ost_migrate_item.ost].append(ost_migrate_item)

        # Initialize OST source free dict depending on the keys from ost_cache_dict
        for key in self.ost_cache_dict.keys():
            self.ost_source_free_dict[key] = True

        while self.run_flag:

            try:

                logging.debug(f"{self.__class__.__name__} active!")

                for ost_idx, ost_cache in self.ost_cache_dict.items():

                    ost_cache = self.ost_cache_dict[ost_idx]

                    print(f"ost-cache: {ost_idx} - len(ost_cache): {len(ost_cache)}")

                    if len(ost_cache):

                        if self.ost_source_free_dict[ost_idx]:

                            print("free slot for source ost: %s" % ost_idx)

                            for target_ost, free in self.ost_target_free_dict.items():

                                if free:

                                    print("found free target ost: %s" % target_ost)

                                    # TODO: create compose tid func
                                    # build task id (tid)
                                    tid = f"{ost_idx}:{target_ost}"

                                    print("tid: %s" % tid)

                                    # TODO: create migrate task...
                                    item = ost_cache.pop()

                                    # create task
                                    task = OstMigrateTask(ost_idx, target_ost, item.filename)
                                    task.tid = tid

                                    logging.debug(f"Pushing task with TID to task queue: {task.tid}")
                                    print(f"Pushing task with TID to task queue: {task.tid}")

                                    with CriticalSection(self.lock_task_queue):
                                        self.task_queue.push(task)

                                    # update ost_source_dict
                                    self.ost_source_free_dict[ost_idx] = False

                                    # update ost_target_dict
                                    self.ost_target_free_dict[target_ost] = False

                                    # TODO: Do target search separately with
                                    #       additional Lustre information
                                    break
                        else:
                            logging.debug("no free slot...")

                    else:
                        logging.debug("cache for OST is empty: %s" % ost_idx)

                # Testing purpose...
                logging.debug("sleeping 1 *******")
                time.sleep(1)

                while not self.result_queue.is_empty():

                    with CriticalSection(self.lock_result_queue):

                        finished_tid = self.result_queue.pop()

                        logging.debug(f"Popped TID from result queue: {finished_tid}")

                        # TODO: create decompose tid func + add error handling
                        source_ost, target_ost = finished_tid.split(":")

                        # update ost_source_dict
                        self.ost_source_free_dict[source_ost] = True

                        # update ost_target_dict
                        self.ost_target_free_dict[target_ost] = True

                # Testing purpose...
                logging.debug("sleeping 2 *******")
                time.sleep(1)

            except InterruptedError as e:
                logging.error("Caught InterruptedError exception.")

            except Exception as e:
                logging.error(f"Caught exception in {self.__class__.__name__}: {e}")
                logging.info(f"{self.__class__.__name__} exited!")
                os._exit(1)

        logging.info(f"{self.__class__.__name__} finished!")
        os._exit(0)

    def _signal_handler_terminate(self, signum, frame):

        self.run_flag = False

        msg = f"{self.__class__.__name__} retrieved signal to terminate."
        logging.debug(msg)
        raise InterruptedError(msg)

    @staticmethod
    def create_ost_migrate_item_list():

        l = list()

        for i in range(10):
            l.append(LustreOstFileMigrationTaskGenerator.create_ost_migrate_item())

        return l

    @staticmethod
    def create_ost_migrate_item():

        ost = str(random.randint(0, 3))

        filename = "/home/xxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/" \
            "34343543354353543535353543/343434343664654646456464436/file.tmp/"

        return LustreOstMigrateItem(ost, filename)
