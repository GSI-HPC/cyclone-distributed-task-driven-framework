#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import distutils.util
import logging

from task.base_task import BaseTask
from lfsutils import LfsUtils

class LustreOstMigrateTask(BaseTask):

    def __init__(self, filename, source_ost, target_ost, direct_io, block, skip):

        super().__init__()

        # TODO: Rethink about object creation by the task factory with empty XML fields...
        # Initialization here for empty files is a bit unhandy.

        # Set later during runtime before task dispatch
        if filename:
            self.filename = filename
        else:
            self._filename = ''

        if source_ost:
            self.source_ost = source_ost
        else:
            self._source_ost = ''

        if target_ost:
            self.target_ost = target_ost
        else:
            self._target_ost = ''

        # Set on initialization based on the XML file
        self.direct_io = direct_io
        self.block = block
        self.skip = skip

        self._lfs_utils = LfsUtils()

    def execute(self):

        try:
            logging.info(self._lfs_utils.migrate_file(self.filename,
                                                      self.source_ost,
                                                      self.target_ost,
                                                      self.direct_io,
                                                      self.block,
                                                      self.skip))
        except Exception:
            logging.exception("Failed to migrate file: %s", self.filename)

    @property
    def direct_io(self) -> bool:
        return self._direct_io

    @direct_io.setter
    def direct_io(self, direct_io) -> None:

        if direct_io is None:
            raise RuntimeError('direct_io parameter must be a set.')

        if not isinstance(direct_io, str):
            raise TypeError('direct_io argument must be str type.')

        self._direct_io = bool(distutils.util.strtobool(direct_io))

    @property
    def block(self) -> bool:
        return self._block

    @block.setter
    def block(self, block) -> None:

        if block is None:
            raise RuntimeError('block parameter must be a set.')

        if not isinstance(block, str):
            raise TypeError('block argument must be str type.')

        self._block = bool(distutils.util.strtobool(block))

    @property
    def skip(self) -> bool:
        return self._skip

    @skip.setter
    def skip(self, skip) -> None:

        if skip is None:
            raise RuntimeError('skip parameter must be a set.')

        if not isinstance(skip, str):
            raise TypeError('skip argument must be str type.')

        self._skip = bool(distutils.util.strtobool(skip))

    @property
    def source_ost(self) -> int:
        return self._source_ost

    @source_ost.setter
    def source_ost(self, idx):
        self._source_ost = int(idx)

    @property
    def target_ost(self) -> int:
        return self._target_ost

    @target_ost.setter
    def target_ost(self, idx) -> None:
        self._target_ost = int(idx)

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, filename) -> None:

        if not filename:
            raise RuntimeError('filename not set.')

        if not isinstance(filename, str):
            raise RuntimeError('filename must be a string.')

        self._filename = filename
