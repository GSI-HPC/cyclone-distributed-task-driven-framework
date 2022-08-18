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

"""Module for additional control components"""

from ctrl.shared_queue import SharedQueue

class SharedQueueStr(SharedQueue):
    """Typified SharedQueue with str objects"""

    def __init__(self):
        super().__init__()

    def fill(self, in_list : list[str]):
        super().fill(in_list)

    def push(self, item : str):
        super().push(item)

    def pop_nowait(self) -> str:
        return super().pop_nowait()

    def pop(self) -> str:
        return super().pop()
