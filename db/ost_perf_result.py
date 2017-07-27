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


class OSTPerfResult:

    def __init__(self,
                 read_timestamp,
                 write_timestamp,
                 ost,
                 ip,
                 size,
                 read_throughput,
                 write_throughput,
                 read_duration,
                 write_duration):

        self.read_timestamp = read_timestamp
        self.write_timestamp = write_timestamp
        self.ost = ost
        self.ip = ip
        self.size = size
        self.read_throughput = read_throughput
        self.write_throughput = write_throughput
        self.read_duration = read_duration
        self.write_duration = write_duration

    def to_string_csv_list(self):

        return "'" + self.read_timestamp + "'," \
            + "'" + self.write_timestamp + "'," \
            + "'" + self.ost + "'," \
            + "'" + self.ip + "'," \
            + str(self.size) + "," \
            + str(int(round(self.read_throughput, 0))) + "," \
            + str(int(round(self.write_throughput, 0))) + "," \
            + str(int(round(self.read_duration, 0))) + "," \
            + str(int(round(self.write_duration, 0)))
