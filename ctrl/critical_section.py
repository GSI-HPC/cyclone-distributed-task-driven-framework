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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

class CriticalSection:

    def __init__(self, lock, block=True, timeout=None):

        self._lock = lock
        self._block = block
        self._timeout = timeout
        self._lock_acquired = False

    def __enter__(self):

        self._lock_acquired = self._lock.acquire(self._block, self._timeout)
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if self._lock_acquired:

            self._lock.release()
            self._lock_acquired = False

    def is_locked(self):
        return self._lock_acquired
