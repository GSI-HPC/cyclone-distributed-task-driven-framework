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


import argparse
import logging
import os
import sys
import time
import multiprocessing
import ctypes
import abc

from comm.controller_handler import ControllerCommHandler
from conf.controller_config_file_reader import ControllerConfigFileReader
from ctrl.pid_control import PIDControl
from ctrl.critical_section import CriticalSection
from ctrl.shared_queue import SharedQueue
from msg.message_factory import MessageFactory
from msg.message_type import MessageType
from msg.task_finished import TaskFinished
from msg.task_request import TaskRequest
from msg.ost_task_response import OstTaskResponse
from task.ost_task import OSTTask


class WorkerState:

    __metaclass__ = abc.ABCMeta

    NOT_READY = 0
    READY = 1
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


def init_arg_parser():

    parser = argparse.ArgumentParser(description='Lustre OST Performance Testing Controller Process.')

    parser.add_argument('-f', '--config-file', dest='config_file', type=str, required=True,
                        help='Path to the config file.')

    parser.add_argument('-D', '--enable-debug', dest='enable_debug', required=False, action='store_true',
                        help='Enables debug log messages.')

    return parser.parse_args()


def init_logging(log_filename, enable_debug):

    if enable_debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if log_filename:
        logging.basicConfig(filename=log_filename, level=log_level, format="%(asctime)s - %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s: %(message)s")


def worker_func(worker_state_table_item, lock_worker_state_table,
                task_queue, lock_task_assign, cond_task_assign):

    logging.debug("Started Worker with ID: %s" % multiprocessing.current_process().name)

    with CriticalSection(lock_worker_state_table):

        worker_state_table_item.set_state(WorkerState.READY)
        worker_state_table_item.set_timestamp(int(time.time()))

    run_condition = True

    while run_condition:

        task = None

        with CriticalSection(cond_task_assign):

            cond_task_assign.wait()

            if not task_queue.is_empty():

                task = task_queue.pop()

                worker_state_table_item.set_state(WorkerState.EXECUTING)
                worker_state_table_item.set_ost_name(task.name)
                worker_state_table_item.set_timestamp(int(time.time()))

        if task:

            task.execute()

            with CriticalSection(lock_worker_state_table):

                worker_state_table_item.set_state(WorkerState.READY)
                worker_state_table_item.set_ost_name('')
                worker_state_table_item.set_timestamp(int(time.time()))



    logging.debug("Exiting Worker with ID: %s" % multiprocessing.current_process().name)

    exit(0)


def create_worker_ids(worker_count):

    worker_ids = list()

    for i in range(0, worker_count):
        worker_ids.append("WORKER_" + str(i))

    return worker_ids


def create_worker_state_table(worker_ids):

    worker_state_table = dict()

    for i in range(0, len(worker_ids)):
        worker_state_table[worker_ids[i]] = WorkerStateTableItem()

    if len(worker_state_table) != len(worker_ids):
        raise RuntimeError("Inconsistent worker state table size found: %s - expected: %s"
                           % (len(worker_state_table), len(worker_ids)))

    return worker_state_table


def create_worker(worker_state_table, lock_worker_state_table,
                  task_queue, lock_task_assign, cond_task_assign):

    worker_handle_dict = dict()

    for worker_id in worker_state_table.iterkeys():

        worker_state_table_item = worker_state_table[worker_id]

        worker_handle = multiprocessing.Process(name=worker_id,
                                                target=worker_func,
                                                args=(worker_state_table_item, lock_worker_state_table,
                                                      task_queue, lock_task_assign, cond_task_assign))

        worker_handle_dict[worker_id] = worker_handle

    return worker_handle_dict


def start_worker(worker_handle_dict, worker_state_table):

    if not len(worker_handle_dict):
        raise RuntimeError("Empty worker handle dict!")

    if len(worker_handle_dict) != len(worker_state_table):
        raise RuntimeError('Different sizes in worker handle dict and worker state table detected!')

    for worker_id in worker_handle_dict.iterkeys():
        worker_handle_dict[worker_id].start()

    max_retry_count = 3
    for retry_count in range(1, max_retry_count + 1):

        worker_ready = True

        for worker_id in worker_handle_dict.iterkeys():

            if not (worker_handle_dict[worker_id].is_alive()
                    and worker_state_table[worker_id].get_state == WorkerState.READY):
                worker_ready = False

        if worker_ready:
            return True

        time.sleep(retry_count * len(worker_handle_dict))
        logging.debug("Waiting for worker to be READY - Waiting seconds: %s" % (retry_count * len(worker_handle_dict)))


