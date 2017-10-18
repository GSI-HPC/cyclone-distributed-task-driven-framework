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
import re
import os


class MasterConfigFileReader:

    def __init__(self, config_file):

        if not os.path.isfile(config_file):
            raise IOError("The config file does not exist or is not a file: %s" % config_file)

        config = ConfigParser.ConfigParser()
        config.read(config_file)

        # TODO: Check parameter values!
        self.pid_file = config.get('control', 'pid_file')
        self.version = config.get('control', 'version')

        self.ost_reg_ex = re.compile(config.get('control', 'ost_reg_ex'))
        self.ip_reg_ex = re.compile(config.get('control', 'ip_reg_ex'))

        self.controller_timeout = float(config.get('control', 'controller_timeout'))
        self.lock_shared_queue_timeout = int(config.get('control', 'lock_shared_queue_timeout'))
        self.controller_wait_duration = int(config.get('control', 'controller_wait_duration'))
        self.task_resend_timeout = int(config.get('control', 'task_resend_timeout'))

        self.comm_target = config.get('comm', 'target')
        self.comm_port = int(config.get('comm', 'port'))
        self.poll_timeout = int(config.get('comm', 'poll_timeout')) * 1000

        self.log_filename = config.get('log', 'filename')

        self.lctl_bin = config.get('lustre', 'lctl_bin')
        self.lfs_bin = config.get('lustre', 'lfs_bin')
        self.lfs_target = config.get('lustre', 'lfs_target')

        self.measure_interval = float(config.get('test', 'measure_interval'))

        self.block_size_bytes = int(config.get('task', 'block_size_bytes'))
        self.total_size_bytes = int(config.get('task', 'total_size_bytes'))
        self.target_dir = config.get('task', 'target_dir')

        self.db_proxy_target = config.get('db_proxy', 'target')
        self.db_proxy_port = config.get('db_proxy', 'port')
