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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


from enum import Enum
from datetime import datetime

import logging
import os
import re
import socket
import subprocess
import yaml


VERSION='0.0.2'


# TODO: Comment code...

class LfsUtilsError(Exception):
    """Exception class LfsUtils specific errors."""

class LfsOstItem:

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
            raise LfsUtilsError(f"OST word not found in argument: {ost}")

        self._ost_idx = int(ost[3:], 16)

class StripeField(str, Enum):

    LMM_STRIPE_COUNT = 'lmm_stripe_count'
    LMM_STRIPE_OFFSET = 'lmm_stripe_offset'

class StripeInfo:

    def __init__(self, filename, count, index):

        self.filename = filename
        self.count = count
        self.index = index

class MigrateState(str, Enum):

    DISPLACED = 'DISPLACED'
    IGNORED   = 'IGNORED'
    SKIPPED   = 'SKIPPED'
    SUCCESS   = 'SUCCESS'
    FAILED    = 'FAILED'

class MigrateResult:
    '''
    Format per result:
    * DISPLACED|filename|time_elapsed|source_index|target_index
      - if file was migrated successfully, but ost target index is different
    * FAILED|filename|time_elapsed|error_code|error_message|source_index|target_index
      - if migration process for file failed
    * IGNORED|filename
      - if file has stripe index not equal source index
      - if file has stripe index equal target index
    * SKIPPED|filename
      - if skip option enabled and file stripe count > 1
    * SUCCESS|filename|time_elapsed|source_index|target_index
      - if migration of file was successful
    '''

    _result = ''

    @classmethod
    def __conv_none__(cls, arg) -> str:

        if arg is None:
            return ''

        return arg

    def __init__(self, state, filename, time_elapsed=None, source_idx=None, target_idx=None, error_code=None, error_msg=''):

        if MigrateState.DISPLACED == state:

            if not time_elapsed:
                raise LfsUtilsError(f"State {MigrateState.DISPLACED} requires time_elapsed to be set.")

            source_index = __class__.__conv_none__(source_idx)
            target_index = __class__.__conv_none__(target_idx)

            self._result = f"{MigrateState.DISPLACED}|{filename}|{time_elapsed}|{source_index}|{target_index}"

        elif MigrateState.FAILED == state:

            if not time_elapsed:
                raise LfsUtilsError(f"State {MigrateState.FAILED} requires time_elapsed to be set.")
            if not error_code:
                raise LfsUtilsError(f"State {MigrateState.FAILED} requires error_code to be set.")
            if not error_msg:
                raise LfsUtilsError(f"State {MigrateState.FAILED} requires error_msg to be set.")

            source_index = __class__.__conv_none__(source_idx)
            target_index = __class__.__conv_none__(target_idx)

            self._result = f"{MigrateState.FAILED}|{filename}|{time_elapsed}|{error_code}|{error_msg}|{source_index}|{target_index}"

        elif MigrateState.IGNORED == state:
            self._result = f"{MigrateState.IGNORED}|{filename}"

        elif MigrateState.SKIPPED == state:
            self._result = f"{MigrateState.SKIPPED}|{filename}"

        elif state == MigrateState.SUCCESS:

            if not time_elapsed:
                raise LfsUtilsError(f"State {MigrateState.SUCCESS} requires time_elapsed to be set.")

            source_index = __class__.__conv_none__(source_idx)
            target_index = __class__.__conv_none__(target_idx)

            self._result = f"{MigrateState.SUCCESS}|{filename}|{time_elapsed}|{source_index}|{target_index}"

    def __str__(self) -> str:
        return self._result

