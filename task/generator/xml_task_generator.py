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

import logging
import signal
import copy
import time
import os

from multiprocessing import Process
from ctrl.critical_section import CriticalSection
from lfs.lfs_utils import LFSUtils
from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory


class XmlTaskGenerator(Process):

    def __init__(self,
                 ost_info_queue,
                 lock_ost_queue,
                 config_file_reader,
                 local_mode=False):

        super(XmlTaskGenerator, self).__init__()

        self.task_file = config_file_reader.task_def_file
        self.task_name = config_file_reader.task_name

        self.measure_interval = config_file_reader.measure_interval
        self.lfs_bin = config_file_reader.lfs_bin
        self.lfs_target = config_file_reader.lfs_target
        self.ost_select_list = config_file_reader.ost_select_list

        self.ost_info_queue = ost_info_queue
        self.lock_ost_queue = lock_ost_queue

        self.local_mode = local_mode

        self.run_flag = False

    def start(self):
        super(XmlTaskGenerator, self).start()

    def run(self):

        self.run_flag = True

        signal.signal(signal.SIGTERM, self._signal_handler_terminate)
        signal.siginterrupt(signal.SIGTERM, True)

        logging.info("XmlTaskGenerator started!")

        while self.run_flag:

            try:

                logging.debug("XmlTaskGenerator active!")

                ost_idx_list = None

                if self.local_mode:
                    ost_idx_list = self._create_local_ost_idx_list()
                else:
                    ost_idx_list = self._create_ost_idx_list()

                task_list = self._create_task_list(ost_idx_list)

                with CriticalSection(self.lock_ost_queue):

                    if not self.ost_info_queue.is_empty():
                        self.ost_info_queue.clear()

                    if task_list:
                        self.ost_info_queue.fill(task_list)

                time.sleep(self.measure_interval)

            except InterruptedError as e:
                logging.error("Caught InterruptedError exception.")

            except Exception as e:
                logging.error("Caught exception in XmlTaskGenerator: %s" % e)
                logging.info("XmlTaskGenerator exited!")
                os._exit(1)

        logging.info("XmlTaskGenerator finished!")
        os._exit(0)

    def _signal_handler_terminate(self, signum, frame):

        self.run_flag = False

        msg = "XmlTaskGenerator retrieved signal to terminate."
        logging.debug(msg)
        raise InterruptedError(msg)

    def _create_task_list(self, ost_idx_list):

        task_xml_info = TaskXmlReader.read_task_definition(self.task_file,
                                                           self.task_name)

        logging.debug("Loaded Task Information from XML: '%s.%s'" %
                      (task_xml_info.class_module, task_xml_info.class_name))

        task_skeleton = TaskFactory().create_from_xml_info(task_xml_info)

        task_list = list()

        logging.debug("Creating task list...")
        logging.debug("Length of OST index list: %s" % len(ost_idx_list))

        # Create tasks and set up runtime determined information
        # e.g. task ID and Lustre specific OST index
        for ost_idx in ost_idx_list:

            logging.debug("Create task for OST index: %s" % ost_idx)

            task = copy.copy(task_skeleton)

            task.tid = ost_idx
            task.ost_idx = ost_idx

            task_list.append(task)

        return task_list

    def _create_ost_idx_list(self):

        ost_idx_list = list()

        lfs_utils = LFSUtils(self.lfs_bin)
        ost_item_list = lfs_utils.create_ost_item_list(self.lfs_target)

        for ost_item in ost_item_list:
            ost_idx_list.append(ost_item.ost_idx)

        if len(ost_idx_list) == 0:
            raise RuntimeError("OST list is empty!")

        if len(self.ost_select_list):

            select_ost_idx_list = list()

            for select_ost_idx in self.ost_select_list:

                found_select_ost_idx = False

                for ost_idx in ost_idx_list:

                    if select_ost_idx == ost_idx:

                        select_ost_idx_list.append(ost_idx)

                        found_select_ost_idx = True

                        logging.debug("Found OST from selected list: %s" % select_ost_idx)

                        break

                if found_select_ost_idx is False:
                    raise RuntimeError("OST to select was not found in ost_info_list: %s" % select_ost_idx)

            if not len(select_ost_idx_list):
                raise RuntimeError("Select OST info list is not allowed to be empty when selecting OSTs!")

            return select_ost_idx_list

        else:
            return ost_idx_list

    def _create_local_ost_idx_list(self):

        ost_idx_list = list()

        max_ost_idx = 100

        for ost_idx in range(max_ost_idx):
            ost_idx_list.append(str(ost_idx))

        if len(self.ost_select_list):

            select_ost_idx_list = list()

            for select_ost_idx in self.ost_select_list:

                found_select_ost_idx = False

                for ost_idx in ost_idx_list:

                    if select_ost_idx == ost_idx:

                        logging.debug("Found OST-IDX from selected list: %s" %
                                      select_ost_idx)

                        if not found_select_ost_idx:
                            found_select_ost_idx = True

                        select_ost_idx_list.append(ost_idx)

                        break

                if not found_select_ost_idx:
                    raise RuntimeError("OST-IDX to select was not found "
                                       "in ost_info_list: %s" % select_ost_idx)

            return select_ost_idx_list

        else:
            return ost_idx_list

