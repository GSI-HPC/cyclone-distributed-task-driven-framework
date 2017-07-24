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
import signal

from worker import Worker
from worker import WorkerState
from worker import WorkerStateTableItem
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
from msg.heartbeat import Heartbeat
from task.ost_task import OSTTask


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
                  task_queue, cond_task_assign,
                  result_queue, cond_result_queue):

    worker_handle_dict = dict()

    for worker_id in worker_state_table.iterkeys():

        worker_state_table_item = worker_state_table[worker_id]

        worker_handle = Worker(worker_id,
                               worker_state_table_item, lock_worker_state_table,
                               task_queue, cond_task_assign,
                               result_queue, cond_result_queue)

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

        error_flag = False

        with PIDControl(pid_file) as pid_control, \
                ControllerCommHandler(config_file_reader.comm_target,
                                      config_file_reader.comm_port,
                                      config_file_reader.poll_timeout) as comm_handler, \
                SharedQueue() as result_queue, \
                SharedQueue() as task_queue:

            if pid_control.lock():

                logging.info('Start')

                comm_handler.connect()

                request_retry_count = 0
                max_num_request_retries = 3
                request_retry_wait_duration = config_file_reader.request_retry_wait_duration

                lock_worker_state_table = multiprocessing.Lock()
                lock_task_assign = multiprocessing.Lock()
                lock_result_queue = multiprocessing.Lock()

                cond_task_assign = multiprocessing.Condition(lock_task_assign)
                cond_result_queue = multiprocessing.Condition(lock_result_queue)

                worker_count = config_file_reader.worker_count
                worker_ids = create_worker_ids(worker_count)
                worker_state_table = create_worker_state_table(worker_ids)
                worker_handle_dict = create_worker(worker_state_table, lock_worker_state_table,
                                                   task_queue, cond_task_assign,
                                                   result_queue, cond_result_queue)

                run_condition = True

                if not start_worker(worker_handle_dict, worker_state_table):

                    logging.error("Not all worker are ready!")
                    error_flag = True
                    run_condition = False

                while run_condition:

                    last_exec_timestamp = int(time.time())

                    send_msg = None

                    with CriticalSection(cond_result_queue):

                        if not result_queue.is_empty():

                            task_result = result_queue.pop()

                            if task_result:

                                logging.debug("TASK RESULT: %s" % task_result)
                                send_msg = TaskFinished(comm_handler.fqdn, task_result)

                    if not send_msg:

                        with CriticalSection(cond_task_assign):

                            found_ready_worker = False

                            for worker_id in worker_state_table.iterkeys():

                                if worker_handle_dict[worker_id].is_alive() \
                                        and worker_state_table[worker_id].get_state == WorkerState.READY:

                                    found_ready_worker = True
                                    break

                        if found_ready_worker:

                            logging.debug('Requesting for task...')
                            send_msg = TaskRequest(comm_handler.fqdn)

                        else:

                            worker_count = len(worker_state_table)
                            worker_count_not_active = 0

                            for worker_id in worker_state_table.iterkeys():

                                if not worker_handle_dict[worker_id].is_alive():
                                    worker_count_not_active += 1

                            if worker_count == worker_count_not_active:

                                logging.error('No worker are alive!')
                                run_condition = False
                                error_flag = True
                                continue

                            else:   # Worker are busy

                                timeout = 2 # TODO: timeout how long???

                                with CriticalSection(cond_result_queue):

                                    cond_result_queue.wait(timeout)

                                    if result_queue.is_empty():

                                        logging.debug('Timeout on result queue, since no task is finished yet!')
                                        send_msg = Heartbeat(comm_handler.fqdn)

                                    else:

                                        task_result = result_queue.pop()

                                        if task_result:

                                            logging.debug("TASK RESULT: %s" % task_result)
                                            send_msg = TaskFinished(comm_handler.fqdn, task_result)

                    if send_msg:

                        logging.debug("Sending message to master: %s" % send_msg.to_string())
                        comm_handler.send(send_msg.to_string())

                    in_raw_data = comm_handler.recv()

                    if in_raw_data:

                        logging.debug("Retrieved Message Raw Data: " + in_raw_data)
                        in_msg = MessageFactory.create(in_raw_data)

                        if in_msg.header == MessageType.OST_TASK_RESPONSE():

                            ost_name = in_msg.body
                            logging.debug("Retrieved Task Response with OST name: " + ost_name)

                            with CriticalSection(cond_task_assign):

                                task_queue.push(OSTTask(ost_name))
                                cond_task_assign.notify()

                        elif in_msg.header == MessageType.ACKNOWLEDGE():
                            logging.debug("Retrieved Task Acknowledge!")

                        elif in_msg.header == MessageType.WAIT_COMMAND():

                            wait_duration = in_msg.duration
                            logging.debug("Retrieved Wait Command with duration: " + str(wait_duration))
                            time.sleep(wait_duration)

                        elif in_msg.header == MessageType.EXIT_RESPONSE():

                            run_condition = False
                            logging.info('Finishing...')

                        # Reset after retrieving a message
                        if request_retry_count > 0:
                            request_retry_count = 0

                    else:

                        if request_retry_count == max_num_request_retries:

                            logging.debug('Exiting, since maximum retry count is reached!')
                            comm_handler.disconnect()
                            run_condition = False

                        time.sleep(request_retry_wait_duration)
                        logging.debug('No response retrieved - Reconnecting...')
                        comm_handler.reconnect()
                        request_retry_count += 1

                # Shutdown all worker...
                if not run_condition:

                    try:

                        all_worker_down = False

                        for i in range(0, 10):

                            found_active_worker = False

                            for worker_id in worker_state_table.iterkeys():

                                if worker_handle_dict[worker_id].is_alive():

                                    os.kill(worker_handle_dict[worker_id].pid, signal.SIGUSR1)

                                    found_active_worker = True

                            if found_active_worker:

                                with CriticalSection(cond_task_assign):
                                    cond_task_assign.notify_all()

                                time.sleep(1)

                            else:
                                logging.debug('All worker are down!')
                                all_worker_down = True
                                break

                        if not all_worker_down:

                            for worker_id in worker_state_table.iterkeys():

                                if worker_handle_dict[worker_id].is_alive():

                                    logging.debug("Waiting for worker to terminate: %s"
                                                  % worker_handle_dict[worker_id].name)

                                    worker_handle_dict[worker_id].terminate()
                                    worker_handle_dict[worker_id].join()

                    except Exception as e:

                        logging.error("Caught exception terminating Worker: " + str(e))
                        error_flag = True

            else:
                logging.error("Another instance might be already running as well!")
                logging.info("PID lock file: " + pid_file)
                exit(1)

    except Exception as e:

        logging.error("Caught exception on last instance: " + str(e))
        exit(1)

    logging.info('Finished')
    exit(0)


if __name__ == '__main__':
    main()
