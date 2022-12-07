#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Gabriele Iannetti <g.iannetti@gsi.de>
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
#
# https://github.com/gabrieleiannetti/lfs-utils

from enum import Enum
from datetime import datetime, timedelta
from types import NoneType
from typing import Dict

import logging
import os
import re
import socket
import subprocess
import yaml

VERSION = '0.0.3'

def conv_obj(arg: int|str|None) -> str:
    """Support convertion from int, str and None objects to str.

    None objects are converted to empty string.
    """

    if isinstance(arg, NoneType):
        return ''
    if isinstance(arg, str):
        return arg
    if isinstance(arg, int):
        return str(arg)

    raise TypeError(f"Argument of type {type(arg)} not supported")

class LfsUtilsError(Exception):
    """Exception class LfsUtils specific errors."""

class LfsComponentType(str, Enum):

    MDT = 'MDT'
    OST = 'OST'

    def __str__(self) -> str:
        return self.value

class LfsComponentState:

    def __init__(self, target: str, name: str, type_: str, state: str, active: bool) -> None:

        self.target = target
        self.name   = name
        self.type   = type_
        self.state  = state
        self.active = active

        self._idx = int(name[3:], 16)

    @property
    def idx(self) -> int:
        return self._idx

class LfsComponentCollection:

    def __init__(self) -> None:

        self._mdts = dict[int, LfsComponentState]()
        self._osts = dict[int, LfsComponentState]()

    @property
    def mdts(self) -> Dict[int, LfsComponentState]:
        return self._mdts

    @property
    def osts(self) -> Dict[int, LfsComponentState]:
        return self._osts

class StripeField(str, Enum):

    LMM_STRIPE_COUNT = 'lmm_stripe_count'
    LMM_STRIPE_OFFSET = 'lmm_stripe_offset'

    def __str__(self) -> str:
        return self.value

class StripeInfo:

    def __init__(self, filename: str, count: int, index: int) -> None:

        self.filename = filename
        self.count    = count
        self.index    = index

class MigrateState(str, Enum):

    DISPLACED = 'DISPLACED'
    IGNORED   = 'IGNORED'
    SKIPPED   = 'SKIPPED'
    SUCCESS   = 'SUCCESS'
    FAILED    = 'FAILED'

    def __str__(self) -> str:
        return self.value

class MigrateResult:
    '''
    Format per result:
    * DISPLACED|filename|time_elapsed|source_index|target_index
      - if file was migrated successfully, but ost target index is different
    * FAILED|filename|time_elapsed|source_index|target_index|error_message
      - if migration process failed for file
    * IGNORED|filename
      - if file has stripe index not equal source index
      - if file has stripe index equal target index
    * SKIPPED|filename
      - if skip option enabled and file stripe count > 1
    * SUCCESS|filename|time_elapsed|source_index|target_index
      - if migration of file was successful
    '''

    def __init__(self,
                 state: MigrateState,
                 filename: str,
                 time_elapsed: timedelta,
                 source_idx: int|None = None,
                 target_idx: int|None = None,
                 error_msg: str = None):

        self._result: str

        if not filename or not isinstance(filename, str):
            raise LfsUtilsError('Filename must be set and type of str')

        if not isinstance(time_elapsed, timedelta):
            raise LfsUtilsError('Time elapsed must be type of datetime.timedelta')

        if MigrateState.DISPLACED == state:
            self._result = f"{MigrateState.DISPLACED}|{filename}|{time_elapsed}|{conv_obj(source_idx)}|{conv_obj(target_idx)}"

        elif MigrateState.FAILED == state:

            if not error_msg:
                raise LfsUtilsError(f"State {MigrateState.FAILED} requires error_msg to be set.")

            self._result = f"{MigrateState.FAILED}|{filename}|{time_elapsed}|{conv_obj(source_idx)}|{conv_obj(target_idx)}|{error_msg}"

        elif MigrateState.IGNORED == state:
            self._result = f"{MigrateState.IGNORED}|{filename}"

        elif MigrateState.SKIPPED == state:
            self._result = f"{MigrateState.SKIPPED}|{filename}"

        elif state == MigrateState.SUCCESS:
            self._result = f"{MigrateState.SUCCESS}|{filename}|{time_elapsed}|{conv_obj(source_idx)}|{conv_obj(target_idx)}"

        else:
            raise LfsUtilsError(f"Invalid state {state}")

    def __str__(self) -> str:
        return self._result

