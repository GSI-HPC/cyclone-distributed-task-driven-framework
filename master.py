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
import signal
import sys
import os

from pid_control import PIDControl
from master_config_file_reader import MasterConfigFileReader
from master_socket_handler import MasterSocketHandler


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


def signal_handler(signal, frame):

    logging.info('Exit')
    sys.exit(0)


def main():

    try:

        args = init_arg_parser()

        config_file_reader = MasterConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        pid_file = config_file_reader.pid_file_dir + os.path.sep + os.path.basename(sys.argv[0]) + ".pid"
        logging.debug("PID file: %s" % pid_file)

        with PIDControl(pid_file) as pid_control, \
                MasterSocketHandler(config_file_reader.comm_target,
                                    config_file_reader.comm_port) as socket_handler:

            if pid_control.lock():

                logging.info('Start')

                signal.signal(signal.SIGINT, signal_handler)

                socket_handler.connect()

                # Process exits on retrieving SIGINT signal.
                while True:

                    message = socket_handler.socket.recv()

                    print "Retrieved Message Size: " + str(len(message))
                    print "Retrieved Message: " + message

                    socket_handler.socket.send("Send: " + message)
                    print "Send: " + message

    except Exception as e:

        logging.error("Caught exception on last instance: " + str(e))
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