def main():

    try:

        args = init_arg_parser()

        config_file_reader = ControllerConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        pid_file = config_file_reader.pid_file_dir + os.path.sep + os.path.basename(sys.argv[0]) + ".pid"

        with PIDControl(pid_file) as pid_control, \
                ControllerCommHandler(config_file_reader.comm_target,
                                      config_file_reader.comm_port,
                                      config_file_reader.poll_timeout) as comm_handler, \
                SharedQueue() as task_queue:

            if pid_control.lock():

                logging.info('Start')

                comm_handler.connect()

                request_retry_count = 0
                max_num_request_retries = 3
                request_retry_wait_duration = config_file_reader.request_retry_wait_duration

                lock_worker_state_table = multiprocessing.Lock()
                lock_task_assign = multiprocessing.Lock()

                cond_task_assign = multiprocessing.Condition(lock_task_assign)

                worker_count = config_file_reader.worker_count
                worker_ids = create_worker_ids(worker_count)
                worker_state_table = create_worker_state_table(worker_ids)
                worker_handle_dict = create_worker(worker_state_table, lock_worker_state_table,
                                                   task_queue, lock_task_assign, cond_task_assign)

                run_condition = True

                # TODO: Shutdown all worker!
                # TODO: Detect not_readt worker and READY worker for poisen pill
                # TODO -> Shutdown AFTER main loop!

                # TODO: Check all worker are active every x hours
                # and then cleanup the data structures if not alive anymove.

                if not start_worker(worker_handle_dict, worker_state_table):

                    logging.error("Not all worker are READY!")
                    run_condition = False

                while run_condition:

                    last_exec_timestamp = int(time.time())

                    found_ready_worker = False

                    with CriticalSection(cond_task_assign):

                        for worker_id in worker_state_table.iterkeys():

                            if worker_handle_dict[worker_id].is_alive() \
                                    and worker_state_table[worker_id].get_state == WorkerState.READY:

                                found_ready_worker = True
                                break

                    if found_ready_worker:

                        task_request = TaskRequest(comm_handler.fqdn)
                        comm_handler.send(task_request.to_string())
                        logging.debug('Requesting for task...')

                    else:
                        #TODO Send heartbeat?
                        logging.info("Should send heartbeat or something...")
                        time.sleep(1)
                        continue

                    in_raw_data = comm_handler.recv()

                    if in_raw_data:

                        logging.debug("Retrieved Message Raw Data: " + in_raw_data)
                        in_msg = MessageFactory.create(in_raw_data)

                        if in_msg.header == MessageType.OST_TASK_RESPONSE():
                            
                            ost_name = in_msg.body
                            logging.debug("Retrieved Task Response with OST name: " + ost_name)

                            with CriticalSection(cond_task_assign):

                                task = OSTTask(ost_name)

                                task_queue.push(task)

                                cond_task_assign.notify()

                        elif in_msg.header == MessageType.TASK_ACKNOWLEDGE():
                            logging.debug("Retrieved Task Acknowledge!")

                        elif in_msg.header == MessageType.WAIT_COMMAND():

                            wait_duration = in_msg.duration
                            logging.debug("Retrieved Wait Command with duration: " + str(wait_duration))
                            time.sleep(wait_duration)

                        elif in_msg.header == MessageType.EXIT_RESPONSE():

                            # TODO: add run_flag
                            logging.info('Finished')
                            exit(0)

                        # Reset after retrieving a message
                        if request_retry_count > 0:
                            request_retry_count = 0

                    else:

                        if request_retry_count == max_num_request_retries:

                            logging.debug('Exiting, since maximum retry count is reached!')
                            comm_handler.disconnect()
                            sys.exit(1)

                        time.sleep(request_retry_wait_duration)
                        logging.debug('No response retrieved - Reconnecting...')
                        comm_handler.reconnect()
                        request_retry_count += 1

            else:
                logging.error("Another instance might be already ru:nning as well!")
                logging.info("PID lock file: " + pid_file)
                exit(1)

    except Exception as e:

        logging.error("Caught exception on last instance: " + str(e))
        exit(1)

    logging.info('Finished')
    exit(0)


if __name__ == '__main__':
    main()
