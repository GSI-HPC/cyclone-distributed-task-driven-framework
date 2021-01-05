#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
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

from task.base_task import BaseTask
from db.ost_perf_result import OSTPerfResult
from util.auto_remove_file import AutoRemoveFile
from lfs.lfs_utils import LFSUtils


class IOTask(BaseTask):

    def __init__(self,
                 ost_idx,
                 block_size_bytes,
                 total_size_bytes,
                 write_file_sync,
                 target_dir,
                 lfs_bin,
                 lfs_target,
                 db_proxy_target,
                 db_proxy_port):

        super(IOTask, self).__init__()

        self.ost_idx = ost_idx

        self.block_size_bytes = int(block_size_bytes)
        self.total_size_bytes = int(total_size_bytes)

        self.write_file_sync = write_file_sync

        self.target_dir = target_dir

        self.lfs_bin = lfs_bin
        self.lfs_target = lfs_target

        self.db_proxy_target = db_proxy_target
        self.db_proxy_port = db_proxy_port

        # Initialization of other class attributes:
        self.payload_block = str()
        self.payload_rest_block = str()

        self.lfs_utils = LFSUtils(lfs_bin)

        if self.db_proxy_target != '' and self.db_proxy_port != '':
            self.db_proxy_endpoint = f"tcp://{self.db_proxy_target}:{self.db_proxy_port}"
        else:
            self.db_proxy_endpoint = None

        if not (self.write_file_sync == 'on' or self.write_file_sync == 'off'):
            raise RuntimeError("Value for parameter write_file_sync must be either 'on' or 'off'!")

    def execute(self):

        try:

            if self.lfs_utils.is_ost_idx_active(self.lfs_target, self.ost_idx):

                logging.debug(f"Found active OST-IDX: {self.ost_idx}")

                self._initialize_payload()

                file_path = self.target_dir + os.path.sep + self.ost_idx + "_perf_test.tmp"

                with AutoRemoveFile(file_path):

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    self.lfs_utils.set_stripe(self.ost_idx, file_path)

                    write_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    write_duration, write_throughput = self._write_file(file_path)

                    read_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    read_duration, read_throughput = self._read_file(file_path)

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

                logging.debug(f"Found non-active OST: {self.ost_idx}")

                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                ost_perf_result = \
                    OSTPerfResult(timestamp, timestamp, self.ost_idx, self.total_size_bytes, 0, 0, 0, 0)

            if ost_perf_result:

                logging.debug(f"ost_perf_result.to_csv_list: {ost_perf_result.to_csv_list()}")

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

            logging.error(f"Caught exception (type: {exc_type}) in IOTask: {e} - {filename} (line: {exc_tb.tb_lineno})")

    def _initialize_payload(self):

        # No random numbers are used, since no compression is used in Lustre FS directly.

        self.payload_block = "".join('A' for i in range(self.block_size_bytes))

        block_rest_size_bytes = self.total_size_bytes % self.block_size_bytes

        if block_rest_size_bytes > 0:
            self.payload_rest_block = "".join('A' for i in range(self.block_rest_size_bytes))

    def _write_file(self, file_path):

        try:
            logging.debug(f"Started writing to file: {file_path}")

            iterations = self.total_size_bytes / self.block_size_bytes

            start_time = time.time() * 1000.0

            with open(file_path, 'w') as f:

                for i in range(int(iterations)):
                    f.write(self.payload_block)

                if self.payload_rest_block:
                    f.write(self.payload_rest_block)

                if self.write_file_sync == "on":

                    logging.debug("write_file_sync is on!")

                    f.flush()
                    os.fsync(f.fileno())

            end_time = time.time() * 1000.0
            duration = (end_time - start_time) / 1000.0

            throughput = 0

            if duration:
                throughput = self.total_size_bytes / duration

            logging.debug(f"Finished writing to file: {file_path}")

            return tuple((duration, throughput))

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error(f"Caught exception (type: {exc_type}) in IOTask during write file: {e} "
                          f"- {filename} (line: {exc_tb.tb_lineno})")

            return tuple((-1, -1))

    def _read_file(self, file_path):

        try:
            if os.path.exists(file_path):

                file_size = os.path.getsize(file_path)

                if file_size == self.total_size_bytes:

                    logging.debug(f"Started reading from file: {file_path}")

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

                    logging.debug(f"Finished reading from file: {file_path}")

                    return tuple((duration, throughput))

                elif file_size == 0:
                    raise RuntimeError(f"File is empty: {file_path}")

                else:
                    raise RuntimeError(f"File is incomplete: {file_path}")

            else:
                raise RuntimeError(f"No file to be read could be found under: {file_path}")

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error(f"Caught exception (type: {exc_type}) in IOTask during read file: {e} "
                          f"- {filename} (line: {exc_tb.tb_lineno})")

            return tuple((-1, -1))
