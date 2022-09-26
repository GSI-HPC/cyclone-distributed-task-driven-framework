#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import logging

from collections import defaultdict
from enum import Enum

from msg.base_message import BaseMessage

class LustreFileCreationCheckState(str, Enum):

    OK      = 'OK'
    ERROR   = 'ERROR'
    FAILED  = 'FAILED'
    IGNORED = 'IGNORED'

    def __str__(self) -> str:
        return self.value

class LustreFileCreationCheckResult:

    def __init__(self, target: str, state: LustreFileCreationCheckState, mdt_idx: int = None, ost_idx: int = None) -> None:

        if not target:
            raise RuntimeError('Argument target must be set')

        if not isinstance(state, LustreFileCreationCheckState):
            raise RuntimeError('Argument state must be type LustreFileCreationCheckState')

        result = f"{target}{BaseMessage.field_separator}{state}"

        if state in (LustreFileCreationCheckState.OK, LustreFileCreationCheckState.FAILED):

            if not isinstance(mdt_idx, int):
                raise RuntimeError('Argument mdt_idx must be type int')

            if not isinstance(ost_idx, int):
                raise RuntimeError('Argument ost_idx must be type int')

            result += f"{BaseMessage.field_separator}{mdt_idx}{BaseMessage.field_separator}{ost_idx}"

        self._target  = target
        self._state   = state
        self._mdt_idx = mdt_idx
        self._ost_idx = ost_idx
        self._result  = result

    def __str__(self) -> str:
        return self._result

    def to_string(self) -> str:
        return self._result

class LustreFileCreationMetricProcessor:

    def __init__(self) -> None:

        self.error_metric  = False
        self.check_metrics = defaultdict[str, dict](lambda: defaultdict[int, dict](dict[int, int]))

        self.metric_error_name = 'cyclone_lustre_file_creation_error'
        self.metric_error_help = f"# HELP {self.metric_error_name} Indicates if an error occured during the Lustre File Creation Check (0=False/1=True)."
        self.metric_error_type = f"# TYPE {self.metric_error_name} gauge"

        self.metric_check_name = 'cyclone_lustre_file_creation_check'
        self.metric_check_help = f"# HELP {self.metric_check_name} Indicates if the Lustre File Creation Check per MDT and OST succeeded (0=False/1=True)."
        self.metric_check_type = f"# TYPE {self.metric_check_name} gauge"

    def process(self, msg: str) -> None:

        result = LustreFileCreationMetricProcessor._create_from_str(msg)

        state = result._state

        if state in (LustreFileCreationCheckState.OK, LustreFileCreationCheckState.FAILED):

            target  = result._target
            mdt_idx = result._mdt_idx
            ost_idx = result._ost_idx

            if LustreFileCreationCheckState.OK == state:
                logging.debug('LustreFileCreationCheckState.OK')
                self.check_metrics[target][mdt_idx][ost_idx] = 1

            elif LustreFileCreationCheckState.FAILED == state:
                logging.debug('LustreFileCreationCheckState.FAILED')
                self.check_metrics[target][mdt_idx][ost_idx] = 0

        else:

            logging.debug('LustreFileCreationCheckState.ERROR')

            if not self.error_metric:
                self.error_metric = True

    def data(self) -> str:

        return (
            f"{self._create_error_metric()}"
            f"{self._create_check_metrics()}")

    def clear(self) -> None:
        self.error_metric = False
        self.check_metrics.clear()

    @staticmethod
    def _create_from_str(result: str) -> LustreFileCreationCheckResult:

        fields = result.split(BaseMessage.field_separator)

        target = fields[0]
        state  = fields[1]

        if LustreFileCreationCheckState.OK == state:
            return LustreFileCreationCheckResult(target, LustreFileCreationCheckState.OK, int(fields[2]), int(fields[3]))
        elif LustreFileCreationCheckState.FAILED == state:
            return LustreFileCreationCheckResult(target, LustreFileCreationCheckState.FAILED, int(fields[2]), int(fields[3]))
        elif LustreFileCreationCheckState.ERROR == state:
            return LustreFileCreationCheckResult(target, LustreFileCreationCheckState.ERROR)

        raise RuntimeError(f"State not supported for object creation from str: {state}")

    def _create_error_metric(self) -> str:

        metric_value = int(self.error_metric)

        return (
            f"{self.metric_error_help}\n"
            f"{self.metric_error_type}\n"
            f"{self.metric_error_name} {metric_value}\n")

    def _create_check_metrics(self) -> str:

        head = (
            f"{self.metric_check_help}\n"
            f"{self.metric_check_type}\n")

        data = ''

        for target in self.check_metrics:
            for mdt_idx in self.check_metrics[target]:
                for ost_idx in self.check_metrics[target][mdt_idx]:
                    value = self.check_metrics[target][mdt_idx][ost_idx]
                    data += f"{self.metric_check_name} {{target=\"{target}\", mdt_index=\"{mdt_idx}\", ost_index=\"{ost_idx}\"}} {value}\n"

        return head + data