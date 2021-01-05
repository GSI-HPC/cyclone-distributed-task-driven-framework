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


from abc import ABCMeta


class MessageType(metaclass=ABCMeta):

    def __init__(self):
        pass

    @staticmethod
    def TASK_REQUEST():
        return 'TASK_REQ'

    @staticmethod
    def TASK_ASSIGN():
        return 'TASK_ASS'

    @staticmethod
    def WAIT_COMMAND():
        return 'WAIT_CMD'

    @staticmethod
    def TASK_FINISHED():
        return 'TASK_FIN'

    @staticmethod
    def ACKNOWLEDGE():
        return 'ACK'

    @staticmethod
    def HEARTBEAT():
        return 'HEARTBEAT'

    @staticmethod
    def EXIT_COMMAND():
        return 'EXIT_CMD'
