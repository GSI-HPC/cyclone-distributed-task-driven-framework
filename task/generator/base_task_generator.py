#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

"""Module for task generator"""

import abc
import configparser
import logging
import multiprocessing
import signal

from ctrl.shared_queue import SharedQueue
from ctrl.shared_queue_str import SharedQueueStr
from util.interruptable_sleep import InterruptableSleep

class BaseTaskGenerator(multiprocessing.Process, metaclass=abc.ABCMeta):
    """Base class for Task Generator"""

    def __init__(self, task_queue: SharedQueue, result_queue: SharedQueueStr, config_file: str) -> None:

        super().__init__()

        self._task_queue = task_queue
        self._result_queue = result_queue

        self._config = configparser.ConfigParser()
        self._config.read_file(open(config_file))

        self._name = self.__class__.__name__
        self._run_flag = False

        self._interruptable_sleep = InterruptableSleep()

        # !!! CAUTION !!!
        # Use the SIGUSR1 instead of SIGTERM signal, since the signal handler will be passed by class inheritance.
        # Otherwise a task generator would catch SIGTERM with the master's PID, so the master would ignore it.
        signal.signal(signal.SIGUSR1, self._signal_handler_terminate)
        signal.siginterrupt(signal.SIGUSR1, True)

    def start(self) -> None:
        """Start forked BaseTaskGenerator process after initialization by the Master process."""

        self.validate_config()

        logging.info("%s started!", self._name)
        self._run_flag = True
        super().start()

    @abc.abstractmethod
    def run(self) -> None:
        raise NotImplementedError("Must be implemented in specific TaskGenerator class!")

    @abc.abstractmethod
    def validate_config(self) -> None:
        raise NotImplementedError("Must be implemented in specific TaskGenerator class!")

    def _signal_handler_terminate(self, signum : signal.Signals, frame) -> None:
        # pylint: disable=unused-argument

        logging.info("%s received signal to terminate", self._name)
        self._run_flag = False
        self._interruptable_sleep.interrupt()
