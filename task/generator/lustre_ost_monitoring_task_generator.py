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
import os

from clush.RangeSet import RangeSet
from ctrl.critical_section import CriticalSection
from ctrl.shared_queue import SharedQueue
from lfs.lfs_utils import LfsUtils
from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory
from task.generator.base_task_generator import BaseTaskGenerator


class LustreOstMonitoringTaskGenerator(BaseTaskGenerator):
    """Class for Lustre Monitoring Task Generator"""

    def __init__(self, task_queue: SharedQueue, result_queue: SharedQueue, config_file: str) -> None:

        super().__init__(task_queue, result_queue, config_file)

        self.local_mode = self._config.getboolean('control', 'local_mode')
        self.measure_interval = self._config.getfloat('control', 'measure_interval')

        self.task_file = self._config.get('task', 'task_file')
        self.task_name = self._config.get('task', 'task_name')

        self.lfs_bin = self._config.get('lustre', 'lfs_bin')
        self.target = self._config.get('lustre', 'target')

        self.ost_select_list = []

        ost_select_list = self._config.get('lustre', 'ost_select_list')

        if ost_select_list:
            self.ost_select_list.extend([int(i) for i in list(RangeSet(ost_select_list).striter())])

    # TODO: Create implement validate_config()
    def validate_config(self) -> None:
        pass

    def run(self) -> None:

        logging.info(f"{self._name} active!")

        while self._run_flag:

            try:

                ost_idx_list = None

                if self.local_mode:
                    ost_idx_list = __class__.build_index_list(self.ost_select_list, list(range(0, 100)))
                else:
                    ost_avail_list = LfsUtils(self.lfs_bin).retrieve_component_states()[self.target].osts.keys()
                    ost_idx_list = __class__.build_index_list(self.ost_select_list, ost_avail_list)

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

            except Exception:
                logging.exception("Caught exception in %s", self._name)
                logging.info("%s exited!", self._name)
                os._exit(1)

        logging.info("%s finished!", self._name)
        os._exit(0)

    def _create_task_list(self, ost_idx_list: list) -> None:

        task_xml_info = TaskXmlReader.read_task_definition(self.task_file, self.task_name)

        logging.debug("Loaded task information from XML: %s.%s", task_xml_info.class_module, task_xml_info.class_name)

        task_skeleton = TaskFactory().create_from_xml_info(task_xml_info)

        task_list = []

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

    @staticmethod
    def build_index_list(selected_indexes: list, available_indexes: list) -> list:

        len_selected_indexes  = len(selected_indexes)
        len_available_indexes = len(available_indexes)

        if not len_available_indexes:
            raise RuntimeError('Available indexes list is empty')

        if not len_selected_indexes:
            return available_indexes

        if len_selected_indexes > len_available_indexes:
            raise RuntimeError('Selected indexes list is not allowed to be greater than available indexes list')

        built_index_list = []

        for selected_idx in selected_indexes:

            if selected_idx in available_indexes:
                built_index_list.append(selected_idx)
            else:
                raise RuntimeError(f"Selected index {selected_idx} not found in available indexes list")

        if not built_index_list:
            raise RuntimeError("Built indexes list is not allowed to be empty when selecting indexes")

        return built_index_list
