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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import multiprocessing
import queue


class SharedQueue:

    def __init__(self):
        self._queue = multiprocessing.Queue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._queue.close()

    def fill(self, in_list):
        """Fills the queue with the passed input list (blocking)"""

        if len(in_list) == 0:
            raise RuntimeError('Input list is empty!')

        if not self._queue.empty():
            raise RuntimeError('Shared Queue is not empty!')

        for item in in_list:
            self._queue.put(item)

    def clear(self):
        """Clears all items from the queue (blocking)"""

        while not self._queue.empty():

            try:
                self._queue.get()
            except Queue.Empty:
                # TODO throw exception?
                print('>>>>>>> clear: get item caught exception <<<<<<<<')

    def push(self, item):
        """Pushes an item into the queue (blocking)"""

        if not item:
            raise RuntimeError("Passed item for shared queue push was not set!")

        self._queue.put(item)

    def pop_nowait(self):
        """Returns an item from the queue (non-blocking)"""

        try:
            return self._queue.get_nowait()
        except Queue.Empty:
            # TODO throw exception?
            print('>>>>>>> pop_nowait caught exception <<<<<<<<')

        return None

    def pop(self):
        """Returns an item from the queue (blocking)"""

        try:
            return self._queue.get()
        except Queue.Empty:
            # TODO throw exception?
            print('>>>>>>> pop_nowait caught exception <<<<<<<<')

        return None

    def is_empty(self):
        """Checks if the queue is empty (non-blocking)"""

        if self._queue.empty():
            return True
        else:
            return False
