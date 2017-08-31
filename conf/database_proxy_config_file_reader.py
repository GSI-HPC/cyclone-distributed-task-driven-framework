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


import ConfigParser
import os


class DatabaseProxyConfigFileReader:

    def __init__(self, config_file):

        if not os.path.isfile(config_file):
            raise IOError("The config file does not exist or is not a file: %s" % config_file)

        config = ConfigParser.ConfigParser()
        config.read(config_file)

        # TODO: Check parameter values!
        self.pid_file = config.get('control', 'pid_file')

        self.comm_target = config.get('comm', 'target')
        self.comm_port = int(config.get('comm', 'port'))
        self.poll_timeout = int(config.get('comm', 'poll_timeout')) * 1000

        self.log_filename = config.get('log', 'filename')

        self.host = config.get('db', 'host')
        self.user = config.get('db', 'user')
        self.passwd = config.get('db', 'passwd')
        self.db = config.get('db', 'database')
        self.table = config.get('db', 'table')
        self.store_timeout = int(config.get('db', 'store_timeout'))
        self.store_max_count = int(config.get('db', 'store_max_count'))

        self.validate()

    def validate(self):
        pass