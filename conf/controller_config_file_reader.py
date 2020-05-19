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


import configparser
import os

from conf.config_value_error import ConfigValueError


class ControllerConfigFileReader:

    def __init__(self, config_file):

        if not os.path.isfile(config_file):
            raise IOError("The config file does not exist or is not a file: %s" % config_file)

        config = configparser.ConfigParser()
        config.read(config_file)

        self.pid_file = config.get('control', 'pid_file')
        self.request_retry_wait_duration = config.getint('control', 'request_retry_wait_duration')

        self.comm_target = config.get('comm', 'target')
        self.comm_port = config.getint('comm', 'port')
        self.poll_timeout = config.getint('comm', 'poll_timeout') * 1000

        self.log_filename = config.get('log', 'filename')

        self.worker_count = config.getint('processing', 'worker_count')

        self.validate()

    def validate(self):

        if not self.pid_file:
            raise ConfigValueError("No PID file was specified!")

        if not self.request_retry_wait_duration:
            raise ConfigValueError("No request retry wait duration was specified!")

        if not self.comm_target:
            raise ConfigValueError("No communication target was specified!")

        if not self.comm_port:
            raise ConfigValueError("No communication port was specified!")

        if not self.poll_timeout:
            raise ConfigValueError("No polling timeout was specified!")

        if self.worker_count < 1 or self.worker_count > 1000:
            raise ConfigValueError("Not supported worker count detected: %s" % self.worker_count)
