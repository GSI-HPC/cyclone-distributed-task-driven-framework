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

class MasterConfigFileReader:

    def __init__(self, config_file):

        if not os.path.isfile(config_file):
            raise IOError(f"The config file does not exist or is not a file: {config_file}")

        config = configparser.ConfigParser()
        config.read(config_file)

        self.pid_file = config.get('control', 'pid_file')

        self.controller_timeout = config.getfloat('control', 'controller_timeout')
        self.controller_wait_duration = config.getint('control', 'controller_wait_duration')
        self.task_resend_timeout = config.getint('control', 'task_resend_timeout')

        self.comm_target = config.get('comm', 'target')
        self.comm_port = config.getint('comm', 'port')
        self.poll_timeout = config.getint('comm', 'poll_timeout') * 1000

        self.log_filename = config.get('log', 'filename')

        self.task_gen_module = config.get('task_generator', 'module')
        self.task_gen_class = config.get('task_generator', 'class')
        self.task_gen_config_file = config.get('task_generator', 'config_file')
