#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
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
"""Module for task generator"""

import abc
import configparser
import logging
import multiprocessing
import signal


class BaseTaskGenerator(multiprocessing.Process, metaclass=abc.ABCMeta):
    """Base class for Task Generator"""

    def __init__(self, task_queue, result_queue, config_file):

        super().__init__()

        self._task_queue = task_queue
        self._result_queue = result_queue

        self._config = configparser.ConfigParser()
        self._config.read_file(open(config_file))

        self._name = self.__class__.__name__
        self._run_flag = False

    def start(self):

        self._run_flag = True

        signal.signal(signal.SIGTERM, self._signal_handler_terminate)
        signal.siginterrupt(signal.SIGTERM, True)

        logging.info(f"{self._name} started!")

        # Start forked process after initialization.
        super().start()

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError("Must be implemented in specific TaskGenerator class!")

    def _signal_handler_terminate(self, signum, frame):
        # pylint: disable=unused-argument

        logging.debug("%s retrieved signal to terminate." % self._name)
        self._run_flag = False

