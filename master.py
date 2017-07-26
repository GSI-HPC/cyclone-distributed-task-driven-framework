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
import multiprocessing
import os
import signal
import sys
import time
import re

from db.ost_perf_history_table_handler import OSTPerfHistoryTableHandler
from comm.master_handler import MasterCommHandler
from conf.master_config_file_reader import MasterConfigFileReader
from ctrl.ost_status_item import OstState
from ctrl.ost_status_item import OstStatusItem
from ctrl.pid_control import PIDControl
from ctrl.shared_queue import SharedQueue
from ctrl.critical_section import CriticalSection
from lfs.ost_list_processor import OSTListProcessor
from msg.exit_command import ExitCommand
from msg.message_factory import MessageFactory
from msg.message_type import MessageType
from msg.acknowledge import Acknowledge
from msg.task_assign import TaskAssign
from msg.wait_command import WaitCommand


TASK_DISTRIBUTION = True


def init_arg_parser():

    parser = argparse.ArgumentParser(description='Lustre OST Performance Testing Master Process.')

    parser.add_argument('-f', '--config-file', dest='config_file', type=str, required=True,
                        help='Path to the config file.')

    parser.add_argument('--create-table', dest='create_table', required=False, action='store_true',
                        help='Creates proper database table for storing OST performance measurements.')

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


def signal_handler_terminate(signal, frame):

    logging.info('Terminate')
    sys.exit(0)


def signal_handler_shutdown(signal, frame):

    logging.info('Shutting down...')

    global TASK_DISTRIBUTION

    if TASK_DISTRIBUTION:
        TASK_DISTRIBUTION = False


def check_all_controller_down(count_active_controller):

    if not count_active_controller:

        logging.info('Shutdown of controllers complete!')
        return True

    logging.debug("Waiting for number of controllers to quit: %s" % count_active_controller)
    return False


