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


class WaitCommand(BaseMessage):
    """The Master sends this message to a controller to let the controller wait for a certain time in seconds."""

    def __init__(self, duration):
        super().__init__(MessageType.WAIT_COMMAND(), str(duration))

    def _validate(self):

        if not self.body:
            raise RuntimeError('No body is set!')

        # Validate duration as int value...
        # TODO: 0-...

    @property
    def duration(self):
        return int(self.body)

