#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import time

class InterruptableSleep():
    """Base class for all interruptable sleep classes."""

    def __init__(self) -> None:
        self._do_sleep = False

    def sleep(self, seconds: float) -> None:

        if seconds <= 1:
            time.sleep(seconds)

        else:

            self._do_sleep = True

            if seconds % 1:
                total = round(seconds)
            else:
                total = int(seconds)

            for _ in range(0, total):

                if not self._do_sleep:
                    break

                time.sleep(1)

    def interrupt(self) -> None:

        if self._do_sleep:
            self._do_sleep = False
