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

import typing

NOT_INIT_INT=-999999

def conv_int(arg : str) -> int:

    if arg:
        return int(arg)
    else:
        return NOT_INIT_INT

# TODO: With Python 3.10 use for type hinting instead: -> int|None
def conv_int_none(arg : str) -> typing.Optional[int]:

    if arg:
        return int(arg)
    else:
        return None
