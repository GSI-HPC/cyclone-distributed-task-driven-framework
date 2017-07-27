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


import multiprocessing
import logging
import time


class OSTTask:

    def __init__(self, name, ip, block_size_bytes, total_size_bytes):

        self.name = name
        self.ip = ip
        self.block_size_bytes = block_size_bytes
        self.total_size_bytes = total_size_bytes

        self.payload_block = str()
        self.payload_block_rest = str()

    def execute(self):

        self._initialize_payload()

        logging.debug("*** %s ***" % self.name)
        logging.debug("*** %s ***" % self.ip)
        logging.debug("*** %s ***" % self.block_size_bytes)
        logging.debug("*** %s ***" % self.total_size_bytes)

    def _initialize_payload(self):

        # No random numbers are used, since no compression is used in Lustre FS directly.

        # start_time = time.time() * 1000.0

        self.payload_block = "".join('A' for i in xrange(self.block_size_bytes))

        block_rest_size_bytes = self.total_size_bytes % self.block_size_bytes

        if block_rest_size_bytes > 0:
            self.payload_block_rest = "".join('A' for i in xrange(self.block_rest_size_bytes))

        # end_time = time.time() * 1000.0
        # duration = round((end_time - start_time) / 1000.0, 2)
        # logging.debug("Creating total payload took: %s seconds." % duration)
