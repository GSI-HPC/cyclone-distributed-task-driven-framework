#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import abc

class BaseTask(metaclass=abc.ABCMeta):
    """Base task class to be implemented so a task can be executed by a worker."""

    # TODO: Think about refactoring, if tid should be passed by init method and loaded by the XML-based task generation.
    def __init__(self):
        """CAUTION: Initialization of a task with parameters must be in sync with the XML task definition and be all of type str."""

        super().__init__()

        self._tid = None

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('Must be implemented in subclass!')

    @property
    def tid(self):
        return self._tid

    @tid.setter
    def tid(self, tid):
        """CAUTION: task id (tid) must be set for each task object before execution."""

        if tid is None:
            raise ValueError('Argument tid must be set!')

        if type(tid) is str:
            self._tid = tid
        else:
            self._tid = str(tid)
