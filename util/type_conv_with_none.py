#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import typing

NOT_INIT_INT=-999999

def conv_int(arg : str) -> int:

    if arg:
        return int(arg)
    else:
        return NOT_INIT_INT

# TODO: With Python 3.10 use for type hinting instead: -> int|None
def conv_int_none(arg : str) -> typing.Optional[int]:

    if arg:
        return int(arg)
    else:
        return None
