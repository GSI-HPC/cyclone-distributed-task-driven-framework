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
import sys
import logging
import subprocess

from datetime import datetime


class LFSOstItem:

    def __init__(self, target, ost, state, active):

        self.target = target
        self.ost = ost
        self.state = state
        self.active = active
        self.ost_idx = ost

    @property
    def ost_idx(self):
        return self._ost_idx

    @ost_idx.setter
    def ost_idx(self, ost):

        if ost[0:3] != "OST":
            raise RuntimeError("OST word not found in argument: %s" % ost)

        # Cut and convert to hex but keep the decimal index as str!
        self._ost_idx = str(int(ost[3:], 16))


# TODO: Make Singleton...?
class LFSUtils:

    def __init__(self, lfs_bin):

        self.lfs_bin = lfs_bin

        if not os.path.isfile(self.lfs_bin):
            raise RuntimeError("LFS binary was not found under: '%s'" % self.lfs_bin)

    def create_ost_item_list(self, target):

        ost_list = list()

        try:

            regex_str = target + "\-(OST[a-z0-9]+)\-[a-z0-9-]+\s(.+)"
            logging.debug("Using regex for `lfs check osts`: %s" % regex_str)
            pattern = re.compile(regex_str)

            args = ['sudo', self.lfs_bin, 'check', 'osts']

            # TODO: Python3.5
            # process_result = subprocess.run(args,
            #                                 check=True,
            #                                 stdout=subprocess.PIPE,
            #                                 stderr=subprocess.PIPE)

            output = subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8')

            for line in output.strip().split('\n'):

                match = pattern.match(line.strip())

                if match:

                    ost = match.group(1)
                    state = match.group(2)

                    if state == "active.":
                        ost_list.append(LFSOstItem(target, ost, state, True))
                    else:
                        ost_list.append(LFSOstItem(target, ost, state, False))

                else:
                    logging.warning("No regex match for line: %s" % line)

        except Exception as e:
            logging.error("Exception occurred: %s" % e)

        return ost_list

    def is_ost_idx_active(self, target, ost_idx):

        for ost_item in self.create_ost_item_list(target):

            if ost_item.ost_idx == ost_idx:

                if ost_item.active:
                    return True
                else:
                    return False

        raise RuntimeError("[LFSUtils::is_ost_idx_active] Index not found: %s"
                           % ost_idx)

    def set_stripe(self, ost_idx, file_path):
        """Throws subprocess.CalledProcessError on error in subprocess.check_output"""

        logging.debug("Setting stripe for file: %s - OST: %s"
                      % (file_path, ost_idx))

        args = [self.lfs_bin, 'setstripe', '-i', ost_idx, file_path]

        # TODO Use subprocess.run() with Python3.5
        subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8')

    def is_file_stripped(self, filename):
        """
        Raises
        ------
        subprocess.CalledProcessError
            If execution of 'lfs getstripe' returns an error.
        """

        args = [self.lfs_bin, 'getstripe', '-c', filename]

        process_result = subprocess.run(args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        check=True)

        stripe_count = int(process_result.stdout)

        if stripe_count == 1:
            return False
        elif stripe_count > 1:
            return True
        else:
            func_name = sys._getframe().f_code.co_name
            raise RuntimeError("[%s] Undefined stripe count returned for '%s': %i"
                               % (func_name, filename, stripe_count))

    def migrate_file(self, filename, idx=None, block=False, skip=True):
        """
        Processor function to process a file.

        Prints the following messages on STDOUT:
            * SKIPPED|{filename}
                - if skip option enabled and file stripe count > 1
            * SUCCESS|{filename}|{time_time_elapsed}
                - if migration of file was successful
            * FAILED|{filename}|{return_code}|{error_message}
                - if migration of file failed e.g. 'lfs' failed
        """

        try:

            if not filename:
                raise RuntimeError('Empty filename!')

            if skip and self.is_file_stripped(filename):
                logging.info("SKIPPED|%s" % filename)
            else:

                args = [self.lfs_bin, 'migrate']

                if block:
                    args.append('--block')
                else:
                    args.append('--non-block')

                if idx:
                    args.append('-o')
                    args.append(idx)

                args.append(filename)

                start_time = datetime.now()
                subprocess.run(args, check=True, stderr=subprocess.PIPE)
                time_elapsed = datetime.now() - start_time

                logging.info("SUCCESS|%s|%s" % (filename, time_elapsed))

        except subprocess.CalledProcessError as error:

            rc = error.returncode
            stderr = ''

            if error.stderr:
                stderr = error.stderr.decode('UTF-8')

            logging.info("FAILED|%s|%i|%s" % (filename, rc, stderr))