def main():

    try:

        args = init_arg_parser()

        config_file_reader = MasterConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        pid_file = config_file_reader.pid_file_dir + os.path.sep + os.path.basename(sys.argv[0]) + ".pid"

        error_count = 0
        max_error_count = 100

        ost_list_processor = None

        with PIDControl(pid_file) as pid_control, \
                MasterCommHandler(config_file_reader.comm_target,
                                  config_file_reader.comm_port,
                                  config_file_reader.poll_timeout) as comm_handler, \
                SharedQueue() as shared_queue:

            if pid_control.lock():

                logging.info('Start')

                signal.signal(signal.SIGINT, signal_handler_terminate)
                signal.signal(signal.SIGUSR1, signal_handler_shutdown)
                signal.siginterrupt(signal.SIGUSR1, True)

                ost_perf_his_table_handler = OSTPerfHistoryTableHandler(config_file_reader.host,
                                                                        config_file_reader.user,
                                                                        config_file_reader.passwd,
                                                                        config_file_reader.db,
                                                                        config_file_reader.table)

                if args.create_table:
                    ost_perf_his_table_handler.create_table()

                comm_handler.connect()

                controller_heartbeat_dict = dict()
                ost_status_lookup_dict = dict()

                controller_timeout = config_file_reader.controller_timeout
                measure_interval = config_file_reader.measure_interval
                lock_shared_queue_timeout = config_file_reader.lock_shared_queue_timeout
                controller_wait_duration = int(config_file_reader.controller_wait_duration)
                task_resend_timeout = config_file_reader.task_resend_timeout

                lock_shared_queue = multiprocessing.Lock()

                ost_list_processor = OSTListProcessor(shared_queue, lock_shared_queue, config_file_reader)
                ost_list_processor.start()

                # TODO: Make a class for the master.
                global TASK_DISTRIBUTION

                run_flag = True

                while run_flag:

                    try:

                        last_exec_timestamp = int(time.time())

                        recv_data = comm_handler.recv()

                        # TODO: To implement...
                        send_msg = None

                        if recv_data:

                            logging.debug("Retrieved message: " + recv_data)
                            recv_msg = MessageFactory.create(recv_data)

                            controller_heartbeat_dict[recv_msg.sender] = int(time.time())

                            if TASK_DISTRIBUTION:

                                # logging.debug("Task Queue is empty: " + str(shared_queue.is_empty()))

                                if MessageType.TASK_REQUEST() == recv_msg.header:

                                    ost_name = None

                                    with CriticalSection(lock_shared_queue, True, lock_shared_queue_timeout):

                                        if not shared_queue.is_empty():
                                            ost_name = shared_queue.pop()

                                        else:

                                            if not ost_list_processor.is_alive():

                                                TASK_DISTRIBUTION = False
                                                controller_wait_duration = 0

                                    if ost_name:

                                        if ost_name in ost_status_lookup_dict:

                                            task_resend_threshold = \
                                                (ost_status_lookup_dict[ost_name].timestamp + task_resend_timeout)

                                            if (ost_status_lookup_dict[ost_name].state == OstState.FINISHED) or \
                                                    last_exec_timestamp >= task_resend_threshold:

                                                ost_status_lookup_dict[ost_name] = \
                                                    OstStatusItem(ost_name,
                                                                  OstState.ASSIGNED,
                                                                  recv_msg.sender,
                                                                  int(time.time()))

                                                send_msg = TaskAssign(ost_name)

                                            elif ost_status_lookup_dict[ost_name].state == OstState.ASSIGNED and \
                                                    last_exec_timestamp < task_resend_threshold:

                                                # logging.debug("Waiting for a task on OST to finish: %s" % ost_name)
                                                #TODO: Wait duration how long?
                                                send_msg = WaitCommand(controller_wait_duration)

                                            else:
                                                raise RuntimeError("Undefined state processing task: ", ost_name)

                                        else:   # Add new OST name to lookup dict!

                                            ost_status_lookup_dict[ost_name] = \
                                                OstStatusItem(ost_name,
                                                              OstState.ASSIGNED,
                                                              recv_msg.sender,
                                                              int(time.time()))

                                            send_msg = TaskAssign(ost_name)

                                    else:
                                        send_msg = WaitCommand(controller_wait_duration)

                                    # logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())

                                elif MessageType.TASK_FINISHED() == recv_msg.header:

                                    ost_name = recv_msg.ost_name

                                    if ost_name in ost_status_lookup_dict:

                                        if recv_msg.sender == ost_status_lookup_dict[ost_name].controller:

                                            logging.debug("Retrieved finished OST message: " + ost_name)

                                            ost_status_lookup_dict[ost_name].state = OstState.FINISHED
                                            ost_status_lookup_dict[ost_name].timestamp = int(time.time())

                                        else:
                                            logging.warning("Retrieved task finished from different controller!")

                                    else:
                                        raise RuntimeError("Inconsistency detected on task finished!")

                                    send_msg = Acknowledge()
                                    # logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())

                                elif MessageType.HEARTBEAT() == recv_msg.header:

                                    send_msg = Acknowledge()
                                    # logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())

                                else:
                                    raise RuntimeError('Undefined type found in message: ' + recv_msg.to_string())

                            else:   # No more task distribution (TASK_DISTRIBUTION == FALSE)!

                                send_msg = ExitCommand()
                                # logging.debug("Sending message: " + send_msg.to_string())
                                comm_handler.send(send_msg.to_string())  # Does not block.

                                controller_heartbeat_dict.pop(recv_msg.sender, None)

                                if check_all_controller_down(len(controller_heartbeat_dict)):
                                    run_flag = False

                        else:   # POLL-TIMEOUT

                            logging.debug('RECV-MSG TIMEOUT')

                            # This gives controllers the last chance to quit themselves until a timeout is reached.
                            if not TASK_DISTRIBUTION:

                                for controller_name in controller_heartbeat_dict.keys():

                                    controller_threshold = \
                                        controller_heartbeat_dict[controller_name] + controller_timeout

                                    if last_exec_timestamp >= controller_threshold:
                                        controller_heartbeat_dict.pop(controller_name, None)

                                if check_all_controller_down(len(controller_heartbeat_dict)):
                                    run_flag = False

                    except Exception as e:

                        logging.error("Caught exception in main loop: %s" % e)

                        if TASK_DISTRIBUTION:
                            TASK_DISTRIBUTION = False

                        error_count += 1

                        if error_count == max_error_count:
                            run_flag = False

            else:

                logging.error("Another instance might be already running as well!")
                logging.info("PID lock file: " + pid_file)
                exit(1)

    except Exception as e:

        logging.error("Caught exception on main block: " + str(e))
        error_count += 1

    try:
        if ost_list_processor and ost_list_processor.is_alive():

            os.kill(ost_list_processor.pid, signal.SIGUSR1)

            for i in range(0, 10, 1):

                if ost_list_processor.is_alive():
                    logging.debug("Waiting for OST Processor to finish...")
                    time.sleep(1)
                else:
                    break

            if ost_list_processor.is_alive():

                ost_list_processor.terminate()
                ost_list_processor.join()

    except Exception as e:

        logging.error("Caught exception terminating OST Processor: " + str(e))
        error_count += 1

    logging.info("Finished")

    if error_count:
        return exit(1)

    exit(0)


if __name__ == '__main__':
    main()
