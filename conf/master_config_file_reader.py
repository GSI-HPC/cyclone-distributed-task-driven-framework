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


class MasterConfigFileReader:

    def __init__(self, config_file):

        if not os.path.isfile(config_file):
            raise IOError("The config file does not exist or is not a file: %s" % config_file)

        config = configparser.ConfigParser()
        config.read(config_file)

        self.version = config.get('control', 'version')
        self.pid_file = config.get('control', 'pid_file')

        self.controller_timeout = float(config.get('control', 'controller_timeout'))
        self.controller_wait_duration = int(config.get('control', 'controller_wait_duration'))
        self.task_resend_timeout = int(config.get('control', 'task_resend_timeout'))

        self.comm_target = config.get('comm', 'target')
        self.comm_port = int(config.get('comm', 'port'))
        self.poll_timeout = int(config.get('comm', 'poll_timeout')) * 1000

        self.log_filename = config.get('log', 'filename')

        self.task_def_file = config.get('task', 'task_def_file')
        self.task_name = config.get('task', 'task_name')

        self.measure_interval = float(config.get('task_generator', 'measure_interval'))
        self.lfs_bin = config.get('task_generator', 'lfs_bin')
        self.lfs_target = config.get('task_generator', 'lfs_target')
        tmp_ost_select_list = config.get('task_generator', 'ost_select_list')

        if tmp_ost_select_list:
            self.ost_select_list = tmp_ost_select_list.replace(' ', '').split(',')
        else:
            self.ost_select_list = list()

    def validate(self):

        if not self.version:
            raise ConfigValueError("No version number was specified!")

        if not self.pid_file:
            raise ConfigValueError("No PID file was specified!")

        if not self.controller_timeout:
            raise ConfigValueError("No controller timeout was set!")

        if not self.controller_wait_duration:
            raise ConfigValueError("No controller wait duration was set!")

        if not self.task_resend_timeout:
            raise ConfigValueError("No task resend timeout was set!")

        if not self.comm_target:
            raise ConfigValueError("No communication target was specified!")

        if not self.comm_port:
            raise ConfigValueError("No communication port was specified!")

        if not self.poll_timeout:
            raise ConfigValueError("No polling timeout was specified!")

        if not self.lfs_bin:
            raise ConfigValueError("No LFS binary was specified!")

        if not self.lfs_target:
            raise ConfigValueError("No Lustre file system target was specified!")

        if not self.measure_interval:
            raise ConfigValueError("No measure interval was specified!")

        if not self.task_def_file:
            raise ConfigValueError("No task definition file was specified!")

        if not self.task_name:
            raise ConfigValueError("No task name for a task execution was specified!")

