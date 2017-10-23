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
import logging
import subprocess


class LFSUtils:

    def __init__(self, lfs_bin):

        self.lfs_bin = lfs_bin
        self.ost_prefix_len = len('OST')
        self.ost_active_output = 'active.'

        if not os.path.isfile(self.lfs_bin):
            raise RuntimeError("LFS binary was not found under: '%s'" % self.lfs_bin)

    def is_ost_available(self, ost_name, lfs_target):
        """
            May rethrow subprocess.CalledProcessError as RuntimeError on error in subprocess.check_output
            if the return code of the caught CalledProcessError is not handled here.
        """

        complete_target = lfs_target + "-" + ost_name

        try:
            output = subprocess.check_output([self.lfs_bin, "check", "osts"], stderr=subprocess.STDOUT)

            for line in output.split('\n'):

                if complete_target in line:

                    if self.ost_active_output == line[-len(self.ost_active_output):]:

                        logging.debug("Found active: '%s'" % complete_target)
                        return True

                    else:

                        logging.debug("Found inactive: '%s'" % complete_target)
                        return False

        except subprocess.CalledProcessError as e:

            logging.error(e.output)

            # Cannot send after transport endpoint shutdown (108)
            if e.returncode == 108:
                return False

            raise RuntimeError(e.output)

    def set_stripe(self, ost_name, file_path):
        """Throws subprocess.CalledProcessError on error in subprocess.check_output"""

        stripe_index = "0x" + ost_name[self.ost_prefix_len:]

        logging.debug("Setting stripe for file: %s on OST: %s" % (file_path, ost_name))

        # Writes stderr to stdout to read the error message from subprocess.CalledProcessError.output on exception.
        subprocess.check_output([self.lfs_bin, "setstripe", "--stripe-index", stripe_index,
                                 "--stripe-count", "1", "--stripe-size", "0", file_path], stderr=subprocess.STDOUT)
