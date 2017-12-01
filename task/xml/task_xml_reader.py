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


from xml.etree import ElementTree
from collections import OrderedDict

import os


class TaskXmlInfo:

    def __init__(self, class_module, class_name, class_properties):

        self.class_module = class_module
        self.class_name = class_name
        self.class_properties = class_properties


class TaskXmlReader:

    def __init__(self):
        pass

    # TODO: Surround function with try/catch construct and rethrow exception with XML-tag!
    @staticmethod
    def read_task_definition(file_path):

        if not os.path.isfile(file_path):
            raise IOError("The XML task definition file does not exist or is not a file: %s" % file_path)

        class_module = None
        class_name = None
        class_properties = OrderedDict()

        tree = ElementTree.parse(file_path)
        root = tree.getroot()

        if root.tag != 'tasks':
            raise RuntimeError("[XML] Wrong root tag detected: '%s'", root.tag)

        if len(root) != 1:
            raise RuntimeError("[XML] Just one task definition is supported currently!")

        for child in root:

            if child.tag != 'task':
                raise RuntimeError("[XML] Wrong child tag detected: '%s'", child.tag)

            class_def = child.find('class')

            if class_def is None:
                raise RuntimeError("[XML] No class definition found!")

            class_module = class_def.get('module')

            if class_module is None:
                raise RuntimeError("[XML] No module definition for class found!")

            class_name = class_def.get('name')

            if class_name is None:
                raise RuntimeError("[XML] No name definition for class found!")

            property_def = child.find('property')

            if property_def is None:
                raise RuntimeError("[XML] No property definition in class found!")

            for property_item in property_def:

                if not property_item.text:
                    property_item.text = str("")

                class_properties[property_item.tag] = property_item.text

        return TaskXmlInfo(class_module, class_name, class_properties)


