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

from zmq import ZMQError

from pid_control import PIDControl

from master_config_file_reader import MasterConfigFileReader

from comm.master_handler import MasterCommHandler

from msg.message_factory import MessageFactory
from msg.message_type import MessageType


RUN_CONDITION = True


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

    global RUN_CONDITION

    if RUN_CONDITION:
        RUN_CONDITION = False


def main():

    try:

        args = init_arg_parser()

        config_file_reader = MasterConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        pid_file = config_file_reader.pid_file_dir + os.path.sep + os.path.basename(sys.argv[0]) + ".pid"
        logging.debug("PID file: %s" % pid_file)

        with PIDControl(pid_file) as pid_control, \
                MasterCommHandler(config_file_reader.comm_target,
                                  config_file_reader.comm_port) as comm_handler:

            if pid_control.lock():

                logging.info('Start')

                signal.signal(signal.SIGINT, signal_handler_terminate)
                signal.signal(signal.SIGUSR1, signal_handler_shutdown)
                signal.siginterrupt(signal.SIGUSR1, True)

                comm_handler.connect()

                controller_last_heartbeat_map = dict()
                controller_timeout_sec = config_file_reader.controller_timeout_sec

                while True:

                    try:

                        in_raw_data = comm_handler.recv()
                        logging.debug("Retrieved Message from Worker: " + in_raw_data)

                        in_msg = MessageFactory.create_message(in_raw_data)

                        # Save last retrieved heartbeat from a controller
                        controller_last_heartbeat_map[in_msg.sender] = time.time()

                        if RUN_CONDITION:

                            if in_msg.type == MessageType.TASK_REQUEST():

                                # TODO: Where to get the task response...!
                                out_msg = MessageFactory.create_task_response('OST_NAME')
                                logging.debug("Sending message: " + out_msg.to_string())
                                comm_handler.send(out_msg.to_string())  # Does not block.

                            else:
                                raise RuntimeError('Undefined type found in message: ' + in_msg.to_string())

                        else:   # not RUN_CONDITION

                            out_msg = MessageFactory.create_exit_response()

                            logging.debug("Sending message: " + out_msg.to_string())
                            comm_handler.send(out_msg.to_string())  # Does not block.

                            controller_last_heartbeat_map.pop(in_msg.sender, None)

                            if not len(controller_last_heartbeat_map):

                                logging.info('Shutdown complete!')
                                sys.exit(0)

                        # controller_timeout_sec

                    except ZMQError as e:

                        if RUN_CONDITION:
                            logging.error("Caught ZMQ Exception: " + str(e))
                        else:
                            logging.warning("Caught ZMQ Exception: " + str(e))

    except Exception as e:

        logging.error("Caught exception on last instance: " + str(e))
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
