#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti
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


import os
import time
import fcntl


class PIDControl:

   def __init__(self, pid_file):
      self.pid_file = pid_file

   def __enter__(self):
      return self

   def __exit__(self, exc_type, exc_value, traceback):
      self.unlock()

   def lock(self):
      
      if not os.path.isfile(self.pid_file):
         
         fd = open(self.pid_file, 'wb')
         
         fcntl.lockf(fd, fcntl.LOCK_EX)
         
         timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
         
         fd.write(str(os.getpid()) + ";" + timestamp)
         fd.close()
         
         return True
         
      else:
         
         if self.read_pid_from_file() == os.getpid():
            raise RuntimeError("Calling process (PID=%s) is already owning the PID file!" % str(os.getpid()))
         
         return False
   
   def unlock(self):
      
      if self.read_pid_from_file() == os.getpid():
         os.remove(self.pid_file)

   def read_pid_from_file(self):
      
      if os.path.isfile(self.pid_file):
      
         fd = open(self.pid_file, 'rb')
         content = fd.read()
         fd.close()
         
         if content == '':
            raise RuntimeError("PID file is empty: %s" % self.pid_file)
         
         content_lines = content.split(';')
         pid_from_file = int(content_lines[0])
         
         return pid_from_file
   
      return -1