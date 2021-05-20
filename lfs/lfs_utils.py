#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
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
import yaml
import logging
import subprocess

from datetime import datetime
from enum import Enum


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

        if ost[0:3] != 'OST':
            raise RuntimeError(f"OST word not found in argument: {ost}")

        # Cut and convert to hex but keep the decimal index as str!
        self._ost_idx = str(int(ost[3:], 16))

class StripeField(str, Enum):

    LMM_STRIPE_COUNT = 'lmm_stripe_count'
    LMM_STRIPE_OFFSET = 'lmm_stripe_offset'

class StripeInfo:

    def __init__(self, count, index):
        self.count = count
        self.index = index

# TODO: Make Singleton...?
class LFSUtils:

    def __init__(self, lfs_bin):

        self.lfs_bin = lfs_bin

        if not os.path.isfile(self.lfs_bin):
            raise RuntimeError(f"LFS binary was not found under: '{self.lfs_bin}'")

    def create_ost_item_list(self, target):

        ost_list = list()

        try:

            regex_str = target + r"\-(OST[a-z0-9]+)\-[a-z0-9-]+\s(.+)"
            logging.debug("Using regex for `lfs check osts`: %s", regex_str)
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
                    logging.warning("No regex match for line: %s", line)

        except Exception as err:
            logging.error("Exception occurred: %s", err)

        return ost_list

    def is_ost_idx_active(self, target, ost_idx):

        for ost_item in self.create_ost_item_list(target):

            if ost_item.ost_idx == ost_idx:
                return ost_item.active

        raise RuntimeError(f"[LFSUtils::is_ost_idx_active] Index not found: {ost_idx}")

    def set_stripe(self, ost_idx, file_path):
        """Throws subprocess.CalledProcessError on error in subprocess.check_output"""

        logging.debug("Setting stripe for file: %s - OST: %s", file_path, ost_idx)

        args = [self.lfs_bin, 'setstripe', '-i', ost_idx, file_path]

        # TODO Use subprocess.run() with Python3.5
        subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8')

    def stripe_info(self, filename) -> StripeInfo:
        """
        Raises
        ------
        subprocess.CalledProcessError
            If execution of 'lfs getstripe' returns an error.

        RuntimeError
            If a field is not found in retrieved stripe info for given file.

        Returns
        -------
        A StripeInfo object.
        """

        args = [self.lfs_bin, 'getstripe', '-c', '-i', '-y', filename]
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # TODO: Write a test that checks on dict type and content...
        fields = yaml.safe_load(result.stdout)

        lmm_stripe_count = 0
        if StripeField.LMM_STRIPE_COUNT in fields:
            lmm_stripe_count = fields[StripeField.LMM_STRIPE_COUNT]
        else:
            raise RuntimeError(f"Field {StripeField.LMM_STRIPE_COUNT} not found in stripe info: {result.stdout}")

        lmm_stripe_offset = 0
        if StripeField.LMM_STRIPE_OFFSET in fields:
            lmm_stripe_offset = fields[StripeField.LMM_STRIPE_OFFSET]
        else:
            raise RuntimeError(f"Field {StripeField.LMM_STRIPE_OFFSET} not found in stripe info: {result.stdout}")

        return StripeInfo(lmm_stripe_count, lmm_stripe_offset)

    def migrate_file(self, filename, source_idx=None, target_idx=-1, block=False, skip=True) -> None:
        """
        Processor function to process a file.

        Prints the following messages on STDOUT:
            * IGNORED|{filename}
                - if file has stripe index not equal source index
            * SKIPPED|{filename}
                - if skip option enabled and file stripe count > 1
            * SUCCESS|{filename}|{ost_source_index}|{ost_target_index}|{time_time_elapsed}
                - if migration of file was successful
            * FAILED|{filename}|{return_code}|{error_message}
                - if migration of file failed
        """

        if not isinstance(filename, str):
            raise RuntimeError('filename must be a str value.')
        if source_idx and not isinstance(source_idx, int):
            raise RuntimeError('source_idx must be an int value.')
        if not isinstance(target_idx, int):
            raise RuntimeError('target_idx must be an int value.')
        if block and not isinstance(block, bool):
            raise RuntimeError('block must be a bool value.')
        if skip and not isinstance(skip, bool):
            raise RuntimeError('skip must be a bool value.')

        if not filename:
            raise RuntimeError('Empty filename provided.')

        try:

            stripe_info = self.stripe_info(filename)

            if skip and stripe_info.count > 1:
                logging.info("SKIPPED|%s", filename)
            elif source_idx and stripe_info.index != source_idx:
                logging.info("IGNORED|%s", filename)
            else:

                args = [self.lfs_bin, 'migrate']

                if block:
                    args.append('--block')
                else:
                    args.append('--non-block')

                if target_idx > -1:
                    args.append('-i')
                    args.append(str(target_idx))

                args.append(filename)

                start_time = datetime.now()
                subprocess.run(args, check=True, stderr=subprocess.PIPE)
                elapsed_time = datetime.now() - start_time

                logging.info("SUCCESS|%s|%i|%i|%s", filename, stripe_info.index, target_idx, elapsed_time)

        except subprocess.CalledProcessError as err:

            stderr = ''

            if err.stderr:
                stderr = err.stderr.decode('UTF-8')

            logging.info("FAILED|%s|%s|%s", filename, err.returncode, stderr)

    def retrieve_ost_fill_level(self, fs_path):

        if not fs_path:
            raise RuntimeError("Lustre file system path is not set!")

        regex = r"(\d{1,3})%.*\[OST:([0-9]{1,4})\]"

        pattern = re.compile(regex)

        args = ['sudo', self.lfs_bin, 'df', fs_path]

        ost_fill_level_dict = dict()

        output = subprocess.check_output(args).decode('UTF-8')

        for line in output.strip().split('\n'):

            match = pattern.search(line.strip())

            if match:

                fill_level = int(match.group(1))
                ost_idx = match.group(2)

                ost_fill_level_dict[ost_idx] = fill_level

        if not ost_fill_level_dict:
            raise RuntimeError("Lustre OST fill levels are empty!")

        return ost_fill_level_dict
