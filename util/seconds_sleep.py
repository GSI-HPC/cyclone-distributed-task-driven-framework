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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import time

from .interruptable_sleep import InterruptableSleep

class SecondsSleep(InterruptableSleep):

    def __init__(self) -> None:
        super().__init__()

    def sleep(self, seconds: int) -> None:

        self._do_sleep = True

        for _ in range(0, seconds):

            if not self._do_sleep:
                break

            time.sleep(1)
