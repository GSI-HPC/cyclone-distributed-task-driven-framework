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
import copy
import os

from ClusterShell.RangeSet import RangeSet
from lfsutils.lib import LfsUtils

from ctrl.critical_section import CriticalSection
from ctrl.shared_queue import SharedQueue
from ctrl.shared_queue_str import SharedQueueStr
from task.base_task import BaseTask
from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory
from task.generator.base_task_generator import BaseTaskGenerator
from util.interruptable_sleep import InterruptableSleep

class LustreOstMonitoringTaskGenerator(BaseTaskGenerator):
    """Class for Lustre Monitoring Task Generator"""

    def __init__(self, task_queue: SharedQueue, result_queue: SharedQueueStr, config_file: str) -> None:

        super().__init__(task_queue, result_queue, config_file)

        self.local_mode = self._config.getboolean('control', 'local_mode')
        self.measure_interval = self._config.getint('control', 'measure_interval')

        self.task_file = self._config.get('task', 'task_file')
        self.task_name = self._config.get('task', 'task_name')

        self.lfs_bin = self._config.get('lustre', 'lfs_bin')
        self.target = self._config.get('lustre', 'target')

        self.ost_select_set = set[int]()

        ost_select_list : str = self._config.get('lustre', 'ost_select_list')

        if ost_select_list:
            self.ost_select_set.update([int(i) for i in set(RangeSet(ost_select_list).striter())])

        self._interruptable_sleep = InterruptableSleep()

    def validate_config(self) -> None:
        pass

    def run(self) -> None:

        logging.info(f"{self._name} active!")

        while self._run_flag:

            try:

                ost_idx_set : set[int]

                if self.local_mode:
                    ost_idx_set = LustreOstMonitoringTaskGenerator.build_index_set(self.ost_select_set, set(range(0, 100)))
                else:
                    ost_avail_set = set[int](LfsUtils(self.lfs_bin).retrieve_component_states()[self.target].osts.keys())
                    ost_idx_set   = LustreOstMonitoringTaskGenerator.build_index_set(self.ost_select_set, ost_avail_set)

                task_list = self._create_task_list(ost_idx_set)

                with CriticalSection(self._task_queue.lock):

                    if not self._task_queue.is_empty():
                        self._task_queue.clear()

                    if task_list:
                        self._task_queue.fill(task_list)

                self._interruptable_sleep.sleep(self.measure_interval)

            except InterruptedError:
                logging.error('Caught InterruptedError exception')

            except Exception:
                logging.exception("Caught exception in %s", self._name)
                logging.info("%s exited!", self._name)
                os._exit(1)

        logging.info("%s finished!", self._name)
        os._exit(0)

    def _create_task_list(self, ost_idx_set: set[int]) -> list[BaseTask]:

        task_xml_info = TaskXmlReader.read_task_definition(self.task_file, self.task_name)

        logging.debug("Loaded task information from XML: %s.%s", task_xml_info.class_module, task_xml_info.class_name)

        task_skeleton = TaskFactory().create_from_xml_info(task_xml_info)

        task_list = list[BaseTask]()

        logging.debug("Creating task list...")

        if logging.root.isEnabledFor(logging.DEBUG):

            if ost_idx_set:
                logging.debug("Length of OST index list: %i", len(ost_idx_set))
            else:
                logging.debug("Empty OST index list!")

        # Create tasks and set up runtime determined information
        # e.g. task ID and Lustre specific OST index
        for ost_idx in ost_idx_set:

            logging.debug("Create task for OST index: %s", ost_idx)

            task = copy.copy(task_skeleton)

            task.tid     = ost_idx
            task.ost_idx = ost_idx

            task_list.append(task)

        return task_list

    @staticmethod
    def build_index_set(selected_indexes: set[int], available_indexes: set[int]) -> set[int]:

        len_selected_indexes  = len(selected_indexes)
        len_available_indexes = len(available_indexes)

        if not len_available_indexes:
            raise RuntimeError('Available indexes set is empty')

        if not len_selected_indexes:
            return available_indexes

        if len_selected_indexes > len_available_indexes:
            raise RuntimeError('Selected indexes set is not allowed to be greater than available indexes set')

        built_index_set = set[int]()

        for selected_idx in selected_indexes:

            if selected_idx in available_indexes:
                built_index_set.add(selected_idx)
            else:
                raise RuntimeError(f"Selected index {selected_idx} not found in available indexes set")

        if not built_index_set:
            raise RuntimeError("Built indexes set is not allowed to be empty when selecting indexes")

        return built_index_set