class LfsUtils:

    _REGEX_STR_OST_STATE = r"\-(OST[a-z0-9]+)\-[a-z0-9-]+\s(.+)"
    _REGEX_STR_OST_FILL_LEVEL = r"(\d{1,3})%.*\[OST:([0-9]{1,4})\]"
    _REGEX_STR_OST_CONN_UUID = r"ost_conn_uuid=([\d\.]+)@"

    _REGEX_PATTERN_OST_FILL_LEVEL = re.compile(_REGEX_STR_OST_FILL_LEVEL)
    _REGEX_PATTERN_OST_CONN_UUID = re.compile(_REGEX_STR_OST_CONN_UUID)

    MIN_OST_INDEX = 0
    MAX_OST_INDEX = 65535

    def __init__(self, lfs='/usr/bin/lfs', lctl='/usr/sbin/lctl'):

        self.lfs = lfs
        self.lctl = lctl

    # TODO: Return dict for multiple targets with proper OST items.
    def create_ost_item_list(self, target) -> list:

        try:
            args = ['sudo', self.lfs, 'check', 'osts']
            result = subprocess.run(args, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            # pylint: disable=W0707
            raise LfsUtilsError(err.stderr.decode('UTF-8'))

        ost_list = []

        regex_str = target + LfsUtils._REGEX_STR_OST_STATE
        logging.debug("Using regex for `lfs check osts`: %s", regex_str)
        pattern = re.compile(regex_str)

        for line in result.stdout.decode('UTF-8').strip().split('\n'):

            match = pattern.match(line.strip())

            if match:

                ost = match.group(1)
                state = match.group(2)

                if state == 'active.':
                    ost_list.append(LfsOstItem(target, ost, state, True))
                else:
                    ost_list.append(LfsOstItem(target, ost, state, False))

            else:
                logging.warning("No regex match for line: %s", line)

        return ost_list

    # TODO: Return boolean
    def is_ost_idx_active(self, target, ost_idx):

        for ost_item in self.create_ost_item_list(target):

            if ost_item.ost_idx == ost_idx:
                return ost_item.active

        raise LfsUtilsError(f"Index {ost_idx} not found on target {target}")

    def set_stripe(self, ost_idx, file_path):

        if ost_idx is None:
            raise LfsUtilsError('Argument ost_idx is not set.')

        if file_path is None or not file_path:
            raise LfsUtilsError('Argument file_path is not set.')

        if not isinstance(ost_idx, int):
            raise LfsUtilsError('Argument ost_idx must be type int.')

        if not isinstance(file_path, str):
            raise LfsUtilsError('Argument file_path must be type str.')

        logging.debug("Setting stripe for file: %s - OST: %i", file_path, ost_idx)

        try:
            args = [self.lfs, 'setstripe', '-i', str(ost_idx), file_path]
            subprocess.run(args, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            # pylint: disable=W0707
            raise LfsUtilsError(err.stderr.decode('UTF-8'))

    def stripe_info(self, filename) -> StripeInfo:
        """
        Raises
        ------
        LfsUtilsError
            * If a field is not found in retrieved stripe info for given file.
            * If execution of 'lfs getstripe' returns an error.

        subprocess.CalledProcessError on lfs getstripe.

        Returns
        -------
        A StripeInfo object.
        """

        args = [self.lfs, 'getstripe', '-c', '-i', '-y', filename]

        result = subprocess.run(args, check=True, capture_output=True)

        # TODO: Write a test that checks on dict type and content...
        fields = yaml.safe_load(result.stdout)

        lmm_stripe_count = 0
        if StripeField.LMM_STRIPE_COUNT in fields:
            lmm_stripe_count = fields[StripeField.LMM_STRIPE_COUNT]
        else:
            raise LfsUtilsError(f"Field {StripeField.LMM_STRIPE_COUNT} not found in stripe info: {result.stdout}")

        lmm_stripe_offset = 0
        if StripeField.LMM_STRIPE_OFFSET in fields:
            lmm_stripe_offset = fields[StripeField.LMM_STRIPE_OFFSET]
        else:
            raise LfsUtilsError(f"Field {StripeField.LMM_STRIPE_OFFSET} not found in stripe info: {result.stdout}")

        return StripeInfo(filename, lmm_stripe_count, lmm_stripe_offset)

    def migrate_file(self, filename, source_idx=None, target_idx=None, block=False, skip=True) -> MigrateResult:

        pre_ost_idx = None
        post_ost_idx = None

        start_time = datetime.now()

        try:

            pre_stripe_info = self.stripe_info(filename)

            pre_ost_idx = pre_stripe_info.index

            if skip and pre_stripe_info.count > 1:
                return MigrateResult(MigrateState.SKIPPED, filename)
            if source_idx is not None and pre_ost_idx != source_idx:
                return MigrateResult(MigrateState.IGNORED, filename)
            if target_idx is not None and pre_ost_idx == target_idx:
                return MigrateResult(MigrateState.IGNORED, filename)

            args = [self.lfs, 'migrate']

            if block:
                args.append('--block')
            else:
                args.append('--non-block')

            # TODO: Check OST min and max index
            if target_idx is not None and target_idx >= 0:
                args.append('-i')
                args.append(str(target_idx))

            if pre_stripe_info.count > 0:
                args.append('-c')
                args.append(str(pre_stripe_info.count))

            args.append(filename)

            subprocess.run(args, check=True, capture_output=True)
            time_elapsed = datetime.now() - start_time

            post_ost_idx = self.stripe_info(filename).index

            if target_idx is not None and target_idx != post_ost_idx:
                return MigrateResult(MigrateState.DISPLACED, filename, time_elapsed, pre_ost_idx, post_ost_idx)

            return MigrateResult(MigrateState.SUCCESS, filename, time_elapsed, pre_ost_idx, post_ost_idx)

        except subprocess.CalledProcessError as err:

            time_elapsed = datetime.now() - start_time

            stderr = ''

            if err.stderr:
                stderr = err.stderr.decode('UTF-8')

            return MigrateResult(MigrateState.FAILED, filename, time_elapsed, pre_ost_idx, post_ost_idx, err.returncode, stderr)

        except LfsUtilsError as err:

            time_elapsed = datetime.now() - start_time

            return MigrateResult(MigrateState.FAILED, filename, time_elapsed, pre_ost_idx, post_ost_idx, -1, stderr)

    def retrieve_ost_fill_level(self, fs_path) -> dict:

        ost_fill_level_dict = {}

        if not fs_path:
            raise LfsUtilsError('Lustre file system path is not set!')

        try:

            args = ['sudo', self.lfs, 'df', fs_path]

            result = subprocess.run(args, check=True, capture_output=True)

            for line in result.stdout.decode('UTF-8').strip().split('\n'):

                match = LfsUtils._REGEX_PATTERN_OST_FILL_LEVEL.search(line.strip())

                if match:

                    fill_level = int(match.group(1))
                    ost_idx = match.group(2)

                    ost_fill_level_dict[ost_idx] = fill_level

            if not ost_fill_level_dict:
                raise LfsUtilsError('Lustre OST fill levels are empty!')

        except subprocess.CalledProcessError as err:
            # pylint: disable=W0707
            raise LfsUtilsError(err.stderr.decode('UTF-8'))

        return ost_fill_level_dict

    # TODO: Implement lookup in cache
    def lookup_ost_to_oss(self, fs_name, ost, caching=True) -> str:

        hostname = ''

        if ost < LfsUtils.MIN_OST_INDEX or ost > LfsUtils.MAX_OST_INDEX:
            raise LfsUtilsError(f"OST index {ost} invalid. Must be in range between {LfsUtils.MIN_OST_INDEX} and {LfsUtils.MAX_OST_INDEX}.")

        ost_hex = hex(ost).split('x')[-1].zfill(4)

        param_value = f"osc.{fs_name}-OST{ost_hex}*.ost_conn_uuid"

        args = [self.lctl, 'get_param', param_value]

        result = subprocess.run(args, check=True, capture_output=True)

        match = LfsUtils._REGEX_PATTERN_OST_CONN_UUID.search(result.stdout.decode('UTF-8'))

        if not match:
            raise LfsUtilsError(f"No match for ost_conn_uuid for OST {ost} on file system {fs_name}")

        ip_addr = match.group(1)

        host_info = socket.gethostbyaddr(ip_addr)

        if not host_info:
            raise LfsUtilsError(f"No host information retrieved from socket.gethostbyaddr() for IP addr {ip_addr}")

        if len(host_info) != 3:
            raise LfsUtilsError(f"Broken interface for value {host_info} on socket.gethostbyaddr()")

        hostname = host_info[0]

        if not hostname:
            raise LfsUtilsError(f"No hostname found for OST {ost} on file system {fs_name}")

        return hostname

    def retrieve_ost_to_oss_map(self, fs_name, caching=True) -> dict:
        pass

    def is_ost_writable(self, ost, file_path) -> bool:

        if file_path is None:
            raise LfsUtilsError('File path must be set.')

        if ost is None:
            raise LfsUtilsError('OST index must be set.')

        if ost < LfsUtils.MIN_OST_INDEX or ost > LfsUtils.MAX_OST_INDEX:
            raise LfsUtilsError(f"OST index {ost} invalid. Must be in range between {LfsUtils.MIN_OST_INDEX} and {LfsUtils.MAX_OST_INDEX}.")

        if os.path.exists(file_path):
            raise LfsUtilsError(f"File already exists: {file_path}")

        try:

            self.set_stripe(ost, file_path)

            stripe_info = self.stripe_info(file_path)

            if stripe_info.index == ost:

                if os.path.exists(file_path):
                    os.remove(file_path)

                return True

        except Exception as err:
            logging.error(err)

        return False

    def create_dir_on_mdt(self, index, path):
        pass
