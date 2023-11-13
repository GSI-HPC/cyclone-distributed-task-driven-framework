#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import argparse
import logging
import signal
import time
import os

from ctrl.pid_control import PIDControl
from comm.proxy_handler import ProxyCommHandler
from conf.database_proxy_config_file_reader import DatabaseProxyConfigFileReader
from db.ost_perf_history_table_handler import OSTPerfHistoryTableHandler
from version.minimal_python import MinimalPython

RUN_FLAG = True

def init_arg_parser():

    parser = argparse.ArgumentParser(description='Cyclone Database Proxy')

    parser.add_argument('-f',
                        '--config-file',
                        dest='config_file',
                        type=str,
                        required=False,
                        help="Path to the config file (default: %(default)s)",
                        default='/etc/cyclone/database-proxy.conf')

    parser.add_argument('--create-table',
                        dest='create_table',
                        required=False,
                        action='store_true',
                        help='Creates proper database table '
                             'for storing OST performance measurements.')

    parser.add_argument('-D',
                        '--debug',
                        dest='enable_debug',
                        required=False,
                        action='store_true',
                        help='Enables debug log messages.')

    return parser.parse_args()

def init_logging(log_filename, enable_debug):

    if enable_debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if log_filename:
        logging.basicConfig(filename=log_filename,
                            level=log_level,
                            format="%(asctime)s - %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=log_level,
                            format="%(asctime)s - %(levelname)s: %(message)s")

def set_run_flag_false():

    global RUN_FLAG

    if RUN_FLAG:
        RUN_FLAG = False

def signal_handler(signum : signal.Signals, frame) -> None:
    # pylint: disable=unused-argument

    if signum == signal.SIGHUP:

        logging.info('Received hang-up signal')
        set_run_flag_false()

    elif signum == signal.SIGINT:

        logging.info('Received interrupt program signal')
        set_run_flag_false()

    elif signum == signal.SIGTERM:

        logging.info('Received signal to terminate')
        set_run_flag_false()

    else:
        logging.debug("Received unhandled signal: %i", signum)

def main():

    MinimalPython.check()

    error = False

    try:

        args = init_arg_parser()

        config_file_reader = DatabaseProxyConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        # TODO: Check Exception with *with* statement.
        with PIDControl(config_file_reader.pid_file) as pid_control, \
            ProxyCommHandler(
                config_file_reader.comm_target,
                config_file_reader.comm_port,
                config_file_reader.poll_timeout) as comm_handler, \
            OSTPerfHistoryTableHandler(
                config_file_reader.host,
                config_file_reader.user,
                config_file_reader.password,
                config_file_reader.database,
                config_file_reader.table) as table_handler:

            try:

                if pid_control.lock():

                    logging.info("Started")
                    logging.info(f"Database Proxy PID: {pid_control.pid()}")

                    signal.signal(signal.SIGHUP, signal_handler)
                    signal.signal(signal.SIGINT, signal_handler)
                    signal.signal(signal.SIGTERM, signal_handler)

                    signal.siginterrupt(signal.SIGHUP, True)
                    signal.siginterrupt(signal.SIGINT, True)
                    signal.siginterrupt(signal.SIGTERM, True)

                    last_store_timestamp = int(time.time())
                    store_timeout = config_file_reader.store_timeout
                    store_max_count = config_file_reader.store_max_count

                    if args.create_table:

                        table_handler.create_table()
                        logging.info('Created database table.')
                        logging.info("Finished")
                        os._exit(0)

                    comm_handler.connect()

                    while RUN_FLAG:

                        last_exec_timestamp = int(time.time())

                        # TODO: Building an object and validate data...
                        recv_data = comm_handler.recv_string()

                        if recv_data:

                            logging.debug("Retrieved data: %s", recv_data)

                            table_handler.insert(recv_data)

                        else:
                            logging.debug('Timeout...')

                        if (last_exec_timestamp >=
                            (last_store_timestamp + store_timeout)) or \
                                table_handler.count() >= store_max_count:

                            if table_handler.count():

                                logging.debug("Storing results...")

                                table_handler.store()
                                table_handler.clear()

                                last_store_timestamp = int(time.time())

                else:

                    logging.error(f"Another instance might be already running "
                                  f"(PID file: {config_file_reader.pid_file})!")
                    os._exit(1)

            except Exception as err:

                logging.error(f"Caught exception in inner block: {err}")
                set_run_flag_false()
                error = True

    except Exception as err:

        logging.error(f"Caught exception in outer block: {err}")
        os._exit(1)

    if table_handler and table_handler.count():

        logging.debug("Storing results into database...")

        table_handler.store()
        table_handler.clear()

    logging.info("Finished")

    if error:
        os._exit(1)
    else:
        os._exit(0)

if __name__ == '__main__':
    main()
