#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

class ConfigValueError(Exception):

    def __init__(self, message):
        super().__init__(f"{message}")

class ConfigValueOutOfRangeError(Exception):

    def __init__(self, name, min_="", max_=""):
        super().__init__(f"Config value is out of range ({min_}-{max_}): {name}")
