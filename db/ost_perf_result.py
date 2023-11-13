#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

class OSTPerfResult:

    def __init__(self,
                 read_timestamp,
                 write_timestamp,
                 ost,
                 size,
                 read_throughput,
                 write_throughput,
                 read_duration,
                 write_duration):

        self.read_timestamp = read_timestamp
        self.write_timestamp = write_timestamp
        self.ost = ost
        self.size = size
        self.read_throughput = read_throughput
        self.write_throughput = write_throughput
        self.read_duration = read_duration
        self.write_duration = write_duration

    def to_csv_list(self):

        return "'" + self.read_timestamp + "'," \
            + "'" + self.write_timestamp + "'," \
            + "'" + self.ost + "'," \
            + str(self.size) + "," \
            + str(int(round(self.read_throughput, 0))) + "," \
            + str(int(round(self.write_throughput, 0))) + "," \
            + str(int(round(self.read_duration, 0))) + "," \
            + str(int(round(self.write_duration, 0)))
