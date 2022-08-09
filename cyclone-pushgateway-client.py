#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import configparser
import logging
import requests
import signal
import time

from conf.pushgateway_config_file_reader import PushgatewayConfigFileReader
from prometheus.lustre_file_creation_check import LustreFileCreationMetricProcessor

from ctrl.pid_control import PIDControl
from comm.proxy_handler import ProxyCommHandler

run_condition = True

lustre_file_creation_metrics = LustreFileCreationMetricProcessor()

def init_arg_parser():

    parser = argparse.ArgumentParser(description='Prometheus Pushgateway for Cyclone Metrics')

    default_config_file = "/etc/cyclone/pushgateway.conf"

    parser.add_argument('-f',
                        '--config-file',
                        dest='config_file',
                        type=str,
                        required=False,
                        help=f"Use this config file (default: {default_config_file})",
                        default=default_config_file)

    parser.add_argument('-D',
                        '--debug',
                        dest='enable_debug',
                        required=False,
                        action='store_true',
                        help='Enable debug log messages')

    return parser.parse_args()

def init_config_parser(filepath: str) -> configparser.ConfigParser:

    config = configparser.ConfigParser()
    config.read(filepath)
    return config

def init_logging(log_filename, enable_debug):

    if enable_debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if log_filename:
        logging.basicConfig(filename=log_filename, level=log_level, format="%(asctime)s - %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s: %(message)s")

def stop_run():

    global run_condition

    if run_condition:
        run_condition = False

def signal_handler(signum, frame):

    if signum == signal.SIGHUP:

        logging.info('Retrieved hang-up signal')
        stop_run()

    if signum == signal.SIGINT:

        logging.info('Retrieved interrupt program signal')
        stop_run()

    if signum == signal.SIGTERM:

        logging.info('Retrieved signal to terminate')
        stop_run()

def init_signal_handler():

    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    signal.siginterrupt(signal.SIGHUP, True)
    signal.siginterrupt(signal.SIGINT, True)
    signal.siginterrupt(signal.SIGTERM, True)

def process_recv_data(comm_handler: ProxyCommHandler):

    try:

        recv_data = comm_handler.recv_string()

        if recv_data:

            logging.debug("Recieved data: %s", recv_data)

            # Currently just the result of LustreFileCreationCheckTask is supported.
            # If multiple task results should be supported, add type field to message.
            lustre_file_creation_metrics.process(recv_data)

        else:
            logging.debug('Timeout...')

    except Exception:
        logging.exception('An error occurred')

def push_metics(url):

    is_debug = logging.root.isEnabledFor(logging.DEBUG)

    data = ''
    data += lustre_file_creation_metrics.data()

    if data:

        if is_debug:
            logging.debug('Pushing metrics to pushgateway')
            start = time.time()

        r = requests.post(url, data=data, timeout=10.0)
        r.raise_for_status()

        if is_debug:
            logging.debug(f"Pushed metrics in {round(time.time() - start, 2)}s")
            logging.debug(data)

def main():

    try:

        args = init_arg_parser()

        config_file_reader = PushgatewayConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        with PIDControl(config_file_reader.pid_file) as pid_control, \
            ProxyCommHandler(
                config_file_reader.comm_target,
                config_file_reader.comm_port,
                config_file_reader.poll_timeout) as comm_handler:

            if pid_control.lock():

                logging.info('START')
                logging.info("Pushgateway PID: %s", pid_control.pid())

                push_interval = config_file_reader.push_interval
                push_url      = config_file_reader.push_url

                init_signal_handler()

                comm_handler.connect()

                next_push_timestamp = int(time.time()) + push_interval

                while run_condition:

                    last_exec_timestamp = int(time.time())

                    process_recv_data(comm_handler)

                    if last_exec_timestamp >= next_push_timestamp:

                        next_push_timestamp = last_exec_timestamp + push_interval

                        push_metics(push_url)

                        lustre_file_creation_metrics.clear()

                logging.info('END')

            else:
                logging.error("Another instance might be already running (PID file: %s)", config_file_reader.pid_file)

    except Exception:
        logging.exception('An error occurred in main function')

if __name__ == '__main__':
    main()
