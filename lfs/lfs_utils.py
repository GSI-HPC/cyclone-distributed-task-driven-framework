#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti <g.iannetti@gsi.de>
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
import commands


class LFSUtils:

    def __init__(self, lfs_bin):

        self.lfs_bin = lfs_bin
        self.ost_prefix_len = len('OST')
        self.ost_active_output = 'active.'

        if not os.path.isfile(self.lfs_bin):
            raise RuntimeError("LFS binary was not found under: %s" % self.lfs_bin)

    def is_ost_available(self, ost_name, lfs_target):

        cmd = self.lfs_bin + " check osts | grep " + lfs_target + "-" + ost_name

        (status, output) = commands.getstatusoutput(cmd)

        if not output:
            raise RuntimeError("'lfs check osts' returned an empty result!")

        if (status == 0) and (self.ost_active_output == output[-len(self.ost_active_output):]):
            return True

        else:

            if ost_name in output:
                return False

            if status > 0:
                raise RuntimeError("Error occurred during 'lfs check osts': %s" % output)

    def set_stripe(self, ost_name, file_path):

        ost_idx = ost_name[self.ost_prefix_len:]

        # logging.debug("Setting stripe for file: %s on OST: %s" % (file_path, ost_name))

        # No stripping is used.
        cmd = self.lfs_bin + " setstripe --stripe-index 0x" + ost_idx + " --stripe-count 1 --stripe-size 0 " + file_path

        # logging.debug("lfs setstripe: %s" %cmd)

        (status, output) = commands.getstatusoutput(cmd)

        if status > 0:
            raise RuntimeError("Failed to set stripe for file: %s\n%s" % (file_path, output))

        if not os.path.isfile(file_path):
            raise RuntimeError("Failed to create file via setstripe under: %s" % file_path)
