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


class WorkerState:

    __metaclass__ = abc.ABCMeta

    @classmethod
    def ready(cls):
        return 0

    @classmethod
    def to_string(cls, state):

        if state == 0:
            return "READY"
        else:
            raise RuntimeError("Not supported worker state detected: %i" % state)


class WorkerStateTableItem:

    def __init__(self):

        # # RETURNS STDOUT: self._state = "TEXT" + str(NUMBER)
        # # RETURNS BAD VALUE: self._timestamp.value = 1234567890.99
        # self._state = multiprocessing.RawValue(ctypes.c_char_p)
        # self._task_name = multiprocessing.RawValue(ctypes.c_char_p)
        # self._timestamp = multiprocessing.RawValue(ctypes.c_float)

        self._state = multiprocessing.RawValue(ctypes.c_int)
        self._task_name = multiprocessing.RawArray('c', 10)
        self._timestamp = multiprocessing.RawValue(ctypes.c_uint)

    @property
    def get_state(self):
        return self._state.value

    @property
    def get_task_name(self):
        return self._task_name.value.decode()

    @property
    def get_timestamp(self):
        return self._timestamp.value

    def set_state(self, state):
        self._state.value = state

    def set_task_name(self, task_name):
        self._task_name.value = task_name.encode()

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


def worker_func(worker_state_table_item, worker_state_table_lock,
                task_queue, result_queue, task_queue_lock, result_queue_lock):

    print ("PID: %s" % multiprocessing.current_process().pid)
    print ("Worker-Name: %s" % multiprocessing.current_process().name)

    with CriticalSection(worker_state_table_lock):

        time.sleep(1)

        print ("Worker-Name: %s - In critical section!" % multiprocessing.current_process().name)

        worker_state_table_item.set_state(WorkerState.ready())
        worker_state_table_item.set_timestamp(int(time.time()))

    if not task_queue.is_empty():
        print("Queue-Pop: %s" % task_queue.pop())

    exit(0)


def create_worker_state_table(worker_count):

    worker_state_table = dict()

    for i in range(0, worker_count):
        worker_state_table[i] = WorkerStateTableItem()

    if len(worker_state_table) != worker_count:
        raise RuntimeError("Inconsistent worker state table size found: %s - expected: %s"
                           % (len(worker_state_table), worker_count))

    return worker_state_table


def create_worker(worker_count, worker_state_table, worker_state_table_lock,
                  task_queue, result_queue, task_queue_lock, result_queue_lock):

    worker_handle_dict = dict()

    for i in range(0, worker_count):

        worker_state_table_item = worker_state_table[i]

        worker_handle = multiprocessing.Process(name=str(i),
                                                target=worker_func,
                                                args=(worker_state_table_item, worker_state_table_lock,
                                                      task_queue, result_queue, task_queue_lock, result_queue_lock))

        worker_handle_dict[i] = worker_handle

    return worker_handle_dict


def check_worker_for_ready_state(worker_state_table):

    for i in range(0, len(worker_state_table)):

        if worker_state_table[i].get_state != WorkerState.ready():
            raise RuntimeError("Not all worker are ready!")

    logging.info("All workers are ready!")


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
                SharedQueue() as task_queue, \
                SharedQueue() as result_queue:

            if pid_control.lock():

                logging.info('Start')

                comm_handler.connect()

                request_retry_count = 0
                max_num_request_retries = 3
                request_retry_wait_duration = config_file_reader.request_retry_wait_duration

                worker_worker_state_table_lock = multiprocessing.Lock()
                task_queue_lock = multiprocessing.Lock()
                result_queue_lock = multiprocessing.Lock()

                worker_count = config_file_reader.worker_count
                worker_state_table = create_worker_state_table(worker_count)
                worker_handle_dict = create_worker(worker_count, worker_state_table, worker_worker_state_table_lock,
                                                   task_queue, result_queue, task_queue_lock, result_queue_lock)

                check_worker_for_ready_state(worker_state_table)

                exit(0)

                while True:

                    last_exec_timestamp = int(time.time())

                    # TODO: Does just task requests for testing...
                    task_request = TaskRequest(comm_handler.fqdn)
                    comm_handler.send(task_request.to_string())
                    logging.debug('sent task request')

                    in_raw_data = comm_handler.recv()

                    if in_raw_data:

                        logging.debug("Retrieved Message Raw Data: " + in_raw_data)
                        in_msg = MessageFactory.create(in_raw_data)

                        if in_msg.header == MessageType.TASK_RESPONSE():

                            #TODO: What do to next with the task response...!
                            ost_name = in_msg.body
                            logging.debug("Retrieved Task Response with OST name: " + ost_name)

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
