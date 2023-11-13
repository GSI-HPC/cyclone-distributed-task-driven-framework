#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import configparser
import os

from conf.config_value_error import ConfigValueError

class ControllerConfigFileReader:

    def __init__(self, config_file):

        if not os.path.isfile(config_file):
            raise IOError(f"The config file does not exist or is not a file: {config_file}")

        config = configparser.ConfigParser()
        config.read(config_file)

        self.pid_file = config.get('control', 'pid_file')
        self.request_retry_wait_duration = config.getint('control', 'request_retry_wait_duration')
        self.max_num_request_retries = config.getint('control', 'max_num_request_retries')

        self.comm_target = config.get('comm', 'target')
        self.comm_port = config.getint('comm', 'port')
        self.poll_timeout = config.getint('comm', 'poll_timeout') * 1000

        self.log_filename = config.get('log', 'filename')

        self.worker_count = config.getint('processing', 'worker_count')

        self.validate()

    def validate(self):

        if self.worker_count < 1 or self.worker_count > 1000:
            raise ConfigValueError(f"Not supported worker count detected: {self.worker_count}")
