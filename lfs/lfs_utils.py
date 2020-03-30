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


import os
import re
import logging
import subprocess


class LFSUtils:

    def __init__(self, lfs_bin):

        self.lfs_bin = lfs_bin
        self.ost_prefix_len = len('OST')
        self.ost_active_output = ' active.'

        if not os.path.isfile(self.lfs_bin):
            raise RuntimeError("LFS binary was not found under: '%s'" % self.lfs_bin)

    def _check_osts(self, lfs_target):

        try:

            regex_str = lfs_target + "\-(OST[a-z0-9]+)\-[a-z0-9-]+\s(.+)"
            pattern = re.compile(regex_str)

            args = ['sudo', self.lfs_bin, 'check', 'osts']

            # TODO: Python3.5
            # process_result = subprocess.run(args,
            #                                 check=True,
            #                                 stdout=subprocess.PIPE,
            #                                 stderr=subprocess.PIPE)

            output = subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8')

            for line in output:

                match = pattern.match(line.strip())

                if match:

                    ost = match.group(1)
                    state = match.group(2)

                    ost_info = lfs_target + "-" + ost + "-" + state

                    if state == "active.":
                        logging.debug("Found active OST: %s" % ost_info)
                    else:
                        logging.debug("Found non-active OST: %s" % ost_info)

                else:
                    logging.debug("No regex match for line: %s" % line)

        except subprocess.CalledProcessError as error:
            pass

    def create_ost_list(self, lfs_target):
        pass

    def is_ost_available(self, ost_name, lfs_target):

        complete_target = lfs_target + "-" + ost_name

        try:

            args = list()
            args.append('sudo')
            args.append(self.lfs_bin)
            args.append('check')
            args.append('osts')

            #TODO Use subprocess.run() with Python3.5
            output = subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8')

            for line in output.split('\n'):

                if complete_target in line:

                    if self.ost_active_output == line[-len(self.ost_active_output):]:

                        logging.debug("Found active OST: '%s'" % complete_target)
                        return True

                    else:

                        logging.debug("Found inactive or unavailable OST: '%s'" % complete_target)
                        return False

        except subprocess.CalledProcessError as e:

            # !!! CAUTION !!!
            #
            # Check return code that should return False, when Lustre OST was not available.
            # Validate against Lustre error codes: lustre/include/lustre_errno.h

            logging.error("Return Code: %s -\nOutput: %s" % (e.returncode, e.output))

            # Cannot send after transport endpoint shutdown (108)
            if e.returncode == 108:
                return False

            raise RuntimeError(e.output)

    def set_stripe(self, ost_name, file_path):
        """Throws subprocess.CalledProcessError on error in subprocess.check_output"""

        stripe_index = "0x" + ost_name[self.ost_prefix_len:]

        logging.debug("Setting stripe settings for file: %s on OST: %s" % (file_path, ost_name))

        args = [self.lfs_bin, 'setstripe', '--stripe-index', stripe_index,
                '--stripe-count', '1', '--stripe-size', '0', file_path]

        # TODO Use subprocess.run() with Python3.5
        subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8')
