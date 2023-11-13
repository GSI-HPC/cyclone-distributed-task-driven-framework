#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import os
import time
import fcntl

class PIDControl:

    def __init__(self, pid_file):

        if os.name != 'posix':
            raise RuntimeError('Just POSIX compliant OS is supported!')

        self._pid_file = pid_file
        self._pid = str(os.getpid())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()

    def lock(self):

        if not os.path.isfile(self._pid_file):
            return self.create_pid_file()
        else:

            pid_from_file = self.read_pid_from_file()

            if pid_from_file == self._pid:
                raise RuntimeError(f"Calling process (PID={self._pid}) is already owning the PID file!")

            if PIDControl.check_process_exits(pid_from_file):
                return False
            else:
                os.remove(self._pid_file)
                return self.create_pid_file()

    def unlock(self):

        if self.read_pid_from_file() == self._pid:
            os.remove(self._pid_file)

    def read_pid_from_file(self):

        if os.path.isfile(self._pid_file):

            with open(self._pid_file, 'r') as fd:

                content = fd.read()

                if not content:
                    raise RuntimeError(f"PID file is empty: {self._pid_file}")

            return content.split(';')[0]

        return -1

    # TODO change to int for pid not str
    def pid(self):
        return self._pid

    def create_pid_file(self):

        pid_file_dir = os.path.dirname(self._pid_file)

        if not os.path.isdir(pid_file_dir):
            raise IOError(f"Directory path does not exist for PID file: {pid_file_dir}")

        with open(self._pid_file, 'w') as fd:

            fcntl.lockf(fd, fcntl.LOCK_EX)

            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            fd.write(self._pid + ";" + timestamp)

            return True

        return False

    @staticmethod
    def check_process_exits(pid):
        return os.path.exists(f"/proc/{pid}")
