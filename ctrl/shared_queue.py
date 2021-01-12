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

"""Module for additional control components"""

import multiprocessing
import queue


class SharedQueue:
    """Wrapper class for the multiprocessing.Queue.

    Underlying multiprocessing.Queue uses locking mechanism for single accesses
    on get() and put(), which are mapped by pop() and push() method for blocking access.

    Use a locking mechanism to guarantee consistency accessing the SharedQueue's
    multiple access methods, for instance fill() and clear(), also with the is_empty() method.
    For the benefit of performance gain, additional locking has to be provided outside or
    by implementing a subclass.

    Example for concurrent accesses on the SharedQueue between accesses of P1 and P2
    are provided as following:

    # P1
    with CriticalSection(SharedQueue.lock):

        if not SharedQueue.is_empty():
            SharedQueue.clear()

        SharedQueue.fill(List)

    # P2
    with CriticalSection(SharedQueue.lock, timeout=1) as critical_section:

        if critical_section.is_locked():

            if not SharedQueue.is_empty():

                # Use non-blocking access here, otherwise a blocking access
                # might interfere with the clear() in the other critical section.
                # Such a race condition might lead to a deadlock situation.
                item = SharedQueue.pop_nowait()

                if item:
                    item.do_something()

    Note: CriticalSection is provided in the local package named ctrl.
    """

    def __init__(self):
        self._queue = multiprocessing.Queue()
        self._lock = multiprocessing.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._queue.close()

    def fill(self, in_list):
        """Fills the queue with the passed input list (partly blocking).

        Since the items in the queue have to be iterated over, just each insert
        of an item is blocking. But the iteration does not guarantee full consistency.
        Because of multiprocessing semantics, this is not reliable.
        Use a locking mechanism to guarantee consistency.
        """

        if len(in_list) == 0:
            raise RuntimeError('Input list is empty!')

        if not self._queue.empty():
            raise RuntimeError('Shared Queue is not empty!')

        for item in in_list:
            self._queue.put(item)

    def clear(self):
        """Clears all items from the queue (partly blocking).

        Since the items in the queue have to be iterated over, just each remove
        of an item is blocking. But the iteration does not guarantee full consistency.
        Because of multiprocessing semantics, this is not reliable.
        Use a locking mechanism to guarantee consistency.
        """

        while not self._queue.empty():
            self._queue.get()

    def push(self, item):
        """Pushes an item into the queue (blocking).
           It might block until a free slot becomes available.
        """

        if not item:
            raise RuntimeError("Passed item for shared queue push was not set!")

        self._queue.put(item)

    def pop_nowait(self):
        """Returns an item from the queue (non-blocking).

        Returns
        -------
        object
            on success an object retrieved from the SharedQueue is returned,
            otherwise None is returned.
        """

        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def pop(self):
        """Returns an item from the queue (blocking)."""
        return self._queue.get()

    def is_empty(self):
        """Checks if the queue is empty (non-blocking).

        Returns True if the queue is empty, False otherwise.
        Because of multiprocessing semantics, this is not reliable.
        Use a locking mechanism to guarantee consistency.
        """
        return self._queue.empty()

    @property
    def lock(self):
        """Returns the prehold internal lock used for critical sections.
           Use of this lock is not forced, but using it keeps code more compact."""
        return self._lock
