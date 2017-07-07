#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti <g.iannetti@gsi.de>
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
import Queue


# TODO: Redesign using a multiprocessing.Value instead... Using a Queue (Pipe) is not natural here!
class SingleItemSharedQueue:

    def __init__(self):
        self.__queue = multiprocessing.Queue(1)
        self.lock = multiprocessing.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__queue.close()

    @property
    def my_lock(self):
        return self.lock

    def clear_item(self):
        self.get_item()

    def get_item(self):

        try:
            return self.__queue.get_nowait()
        except Queue.Empty:
            print '>>>>>>> get item caught exception <<<<<<<<'
            return None

    def put_item(self, obj):
        self.__queue.put_nowait(obj)

    def has_item(self):

        if self.__queue.full():
            return True
        else:
            return False
