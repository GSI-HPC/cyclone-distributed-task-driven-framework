#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

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
