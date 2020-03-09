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


from msg.base_message import BaseMessage
from msg.message_type import MessageType


class Acknowledge(BaseMessage):
    """
        Master sends this message to the controller for acknowledging a previous message from the controller
        (e.g. a task is finished or heartbeat message),

        This is required for the request and response model to not cause inconsistency in the communication model!
    """

    def __init__(self):
        super(Acknowledge, self).__init__(MessageType.ACKNOWLEDGE(), '')

    def _validate(self):
        pass

