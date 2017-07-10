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

from pid_control import PIDControl
from controller_config_file_reader import ControllerConfigFileReader
from comm.controller_handler import ControllerCommHandler

from msg.message_factory import MessageFactory
from msg.message_type import MessageType


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


def main():

    try:

        args = init_arg_parser()

        config_file_reader = ControllerConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        pid_file = config_file_reader.pid_file_dir + os.path.sep + os.path.basename(sys.argv[0]) + ".pid"
        logging.debug("PID file: %s" % pid_file)

        with PIDControl(pid_file) as pid_control, \
                ControllerCommHandler(config_file_reader.comm_target,
                                      config_file_reader.comm_port,
                                      config_file_reader.poll_timeout) as comm_handler:

            if pid_control.lock():

                logging.info('Start')

                comm_handler.connect()

                request_retry_count = 0
                MAX_REQUEST_RETRIES = 3

                while True:

                    task_request = MessageFactory.create_task_request(comm_handler.fqdn)
                    comm_handler.send(task_request.to_string())

                    in_raw_data = comm_handler.recv()

                    if in_raw_data:

                        logging.debug("Retrieved Message Raw Data: " + in_raw_data)
                        in_msg = MessageFactory.create_message(in_raw_data)

                        if in_msg.header == MessageType.TASK_RESPONSE():

                            #TODO: What do to next with the task response...!
                            logging.debug("Retrieved Task Response: " + in_msg.body)

                        elif in_msg.header == MessageType.WAIT_COMMAND():

                            wait_duration = in_msg.duration
                            logging.debug("Retrieved Wait Command with duration: " + str(wait_duration))
                            time.sleep(wait_duration)

                        elif in_msg.header == MessageType.EXIT_RESPONSE():

                            logging.debug('Quit!')
                            exit(0)

                    else:

                        request_retry_count = request_retry_count + 1

                        if request_retry_count == MAX_REQUEST_RETRIES:

                            logging.debug('Exiting, since maximum retry count is reached!')
                            comm_handler.disconnect()
                            sys.exit(1)

                        logging.debug('No response retrieved - Reconnecting...')
                        comm_handler.reconnect()

                    time.sleep(2)

    except Exception as e:

        logging.error("Caught exception on last instance: " + str(e))
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
