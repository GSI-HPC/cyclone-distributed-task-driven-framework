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

import logging
import copy
import time
import sys
import os

from clush.RangeSet import RangeSet
from ctrl.critical_section import CriticalSection
from lfs.lfs_utils import LFSUtils
from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory
from task.generator.base_task_generator import BaseTaskGenerator


# TODO: Rename Class to LustreOSTMonitoringTaskGenerator
class LustreMonitoringTaskGenerator(BaseTaskGenerator):
    """Class for Lustre Monitoring Task Generator"""

    def __init__(self, task_queue, result_queue, config_file):

        super().__init__(task_queue, result_queue, config_file)

        self.task_file = self._config.get('task', 'task_file')
        self.task_name = self._config.get('task', 'task_name')

        self.lfs_bin = self._config.get('lustre', 'lfs_bin')
        self.target = self._config.get('lustre', 'target')

        ost_select_list = self._config.get('lustre', 'ost_select_list')

        if ost_select_list:
            self.ost_select_list = list(RangeSet(ost_select_list).striter())
        else:
            self.ost_select_list = list()

        self.local_mode = self._config.getboolean('control', 'local_mode')
        self.measure_interval = self._config.getfloat('control', 'measure_interval')

    # TODO: Create implement validate_config()
    def validate_config(self):
        pass

    def run(self):

        logging.info(f"{self._name} active!")

        while self._run_flag:

            try:

                ost_idx_list = None

                if self.local_mode:
                    ost_idx_list = self._create_local_ost_idx_list()
                else:
                    ost_idx_list = self._create_ost_idx_list()

                task_list = self._create_task_list(ost_idx_list)

                with CriticalSection(self._task_queue.lock):

                    if not self._task_queue.is_empty():
                        self._task_queue.clear()

                    if task_list:
                        self._task_queue.fill(task_list)

                # TODO: Check more frequently for the run condition, since the measure interval will let sleep
                #       this process before it becomes active again.
                time.sleep(self.measure_interval)

            except InterruptedError:
                logging.error("Caught InterruptedError exception.")

            except Exception as err:

                _, _, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

                logging.error(f"Exception in {filename} (line: {exc_tb.tb_lineno}): {err}")
                logging.info("LustreMonitoringTaskGenerator exited!")
                os._exit(1)

        logging.info("LustreMonitoringTaskGenerator finished!")
        os._exit(0)

    def _create_task_list(self, ost_idx_list):

        task_xml_info = TaskXmlReader.read_task_definition(self.task_file, self.task_name)

        logging.debug("Loaded task information from XML: %s.%s", task_xml_info.class_module, task_xml_info.class_name)

        task_skeleton = TaskFactory().create_from_xml_info(task_xml_info)

        task_list = list()

        logging.debug("Creating task list...")

        if logging.root.isEnabledFor(logging.DEBUG):

            if ost_idx_list:
                logging.debug("Length of OST index list: %i", len(ost_idx_list))
            else:
                logging.debug("Empty OST index list!")

        # Create tasks and set up runtime determined information
        # e.g. task ID and Lustre specific OST index
        for ost_idx in ost_idx_list:

            logging.debug("Create task for OST index: %s", ost_idx)

            task = copy.copy(task_skeleton)

            task.tid = ost_idx
            task.ost_idx = ost_idx

            task_list.append(task)

        return task_list

    def _create_ost_idx_list(self):

        ost_idx_list = list()

        lfs_utils = LFSUtils(self.lfs_bin)
        ost_item_list = lfs_utils.create_ost_item_list(self.target)

        for ost_item in ost_item_list:
            ost_idx_list.append(ost_item.ost_idx)

        if not ost_idx_list:
            raise RuntimeError("OST list is empty!")

        if self.ost_select_list:

            select_ost_idx_list = list()

            for select_ost_idx in self.ost_select_list:

                found_select_ost_idx = False

                for ost_idx in ost_idx_list:

                    if select_ost_idx == ost_idx:

                        select_ost_idx_list.append(ost_idx)

                        found_select_ost_idx = True

                        logging.debug("Found OST from selected list: %s", select_ost_idx)

                        break

                if found_select_ost_idx is False:
                    raise RuntimeError(f"OST to select was not found in ost_info_list: {select_ost_idx}")

            if not select_ost_idx_list:
                raise RuntimeError("Select OST info list is not allowed to be empty when selecting OSTs!")

            return select_ost_idx_list

        return ost_idx_list

    def _create_local_ost_idx_list(self):

        ost_idx_list = list()

        max_ost_idx = 100

        for ost_idx in range(max_ost_idx):
            ost_idx_list.append(str(ost_idx))

        if self.ost_select_list:

            select_ost_idx_list = list()

            for select_ost_idx in self.ost_select_list:

                found_select_ost_idx = False

                for ost_idx in ost_idx_list:

                    if select_ost_idx == ost_idx:

                        logging.debug("Found OST-IDX from selected list: %s", select_ost_idx)

                        if not found_select_ost_idx:
                            found_select_ost_idx = True

                        select_ost_idx_list.append(ost_idx)

                        break

                if not found_select_ost_idx:
                    raise RuntimeError(f"OST-IDX to select was not found in ost_info_list: {select_ost_idx}")

            return select_ost_idx_list

        return ost_idx_list
