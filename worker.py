#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti <g.iannetti@gsi.de>
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


import multiprocessing
import logging
import signal
import ctypes
import time
import abc


from ctrl.critical_section import CriticalSection


class WorkerState:

    __metaclass__ = abc.ABCMeta

    NOT_READY = 0
    READY     = 1
    EXECUTING = 2

    @classmethod
    def to_string(cls, state):

        if WorkerState.NOT_READY == state:
            return "NOT_READY"
        elif WorkerState.READY == state:
            return "READY"
        elif WorkerState.EXECUTING == state:
            return "EXECUTING"
        else:
            raise RuntimeError("Not supported worker state detected: %i" % state)


class WorkerStateTableItem:

    def __init__(self):

        # # RETURNS STDOUT: self._state = "TEXT" + str(NUMBER)
        # # RETURNS BAD VALUE: self._timestamp.value = 1234567890.99
        # self._state = multiprocessing.RawValue(ctypes.c_char_p)
        # self._ost_name = multiprocessing.RawValue(ctypes.c_char_p)
        # self._timestamp = multiprocessing.RawValue(ctypes.c_float)

        self._state = multiprocessing.RawValue(ctypes.c_int, WorkerState.NOT_READY)
        self._ost_name = multiprocessing.RawArray('c', 64)
        self._timestamp = multiprocessing.RawValue(ctypes.c_uint, 0)

    @property
    def get_state(self):
        return self._state.value

    @property
    def get_ost_name(self):
        return self._ost_name.value.decode()

    @property
    def get_timestamp(self):
        return self._timestamp.value

    def set_state(self, state):
        self._state.value = state

    def set_ost_name(self, task_name):
        self._ost_name.value = task_name.encode()

    def set_timestamp(self, timestamp):
        self._timestamp.value = timestamp


class Worker(multiprocessing.Process):

    def __init__(self,
                 name,
                 worker_state_table_item,
                 lock_worker_state_table,
                 task_queue,
                 result_queue, cond_result_queue):

        super(Worker, self).__init__()

        self.name = name

        self.worker_state_table_item = worker_state_table_item
        self.lock_worker_state_table = lock_worker_state_table

        self.task_queue = task_queue

        self.result_queue = result_queue
        self.cond_result_queue = cond_result_queue

        self.run_flag = False

    def start(self):

        self.run_flag = True

        super(Worker, self).start()

    def run(self):

        signal.signal(signal.SIGUSR1, self.signal_handler_shutdown)
        signal.siginterrupt(signal.SIGUSR1, True)

        logging.debug("Started Worker: '%s'" % multiprocessing.current_process().name)

        with CriticalSection(self.lock_worker_state_table):

            self.worker_state_table_item.set_state(WorkerState.READY)
            self.worker_state_table_item.set_timestamp(int(time.time()))

        while self.run_flag:

            task = self.task_queue.pop()

            with CriticalSection(self.lock_worker_state_table):

                self.worker_state_table_item.set_state(WorkerState.EXECUTING)
                self.worker_state_table_item.set_ost_name(task.ost_name)
                self.worker_state_table_item.set_timestamp(int(time.time()))

            task.execute()

            with CriticalSection(self.cond_result_queue):

                self.result_queue.push(task.ost_name)
                self.cond_result_queue.notify()

            with CriticalSection(self.lock_worker_state_table):

                self.worker_state_table_item.set_state(WorkerState.READY)
                self.worker_state_table_item.set_ost_name('')
                self.worker_state_table_item.set_timestamp(int(time.time()))

        logging.debug("Exiting worker: '%s'" % multiprocessing.current_process().name)

        exit(0)

    def signal_handler_shutdown(self, signal, frame):
        self.run_flag = False
