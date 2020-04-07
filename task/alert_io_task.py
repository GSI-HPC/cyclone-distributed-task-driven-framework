#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020 Gabriele Iannetti <g.iannetti@gsi.de>
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


import os
import sys
import zmq
import time
import logging
import datetime
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from task.io_task import IOTask
from db.ost_perf_result import OSTPerfResult
from util.auto_remove_file import AutoRemoveFile
from threading import Timer


class AlertIOTask(IOTask):

    def __init__(self,
                 mail_server,
                 mail_sender,
                 mail_receiver,
                 mail_threshold,
                 ost_idx,
                 block_size_bytes,
                 total_size_bytes,
                 write_file_sync,
                 target_dir,
                 lfs_bin,
                 lfs_target,
                 db_proxy_target,
                 db_proxy_port):

        super(AlertIOTask, self).__init__(ost_idx,
                                          int(block_size_bytes),
                                          int(total_size_bytes),
                                          write_file_sync,
                                          target_dir,
                                          lfs_bin,
                                          lfs_target,
                                          db_proxy_target,
                                          db_proxy_port)

        self.mail_server = mail_server
        self.mail_sender = mail_sender
        self.mail_receiver = mail_receiver
        self.mail_threshold = float(mail_threshold)
        self.mail_receiver_list = mail_receiver.replace(' ', '').split(',')

    def execute(self):

        try:

            if self.lfs_utils.is_ost_idx_active(self.lfs_target, self.ost_idx):

                self._initialize_payload()

                file_path = self.target_dir + os.path.sep + self.ost_idx + "_perf_test.tmp"

                with AutoRemoveFile(file_path):

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    self.lfs_utils.set_stripe(self.ost_idx, file_path)

                    write_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    mail_subject = "[LUSTRE Monitoring] OST Write Performance Degradation Detected: %s" % self.ost_idx

                    mail_text = "Timestamp: %s\n" \
                                "OST: %s\n\n" \
                                "Alert Threshold: %ss\n" \
                                "Total Size: %s\n" \
                                "Block Size: %s\n" \
                                "Sync Flag: %s\n" % \
                                (write_timestamp,
                                 self.ost_idx,
                                 self.mail_threshold,
                                 self.total_size_bytes,
                                 self.block_size_bytes,
                                 self.write_file_sync)

                    args_send_mail = [(mail_subject, mail_text)]

                    mail_timer = Timer(self.mail_threshold, self._send_mail, args_send_mail)

                    mail_timer.start()

                    write_duration, write_throughput = self._write_file(file_path)

                    mail_timer.cancel()

                    read_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    mail_subject = "[LUSTRE Monitoring] OST Read Performance Degradation Detected: %s" % self.ost_idx

                    mail_text = "OST-IDX: %s\nTimestamp: %s\nAlert Threshold: %ss" % \
                                (self.ost_idx, write_timestamp, str(self.mail_threshold))

                    args_send_mail = [(mail_subject, mail_text)]

                    mail_timer = Timer(self.mail_threshold, self._send_mail, args_send_mail)

                    mail_timer.start()

                    read_duration, read_throughput = self._read_file(file_path)

                    mail_timer.cancel()

                    ost_perf_result = \
                        OSTPerfResult(read_timestamp,
                                      write_timestamp,
                                      self.ost_idx,
                                      self.total_size_bytes,
                                      read_throughput,
                                      write_throughput,
                                      read_duration,
                                      write_duration)
            else:

                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                ost_perf_result = \
                    OSTPerfResult(timestamp, timestamp, self.ost_idx, self.total_size_bytes, 0, 0, 0, 0)

            # TODO: Remove code redundancy in IOTasks.
            if ost_perf_result:

                logging.debug("ost_perf_result.to_csv_list: %s" % ost_perf_result.to_csv_list())

                if self.db_proxy_endpoint:

                    timeout = 1000

                    context = zmq.Context()

                    sock = context.socket(zmq.PUSH)

                    sock.setsockopt(zmq.LINGER, timeout)
                    sock.SNDTIMEO = timeout

                    sock.connect(self.db_proxy_endpoint)

                    sock.send_string(ost_perf_result.to_csv_list())

                    logging.debug('Sent ost_perf_result to db-proxy.')

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error("Caught exception (type: %s) in AlertIOTask: %s - %s (line: %s)"
                          % (exc_type, str(e), filename, exc_tb.tb_lineno))

    def _send_mail(self, args):

        if args is None:
            raise RuntimeError("Passed argument for send mail is not set!")

        if len(args) != 2:
            raise RuntimeError("Passed argument for send mail has invalid number of arguments!")

        subject = args[0]
        text = args[1]

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.mail_sender
        msg['To'] = ', '.join(self.mail_receiver_list)

        msg.attach(MIMEText(text))
        msg_string = msg.as_string()

        logging.debug(msg_string)

        smtp_conn = smtplib.SMTP(self.mail_server)
        smtp_conn.sendmail(self.mail_sender, self.mail_receiver_list, msg_string)
        smtp_conn.quit()

