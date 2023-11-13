#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Timer

import os
import zmq
import time
import logging
import datetime
import smtplib

from task.lustre_io_task import LustreIOTask
from db.ost_perf_result import OSTPerfResult
from util.auto_remove_file import AutoRemoveFile

class LustreAlertIOTask(LustreIOTask):

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

        super().__init__(ost_idx,
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

                str_ost_idx = str(self.ost_idx)

                logging.debug("Found active OST-IDX: %s", str_ost_idx)

                self._initialize_payload()

                file_path = self.target_dir + os.path.sep + str_ost_idx + "_perf_test.tmp"

                with AutoRemoveFile(file_path):

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    self.lfs_utils.set_ost_file_stripe(file_path, str_ost_idx)

                    write_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    mail_subject = f"[LUSTRE Monitoring] OST Write Performance Degradation Detected: {str_ost_idx}"

                    mail_text = f"Timestamp: {write_timestamp}\n" \
                                f"OST: {str_ost_idx}\n\n" \
                                f"Alert Threshold: {self.mail_threshold}s\n" \
                                f"Total Size: {self.total_size_bytes}\n" \
                                f"Block Size: {self.block_size_bytes}\n" \
                                f"Sync Flag: {self.write_file_sync}\n"

                    args_send_mail = [(mail_subject, mail_text)]

                    mail_timer = Timer(self.mail_threshold, self._send_mail, args_send_mail)

                    mail_timer.start()

                    write_duration, write_throughput = self._write_file(file_path)

                    mail_timer.cancel()

                    read_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    mail_subject = f"[LUSTRE Monitoring] OST Read Performance Degradation Detected: {str_ost_idx}"

                    mail_text = f"OST-IDX: {str_ost_idx}\n" \
                                f"Timestamp: {write_timestamp}\n" \
                                f"Alert Threshold: {self.mail_threshold}s"

                    args_send_mail = [(mail_subject, mail_text)]

                    mail_timer = Timer(self.mail_threshold, self._send_mail, args_send_mail)

                    mail_timer.start()

                    read_duration, read_throughput = self._read_file(file_path)

                    mail_timer.cancel()

                    ost_perf_result = \
                        OSTPerfResult(read_timestamp,
                                      write_timestamp,
                                      str_ost_idx,
                                      self.total_size_bytes,
                                      read_throughput,
                                      write_throughput,
                                      read_duration,
                                      write_duration)
            else:

                logging.debug("Found non-active OST: %s", str_ost_idx)

                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                ost_perf_result = \
                    OSTPerfResult(timestamp, timestamp, str_ost_idx, self.total_size_bytes, 0, 0, 0, 0)

            # TODO: Remove code redundancy in IOTasks.
            if ost_perf_result:

                if logging.root.isEnabledFor(logging.DEBUG):
                    logging.debug("ost_perf_result.to_csv_list: %s", ost_perf_result.to_csv_list())

                if self.db_proxy_endpoint:

                    timeout = 1000

                    context = zmq.Context()

                    sock = context.socket(zmq.PUSH)

                    sock.setsockopt(zmq.LINGER, timeout)
                    sock.SNDTIMEO = timeout

                    sock.connect(self.db_proxy_endpoint)

                    sock.send_string(ost_perf_result.to_csv_list())

                    logging.debug('Sent ost_perf_result to db-proxy.')

        except Exception:
            logging.exception('Caught exception during task execution')

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
