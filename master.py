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
import signal
import sys
import time
import multiprocessing

from single_item_shared_queue import SingleItemSharedQueue
from comm.master_handler import MasterCommHandler
from master_config_file_reader import MasterConfigFileReader
from msg.message_factory import MessageFactory
from msg.message_type import MessageType
from pid_control import PIDControl
from zmq import ZMQError


MAIN_LOOP_RUN_FLAG = True
TASK_DISTRIBUTION_FLAG = True


def init_arg_parser():

    parser = argparse.ArgumentParser(description='Lustre OST Performance Testing Master Process.')

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


def signal_handler_terminate(signal, frame):

    logging.info('Terminate')
    sys.exit(0)


def signal_handler_shutdown(signal, frame):

    logging.info('Shutting down...')

    global TASK_DISTRIBUTION_FLAG

    if TASK_DISTRIBUTION_FLAG:
        TASK_DISTRIBUTION_FLAG = False


def wait_for_controllers_shutdown(len_ctrl_map):

    if not len_ctrl_map:

        logging.info('Shutdown of controllers complete!')
        return True

    logging.debug("Waiting for number of controllers to quit: " + str(len_ctrl_map))
    return False


def process_ost_lists(active_ost_list_queue, measure_interval):

    # TODO RUN FLAG...
    while True:

        try:

            active_list, inactive_list = get_ost_lists()

            if active_ost_list_queue.lock.acquire():

                if active_ost_list_queue.has_item():
                    active_ost_list_queue.clear_item()

                active_ost_list_queue.put_item(active_list)
                active_ost_list_queue.lock.release()

            time.sleep(measure_interval)
            print 'sleep done'

        except Exception as e:
            logging.error("Caught exception in OST List Processor: " + str(e))


def get_ost_lists():

    active_ost_list = list()
    active_ost_list.append('nyx-OST0000-osc-ffff88102f578800')
    active_ost_list.append('nyx-OST0007-osc-ffff88102f578800')
    active_ost_list.append('nyx-OST000e-osc-ffff88102f578800')
    active_ost_list.append('nyx-OST0015-osc-ffff88102f578800')

    inactive_ost_list = list()
    inactive_ost_list.append('nyx-OST11ef-osc-ffff88102f578800')
    inactive_ost_list.append('nyx-OST22ef-osc-aaaa88102f578800')

    return tuple((active_ost_list, inactive_ost_list))


def update_active_ost_list(active_ost_list_queue):

    if active_ost_list_queue.has_item() and active_ost_list_queue.lock.acquire(False):

        if active_ost_list_queue.has_item():

            active_ost_list = active_ost_list_queue.get_item()

            if active_ost_list:
                print 'active_ost_list'

                active_ost_list_queue.lock.release()


def main():

    try:

        args = init_arg_parser()

        config_file_reader = MasterConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        pid_file = config_file_reader.pid_file_dir + os.path.sep + os.path.basename(sys.argv[0]) + ".pid"
        logging.debug("PID file: %s" % pid_file)

        with PIDControl(pid_file) as pid_control, \
                MasterCommHandler(config_file_reader.comm_target,
                                  config_file_reader.comm_port,
                                  config_file_reader.poll_timeout) as comm_handler:

            if pid_control.lock():

                logging.info('Start')

                signal.signal(signal.SIGINT, signal_handler_terminate)
                signal.signal(signal.SIGUSR1, signal_handler_shutdown)
                signal.siginterrupt(signal.SIGUSR1, True)

                comm_handler.connect()

                controller_heartbeat_map = dict()

                controller_timeout = config_file_reader.controller_timeout
                measure_interval = config_file_reader.measure_interval

                active_ost_list_queue = SingleItemSharedQueue()

                ost_lists_processor = \
                    multiprocessing.Process(target=process_ost_lists, args=(active_ost_list_queue, measure_interval))

                ost_lists_processor.start()

                ost_lists_update_timestamp = time.time()

                global MAIN_LOOP_RUN_FLAG
                while MAIN_LOOP_RUN_FLAG:

                    try:

                        last_exec_timestamp = time.time()

                        if TASK_DISTRIBUTION_FLAG:

                            update_active_ost_list(active_ost_list_queue)

                        recv_data = comm_handler.recv()

                        # Check if new data has been received from a controller
                        if recv_data:

                            logging.debug("Retrieved Message from Worker: " + recv_data)
                            recv_msg = MessageFactory.create_message(recv_data)

                            # Save last retrieved heartbeat from a controller
                            controller_heartbeat_map[recv_msg.sender] = time.time()

                            if TASK_DISTRIBUTION_FLAG:

                                if recv_msg.type == MessageType.TASK_REQUEST():

                                    # TODO: Where to get the task response...!
                                    send_msg = MessageFactory.create_task_response('OST_NAME')
                                    logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())  # Does not block.

                                else:
                                    raise RuntimeError('Undefined type found in message: ' + recv_msg.to_string())

                            else:   # NOT TASK_DISTRIBUTION_FLAG

                                send_msg = MessageFactory.create_exit_response()

                                logging.debug("Sending message: " + send_msg.to_string())
                                comm_handler.send(send_msg.to_string())  # Does not block.

                                controller_heartbeat_map.pop(recv_msg.sender, None)

                                if wait_for_controllers_shutdown(len(controller_heartbeat_map)):
                                    MAIN_LOOP_RUN_FLAG = False

                        else:   # POLL-TIMEOUT

                            logging.debug('*** POLL TIMEOUT ***')

                            if not TASK_DISTRIBUTION_FLAG:

                                # Check if a controller reached timeout
                                for controller_name in controller_heartbeat_map.keys():

                                    last_timestamp = controller_heartbeat_map[controller_name]

                                    if (last_timestamp + controller_timeout) <= last_exec_timestamp:
                                        controller_heartbeat_map.pop(controller_name, None)

                                if wait_for_controllers_shutdown(len(controller_heartbeat_map)):
                                    MAIN_LOOP_RUN_FLAG = False

                    except ZMQError as e:

                        if TASK_DISTRIBUTION_FLAG:
                            logging.error("Caught ZMQ Exception: " + str(e))
                        else:
                            logging.warning("Caught ZMQ Exception: " + str(e))

                # TODO NO GOOD!!! BETTER USE RUN FLAG WITH INTERRUPTION POSSIBILITY!
                print 'MAIN waiting for OST Processor to quit'
                ost_lists_processor.terminate()
                ost_lists_processor.join()

    except Exception as e:

        logging.error("Caught exception on last instance: " + str(e))
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
