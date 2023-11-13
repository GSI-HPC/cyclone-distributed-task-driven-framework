#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

class CriticalSection:

    def __init__(self, lock, block=True, timeout=None):

        self._lock = lock
        self._block = block
        self._timeout = timeout
        self._lock_acquired = False

    def __enter__(self):

        self._lock_acquired = self._lock.acquire(self._block, self._timeout)
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if self._lock_acquired:

            self._lock.release()
            self._lock_acquired = False

    def is_locked(self):
        return self._lock_acquired