class LfsUtils:

    _REGEX_STR_COMP_STATE = r"(.+)\-((OST|MDT){1}[a-z0-9]+)\-[a-z0-9-]+\s(.+)\."
    _REGEX_STR_OST_FILL_LEVEL = r"(\d{1,3})%.*\[OST:([0-9]{1,4})\]"
    _REGEX_STR_OST_CONN_UUID = r"ost_conn_uuid=([\d\.]+)@"

    _REGEX_PATTERN_OST_FILL_LEVEL = re.compile(_REGEX_STR_OST_FILL_LEVEL)
    _REGEX_PATTERN_OST_CONN_UUID = re.compile(_REGEX_STR_OST_CONN_UUID)

    MIN_OST_INDEX = 0
    MAX_OST_INDEX = 65535

    def __init__(self, lfs: str = '/usr/bin/lfs', lctl: str ='/usr/sbin/lctl'):

        self.lfs = lfs
        self.lctl = lctl

    def retrieve_component_states(self, file: str = None) -> Dict[str, LfsComponentCollection]:

        comp_states = dict[str, LfsComponentCollection]()

        if file:
            with open(file, 'r', encoding='UTF-8') as file_handle:
                output = file_handle.read()
        else:
            args = ['sudo', self.lfs, 'check', 'osts']
            output = subprocess.run(args, check=True, capture_output=True).stdout.decode('UTF-8')

        logging.debug("Using regex for `lfs check osts`: %s", LfsUtils._REGEX_STR_COMP_STATE)
        pattern = re.compile(LfsUtils._REGEX_STR_COMP_STATE)

        for line in output.split('\n'):

            stripped_line = line.strip()

            if not stripped_line:
                continue

            match = pattern.match(stripped_line)

            if match:

                target    = match.group(1)
                comp_name = match.group(2)
                comp_type = match.group(3)
                state     = match.group(4)

                if target not in comp_states:
                    comp_states[target] = LfsComponentCollection()

                if comp_type == LfsComponentType.OST:
                    handle_comp_state_col_item = comp_states[target].osts
                elif comp_type == LfsComponentType.MDT:
                    handle_comp_state_col_item = comp_states[target].mdts
                else:
                    raise RuntimeError(f"Unknown component type found: {comp_type}")

                active = ('active' == state)

                comp_state_item = LfsComponentState(target, comp_name, comp_type, state, active)
                handle_comp_state_col_item[comp_state_item.idx] = comp_state_item

            else:
                logging.warning("No regex match for line: %s", line)

        return comp_states

    def is_ost_idx_active(self, target: str, idx: int, file=None) -> bool:
        return self.retrieve_component_states(file)[target].osts[idx].active

    def set_ost_file_stripe(self, file_path: str, idx: int) -> None:

        if not file_path or not isinstance(file_path, str):
            raise LfsUtilsError('File path must be set and type of str')

        if idx is None or not isinstance(idx, int):
            raise LfsUtilsError('Index must be set and type of int')

        logging.debug("Setting stripe for file: %s - OST: %i", file_path, idx)

        args = [self.lfs, 'setstripe', '-i', str(idx), file_path]
        subprocess.run(args, check=True, capture_output=True)

    def stripe_info(self, filename: str, file: str = None) -> StripeInfo:
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

        if file:
            with open(file, 'r', encoding='UTF-8') as file_handle:
                output = file_handle.read()
        else:
            args = [self.lfs, 'getstripe', '-c', '-i', '-y', filename]
            output = subprocess.run(args, check=True, capture_output=True).stdout.decode('UTF-8')

        fields = yaml.safe_load(output)

        if StripeField.LMM_STRIPE_COUNT in fields:
            lmm_stripe_count = fields[StripeField.LMM_STRIPE_COUNT]
        else:
            raise LfsUtilsError(f"Field {StripeField.LMM_STRIPE_COUNT} not found in stripe info: {output}")

        if StripeField.LMM_STRIPE_OFFSET in fields:
            lmm_stripe_offset = fields[StripeField.LMM_STRIPE_OFFSET]
        else:
            raise LfsUtilsError(f"Field {StripeField.LMM_STRIPE_OFFSET} not found in stripe info: {output}")

        return StripeInfo(filename, lmm_stripe_count, lmm_stripe_offset)

    def migrate_file(self,
                     filename: str,
                     source_idx: int|None = None,
                     target_idx: int|None = None,
                     block: bool = False,
                     skip: bool = True) -> MigrateResult:

        state        = None
        pre_ost_idx  = None
        post_ost_idx = None
        error_msg    = None

        start_time = datetime.now()

        try:

            if source_idx and not isinstance(source_idx, int):
                raise TypeError('If source_idx ist set, it must be type of int')

            if target_idx and not isinstance(target_idx, int):
                raise TypeError('If target_idx ist set, it must be type of int')

            pre_stripe_info = self.stripe_info(filename)

            pre_ost_idx = pre_stripe_info.index

            if skip and pre_stripe_info.count > 1:
                state = MigrateState.SKIPPED
            elif source_idx != pre_ost_idx:
                state = MigrateState.IGNORED
            elif target_idx == pre_ost_idx:
                state = MigrateState.IGNORED

            else:

                args = [self.lfs, 'migrate']

                if block:
                    args.append('--block')
                else:
                    args.append('--non-block')

                if target_idx:

                    if target_idx < LfsUtils.MIN_OST_INDEX:
                        raise ValueError(f"target_idx is less than LfsUtils.MIN_OST_INDEX ({LfsUtils.MIN_OST_INDEX})")

                    if source_idx > LfsUtils.MAX_OST_INDEX:
                        raise ValueError(f"target_idx is greater than LfsUtils.MAX_OST_INDEX ({LfsUtils.MAX_OST_INDEX})")

                    args.append('-i')
                    args.append(str(target_idx))

                if pre_stripe_info.count > 0:
                    args.append('-c')
                    args.append(str(pre_stripe_info.count))

                args.append(filename)

                # Save target OST index in case of migration failure.
                post_ost_idx = target_idx

                subprocess.run(args, check=True, capture_output=True)

                post_ost_idx = self.stripe_info(filename).index

                if target_idx != post_ost_idx:
                    state = MigrateState.DISPLACED
                else:
                    state = MigrateState.SUCCESS

        except subprocess.CalledProcessError as err:

            if err.stderr:
                error_msg = err.stderr.decode('UTF-8')

            state = MigrateState.FAILED

        except LfsUtilsError as err:
            error_msg = str(err)
            state = MigrateState.FAILED

        time_elapsed = datetime.now() - start_time

        return MigrateResult(state, filename, time_elapsed, pre_ost_idx, post_ost_idx, error_msg)

    def retrieve_ost_disk_usage(self, fs_path: str, file: str = None) -> Dict[int, int]:

        ost_fill_level_dict = {}

        if not fs_path:
            raise LfsUtilsError('Lustre file system path is not set')

        if file:
            with open(file, 'r', encoding='UTF-8') as file_handle:
                output = file_handle.read()
        else:
            args = ['sudo', self.lfs, 'df', fs_path]
            output = subprocess.run(args, check=True, capture_output=True).stdout.decode('UTF-8')

        for line in output.split('\n'):

            stripped_line = line.strip()

            if not stripped_line:
                continue

            match = LfsUtils._REGEX_PATTERN_OST_FILL_LEVEL.search(stripped_line)

            if match:

                fill_level = int(match.group(1))
                ost_idx    = int(match.group(2))

                ost_fill_level_dict[ost_idx] = fill_level

        if not ost_fill_level_dict:
            raise LfsUtilsError('Lustre OST fill levels are empty')

        return ost_fill_level_dict

    # TODO: Implement lookup in cache
    def lookup_ost_to_oss(self, fs_name: str, ost: int, caching: bool = True) -> str:

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

    def retrieve_ost_to_oss_map(self, fs_name: str, caching: bool = True) -> dict:
        pass

    def is_ost_writable(self, ost: int, file_path: str) -> bool:

        if file_path is None:
            raise LfsUtilsError('File path must be set.')

        if ost is None:
            raise LfsUtilsError('OST index must be set.')

        if ost < LfsUtils.MIN_OST_INDEX or ost > LfsUtils.MAX_OST_INDEX:
            raise LfsUtilsError(f"OST index {ost} invalid. Must be in range between {LfsUtils.MIN_OST_INDEX} and {LfsUtils.MAX_OST_INDEX}.")

        if os.path.exists(file_path):
            raise LfsUtilsError(f"File already exists: {file_path}")

        try:

            self.set_ost_file_stripe(file_path, ost)

            stripe_info = self.stripe_info(file_path)

            if stripe_info.index == ost:

                if os.path.exists(file_path):
                    os.remove(file_path)

                return True

        except Exception:
            logging.exception('Exception occured during OST writable test')

        return False

    def create_dir_on_mdt(self, index: int, path: str) -> None:
        pass
