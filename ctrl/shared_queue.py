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


class SharedQueue:

    def __init__(self):
        self.__queue = multiprocessing.Queue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__queue.close()

    def fill(self, in_list):

        if len(in_list) == 0:
            raise RuntimeError('Input list is empty!')

        if not self.__queue.empty():
            raise RuntimeError('Shared Queue is not empty!')

        for item in in_list:
            self.__queue.put(item)

    def clear(self):

        while not self.__queue.empty():

            try:
                self.__queue.get()
            except Queue.Empty:
                print '>>>>>>> clear: get item caught exception <<<<<<<<'

    def pop(self):

        try:
            return self.__queue.get_nowait()
        except Queue.Empty:
            print '>>>>>>> pop caught exception <<<<<<<<'

        return None

    def is_empty(self):

        if self.__queue.empty():
            return True
        else:
            return False
