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


import logging
import datetime
import time
import os
import zmq

from db.ost_perf_result import OSTPerfResult
from util.auto_remove_file import AutoRemoveFile
from lfs.lfs_utils import LFSUtils


class OSTTask:

    def __init__(self,
                 name,
                 ip,
                 block_size_bytes,
                 total_size_bytes,
                 target_dir,
                 lfs_bin,
                 db_proxy_target,
                 db_proxy_port):

        self.name = name
        self.ip = ip
        self.block_size_bytes = block_size_bytes
        self.total_size_bytes = total_size_bytes

        self.payload_block = str()
        self.payload_rest_block = str()

        self.file_path = target_dir + os.path.sep + self.name + "_perf_test.tmp"

        self.lfs_utils = LFSUtils(lfs_bin)

        self.db_proxy_target = db_proxy_target
        self.db_proxy_port = db_proxy_port
        self.db_proxy_endpoint = "tcp://" + self.db_proxy_target + ":" + self.db_proxy_port


    def execute(self):

        ost_perf_result = None

        self._initialize_payload()

        with AutoRemoveFile(self.file_path):

            if os.path.exists(self.file_path):
                os.remove(self.file_path)

            self.lfs_utils.set_stripe(self.name, self.file_path)

            write_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            write_duration, write_throughput = self.write_file()

            read_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            read_duration, read_throughput = self.read_file()

            ost_perf_result = \
                OSTPerfResult(write_timestamp,
                              read_timestamp,
                              self.name,
                              self.ip,
                              self.total_size_bytes,
                              read_throughput,
                              write_throughput,
                              read_duration,
                              write_duration)

            try:

                if ost_perf_result:

                    timeout = 1000

                    context = zmq.Context()

                    sock = context.socket(zmq.PUSH)

                    sock.setsockopt(zmq.LINGER, timeout)
                    sock.SNDTIMEO = timeout

                    sock.connect(self.db_proxy_endpoint)

                    sock.send(ost_perf_result.to_string_csv_list())

            except Exception as e:
                logging.error("Exception: %s" % e)

    def _initialize_payload(self):

        # No random numbers are used, since no compression is used in Lustre FS directly.

        self.payload_block = "".join('A' for i in xrange(self.block_size_bytes))

        block_rest_size_bytes = self.total_size_bytes % self.block_size_bytes

        if block_rest_size_bytes > 0:
            self.payload_rest_block = "".join('A' for i in xrange(self.block_rest_size_bytes))

    def write_file(self):

        try:
            iterations = self.total_size_bytes / self.block_size_bytes

            start_time = time.time() * 1000.0

            with open(self.file_path, 'w') as f:

                for i in xrange(int(iterations)):
                    f.write(self.payload_block)

                if self.payload_rest_block:
                    f.write(self.payload_rest_block)

            end_time = time.time() * 1000.0
            duration = (end_time - start_time) / 1000.0

            throughput = 0

            if duration:
                throughput = self.total_size_bytes / duration

            return tuple((duration, throughput))

        except Exception as e:

            logging.error("Caught exception in OSTTask: %s" % e)
            return tuple((-1, -1))

    def read_file(self):

        try:
            if os.path.exists(self.file_path):

                file_size = os.path.getsize(self.file_path)

                if file_size == self.total_size_bytes:

                    logging.debug("Reading output file from: %s" % self.file_path)

                    total_read_bytes = 0

                    start_time = time.time() * 1000.0

                    with open(self.file_path, 'r') as f:

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
                    raise RuntimeError("File is empty: %s" % self.file_path)

                else:
                    raise RuntimeError("File is incomplete: %s" % self.file_path)

            else:
                raise RuntimeError("No file to be read could be found under: %s" % self.file_path)

        except Exception as e:

            logging.error("Caught exception in OSTTask: %s" % e)
            return tuple((-1, -1))
