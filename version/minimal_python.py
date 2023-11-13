#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from enum import Enum

import sys

class MinimalPython(int, Enum):

    # See: https://docs.python.org/3/c-api/apiabiversion.html#apiabiversion
    MAJOR = 3
    MINOR = 9
    MICRO = 12
    FINAL_RELEASE_LEVEL = 240 # 0xF0

    def check(major=MAJOR, minor=MINOR, micro=MICRO, final=FINAL_RELEASE_LEVEL):

        build_hexversion = '0x' \
                            + format(major, '02x') \
                            + format(minor, '02x') \
                            + format(micro, '02x') \
                            + format(final, '02x')

        hexversion = int(build_hexversion, 16)

        if sys.hexversion < hexversion:

            found_version = f"{sys.version_info.major}." \
                            f"{sys.version_info.minor}." \
                            f"{sys.version_info.micro}-" \
                            f"{sys.version_info.releaselevel}"

            error = f"Not supported Python version found: {found_version}" \
                    f" - Minimal version required: {MinimalPython._version(major, minor, micro)}"

            raise RuntimeError(error)

    def _version(major, minor, micro) -> str:
        return f"{major}.{minor}.{micro}-final"
