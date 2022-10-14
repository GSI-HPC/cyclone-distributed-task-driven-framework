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

import time

class InterruptableSleep():
    """Base class for all interruptable sleep classes."""

    def __init__(self) -> None:
        self._do_sleep = False

    def sleep(self, seconds: float) -> None:

        if seconds <= 1:
            time.sleep(seconds)

        else:

            self._do_sleep = True

            if seconds % 1:
                total = round(seconds)
            else:
                total = int(seconds)

            for _ in range(0, total):

                if not self._do_sleep:
                    break

                time.sleep(1)

    def interrupt(self) -> None:

        if self._do_sleep:
            self._do_sleep = False
