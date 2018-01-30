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
from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory


TASK_DISTRIBUTION = True


def init_arg_parser():

    default_config_file = "/etc/lfsm/master.conf"

    parser = argparse.ArgumentParser(description='LFSM Master')

    parser.add_argument('-f', '--config-file', dest='config_file', type=str, required=False,
                        help=str('Path to the config file (default: %s)' % default_config_file),
                        default=default_config_file)

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


def stop_task_distribution():

    global TASK_DISTRIBUTION

    if TASK_DISTRIBUTION:
        TASK_DISTRIBUTION = False


def signal_handler(signum, frame):

    if signum == signal.SIGHUP:

        logging.info('Retrieved hang-up signal.')
        stop_task_distribution()

    if signum == signal.SIGINT:

        logging.info('Retrieved interrupt program signal.')
        stop_task_distribution()

    if signum == signal.SIGTERM:

        logging.info('Retrieved signal to terminate.')
        stop_task_distribution()


def check_all_controller_down(count_active_controller):

    if not count_active_controller:

        logging.info('Shutdown of controllers complete!')
        return True

    logging.debug("Waiting for number of controllers to quit: %s" % count_active_controller)
    return False


def main():

    error_count = 0
    max_error_count = 100

    ost_list_processor = None

    try:

        args = init_arg_parser()

        config_file_reader = MasterConfigFileReader(args.config_file)

        init_logging(config_file_reader.log_filename, args.enable_debug)

        with PIDControl(config_file_reader.pid_file) as pid_control, \
                MasterCommHandler(config_file_reader.comm_target,
                                  config_file_reader.comm_port,
                                  config_file_reader.poll_timeout) as comm_handler, \
                SharedQueue() as ost_info_queue:

            if pid_control.lock():

                logging.info("Started Master with PID: [%s]", pid_control.pid())

                signal.signal(signal.SIGHUP, signal_handler)
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)

                signal.siginterrupt(signal.SIGHUP, True)
                signal.siginterrupt(signal.SIGINT, True)
                signal.siginterrupt(signal.SIGTERM, True)

                comm_handler.connect()

                controller_heartbeat_dict = dict()
                ost_status_lookup_dict = dict()

                controller_timeout = config_file_reader.controller_timeout
                controller_wait_duration = config_file_reader.controller_wait_duration
                task_resend_timeout = config_file_reader.task_resend_timeout

                task_def_file = config_file_reader.task_def_file
                task_name = config_file_reader.task_name

                task_xml_info = TaskXmlReader.read_task_definition(task_def_file, task_name)
                logging.debug("Loaded Task Information from XML: '%s.%s'" %
                              (task_xml_info.class_module, task_xml_info.class_name))

                task = TaskFactory().create_from_xml_info(task_xml_info)

                lock_ost_info_queue = multiprocessing.Lock()
                lock_ost_info_queue_timeout = 1

                ost_list_processor = OSTListProcessor(ost_info_queue, lock_ost_info_queue, config_file_reader)
                ost_list_processor.start()

                # TODO: Make a class for the master.
                global TASK_DISTRIBUTION

                run_flag = True

                while run_flag:

                    try:

                        last_exec_timestamp = int(time.time())

                        recv_data = comm_handler.recv()

                        send_msg = None

                        if recv_data:

                            logging.debug("Retrieved message: " + recv_data)

                            recv_msg = MessageFactory.create(recv_data)
                            recv_msg_type = recv_msg.type()

                            # TODO: Caution, sender is not set everywhere!
                            controller_heartbeat_dict[recv_msg.sender] = int(time.time())

                            if TASK_DISTRIBUTION:

                                if MessageType.TASK_REQUEST() == recv_msg_type:

                                    ost_info = None

                                    with CriticalSection(lock_ost_info_queue, True, lock_ost_info_queue_timeout):

                                        if not ost_info_queue.is_empty():
                                            ost_info = ost_info_queue.pop_nowait()

                                        else:

                                            if not ost_list_processor.is_alive():

                                                TASK_DISTRIBUTION = False
                                                controller_wait_duration = 0

                                    if ost_info:

                                        do_task_assign = False  # TODO: Could be a method call instead.

                                        if ost_info.name in ost_status_lookup_dict:

                                            task_resend_threshold = \
                                                (ost_status_lookup_dict[ost_info.name].timestamp + task_resend_timeout)

                                            if ost_status_lookup_dict[ost_info.name].state == OstState.finished() \
                                                    or last_exec_timestamp >= task_resend_threshold:

                                                do_task_assign = True

                                            elif ost_status_lookup_dict[ost_info.name].state == OstState.assigned() \
                                                    and last_exec_timestamp < task_resend_threshold:

                                                logging.debug("Waiting for a task on OST to finish: %s" % ost_info)
                                                send_msg = WaitCommand(controller_wait_duration)

                                            else:
                                                raise RuntimeError("Undefined state processing task: ", ost_info.name)

                                        else:   # Add new OST name to lookup dict!
                                            do_task_assign = True

                                        if do_task_assign:

                                            ost_status_lookup_dict[ost_info.name] = \
                                                OstStatusItem(ost_info.name,
                                                              OstState.assigned(),
                                                              recv_msg.sender,
                                                              int(time.time()))

                                            # Assign Lustre specific information to the task before task assignment.
                                            task.ost_name = ost_info.name
                                            task.oss_ip = ost_info.ip

                                            send_msg = TaskAssign(task)

                                    else:
                                        send_msg = WaitCommand(controller_wait_duration)

                                    logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())

                                elif MessageType.TASK_FINISHED() == recv_msg_type:

                                    ost_name = recv_msg.ost_name

                                    if ost_name in ost_status_lookup_dict:

                                        if recv_msg.sender == ost_status_lookup_dict[ost_name].controller:

                                            logging.debug("Retrieved finished OST message: " + ost_name)

                                            ost_status_lookup_dict[ost_name].state = OstState.finished()
                                            ost_status_lookup_dict[ost_name].timestamp = int(time.time())

                                        else:
                                            logging.warning("Retrieved task finished from different controller!")

                                    else:
                                        raise RuntimeError("Inconsistency detected on task finished!")

                                    send_msg = Acknowledge()
                                    logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())

                                elif MessageType.HEARTBEAT() == recv_msg_type:

                                    send_msg = Acknowledge()
                                    logging.debug("Sending message: " + send_msg.to_string())
                                    comm_handler.send(send_msg.to_string())

                                else:
                                    raise RuntimeError('Undefined type found in message: ' + recv_msg.to_string())

                            else:   # Do graceful shutdown, since task distribution is off!

                                logging.debug("Sending message: " + send_msg.to_string())
                                send_msg = ExitCommand()
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

                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

                        logging.error("Caught exception in main loop: %s - "
                                      "%s (line: %s)" % (str(e), filename, exc_tb.tb_lineno))

                        stop_task_distribution()

                        error_count += 1

                        if error_count == max_error_count:
                            run_flag = False

            else:

                logging.error("Another instance might be already running as well!")
                logging.info("PID lock file: '%s'" % config_file_reader.pid_file)

                sys.exit(1)

    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

        logging.error("Caught exception in main block: %s - "
                      "%s (line: %s)" % (str(e), filename, exc_tb.tb_lineno))

        error_count += 1

    try:
        if ost_list_processor and ost_list_processor.is_alive():

            os.kill(ost_list_processor.pid, signal.SIGTERM)

            for i in range(0, 10, 1):

                if ost_list_processor.is_alive():

                    logging.debug("Waiting for OSTListProcessor to finish...")
                    time.sleep(1)

                else:
                    break

            if ost_list_processor.is_alive():

                ost_list_processor.terminate()
                ost_list_processor.join()

    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

        logging.error("Caught exception (type: %s) on last instance: %s - %s (line: %s)"
                      % (exc_type, str(e), filename, exc_tb.tb_lineno))

        error_count += 1

    logging.info("Finished")

    if error_count:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
