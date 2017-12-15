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


import os
import zmq
import time
import logging
import datetime
import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from base_task import BaseTask
from db.ost_perf_result import OSTPerfResult
from util.auto_remove_file import AutoRemoveFile
from lfs.lfs_utils import LFSUtils
from threading import Timer


class AlertIOTask(BaseTask):

    def __init__(self,
                 mail_server,
                 mail_sender,
                 mail_receiver,
                 mail_threshold,
                 block_size_bytes,
                 total_size_bytes,
                 target_dir,
                 lfs_bin,
                 lfs_target,
                 db_proxy_target,
                 db_proxy_port):

        super(AlertIOTask, self).__init__()

        self.mail_server = mail_server
        self.mail_sender = mail_sender
        self.mail_receiver = mail_receiver
        self.mail_threshold = float(mail_threshold)
        self.mail_receiver_list = self.mail_receiver.replace(' ', '').split(',')

        self.block_size_bytes = int(block_size_bytes)
        self.total_size_bytes = int(total_size_bytes)

        self.payload_block = str()
        self.payload_rest_block = str()

        self.target_dir = target_dir

        self.lfs_bin = lfs_bin
        self.lfs_utils = LFSUtils(lfs_bin)
        self.lfs_target = lfs_target

        self.db_proxy_target = db_proxy_target
        self.db_proxy_port = db_proxy_port
        self.db_proxy_endpoint = "tcp://" + self.db_proxy_target + ":" + self.db_proxy_port

    def execute(self):

        try:

            if self.lfs_utils.is_ost_available(self.ost_name, self.lfs_target):

                self._initialize_payload()

                file_path = self.target_dir + os.path.sep + self.ost_name + "_perf_test.tmp"

                with AutoRemoveFile(file_path):

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    self.lfs_utils.set_stripe(self.ost_name, file_path)

                    write_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    mail_subject = "[LUSTRE Monitoring] OST Write Performance Degradation Detected: %s" % self.ost_name

                    mail_text = "OST Name: %s\nOSS IP: %s\nTimestamp: %s\nAlert Threshold: %ss" % \
                                (self.ost_name, self.oss_ip, write_timestamp, str(self.mail_threshold))

                    args_send_mail = [(mail_subject, mail_text)]

                    mail_timer = Timer(self.mail_threshold, self._send_mail, args_send_mail)

                    mail_timer.start()

                    write_duration, write_throughput = self._write_file(file_path)

                    mail_timer.cancel()

                    read_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    mail_subject = "[LUSTRE Monitoring] OST Read Performance Degradation Detected: %s" % self.ost_name

                    mail_text = "OST Name: %s\nOSS IP: %s\nTimestamp: %s\nAlert Threshold: %ss" % \
                                (self.ost_name, self.oss_ip, write_timestamp, str(self.mail_threshold))

                    args_send_mail = [(mail_subject, mail_text)]

                    mail_timer = Timer(self.mail_threshold, self._send_mail, args_send_mail)

                    mail_timer.start()

                    read_duration, read_throughput = self._read_file(file_path)

                    mail_timer.cancel()

                    ost_perf_result = \
                        OSTPerfResult(read_timestamp,
                                      write_timestamp,
                                      self.ost_name,
                                      self.oss_ip,
                                      self.total_size_bytes,
                                      read_throughput,
                                      write_throughput,
                                      read_duration,
                                      write_duration)
            else:

                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                ost_perf_result = \
                    OSTPerfResult(timestamp, timestamp, self.ost_name, self.oss_ip, self.total_size_bytes, 0, 0, 0, 0)

            if ost_perf_result:

                logging.debug(ost_perf_result.to_string_csv_list())

                timeout = 1000

                context = zmq.Context()

                sock = context.socket(zmq.PUSH)

                sock.setsockopt(zmq.LINGER, timeout)
                sock.SNDTIMEO = timeout

                sock.connect(self.db_proxy_endpoint)

                sock.send(ost_perf_result.to_string_csv_list())

        except Exception as e:
            logging.error("Task-Exception: %s" % e)

    def _initialize_payload(self):

        # No random numbers are used, since no compression is used in Lustre FS directly.

        self.payload_block = "".join('A' for i in xrange(self.block_size_bytes))

        block_rest_size_bytes = self.total_size_bytes % self.block_size_bytes

        if block_rest_size_bytes > 0:
            self.payload_rest_block = "".join('A' for i in xrange(self.block_rest_size_bytes))

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

    def _write_file(self, file_path):

        try:
            iterations = self.total_size_bytes / self.block_size_bytes

            start_time = time.time() * 1000.0

            with open(file_path, 'w') as f:

                for i in xrange(int(iterations)):
                    f.write(self.payload_block)

                if self.payload_rest_block:
                    f.write(self.payload_rest_block)

                f.flush()
                os.fsync(f.fileno())

            end_time = time.time() * 1000.0
            duration = (end_time - start_time) / 1000.0

            throughput = 0

            if duration:
                throughput = self.total_size_bytes / duration

            return tuple((duration, throughput))

        except Exception as e:

            logging.error("Caught exception in AlertIOTask: %s" % e)
            return tuple((-1, -1))

    def _read_file(self, file_path):

        try:
            if os.path.exists(file_path):

                file_size = os.path.getsize(file_path)

                if file_size == self.total_size_bytes:

                    logging.debug("Reading output file from: %s" % file_path)

                    total_read_bytes = 0

                    start_time = time.time() * 1000.0

                    with open(file_path, 'r') as f:

                        read_bytes = f.read(self.block_size_bytes)
                        total_read_bytes += len(read_bytes)

                        while read_bytes:
                            read_bytes = f.read(self.block_size_bytes)
                            total_read_bytes += len(read_bytes)

                    end_time = time.time() * 1000.0
                    duration = (end_time - start_time) / 1000.0

                    if total_read_bytes != self.total_size_bytes:
                        raise RuntimeError('Read bytes differ from total size!')

                    throughput = 0

                    if duration:
                        throughput = self.total_size_bytes / duration

                    return tuple((duration, throughput))

                elif file_size == 0:
                    raise RuntimeError("File is empty: %s" % file_path)

                else:
                    raise RuntimeError("File is incomplete: %s" % file_path)

            else:
                raise RuntimeError("No file to be read could be found under: %s" % file_path)

        except Exception as e:

            logging.error("Caught exception in AlertIOTask: %s" % e)
            return tuple((-1, -1))

