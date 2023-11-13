#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from xml.etree import ElementTree
from collections import OrderedDict

import os

class TaskXmlReaderError(Exception):

    def __init__(self, message):
        super().__init__(f"[XML]: {message}")

class TaskXmlInfo:

    def __init__(self, class_module, class_name, class_properties):

        #TODO: Check required and optional!
        self.class_module = class_module
        self.class_name = class_name
        self.class_properties = class_properties

class TaskXmlReader:

    def __init__(self):
        pass

    @staticmethod
    def read_task_definition(file_path, task_name):

        if not os.path.isfile(file_path):
            raise IOError(f"The XML task definition file does not exist or is not a file: {file_path}")

        try:

            class_module = None
            class_name = None
            class_properties = OrderedDict()

            tree = ElementTree.parse(file_path)
            root = tree.getroot()

            found_task = False

            if root.tag != 'tasks':
                raise RuntimeError(f"Wrong root tag detected: '{root.tag}'")

            if not root:
                raise RuntimeError(f"No task definitions found in '{file_path}'")

            for child in root:

                if child.tag != 'task':
                    raise RuntimeError(f"Wrong child tag detected: '{child.tag}'")

                if child.attrib['name'] == task_name:

                    if found_task:
                        raise RuntimeError(f"Found duplicate task name definition for: '{task_name}'")
                    else:
                        found_task = True

                    class_def = child.find('class')

                    if class_def is None:
                        raise RuntimeError("No class definition found!")

                    class_module = class_def.get('module')

                    if class_module is None:
                        raise RuntimeError("No module definition for class found!")

                    if not ("task." in class_module):
                        raise RuntimeError("A task has to be located into the 'task' package!")

                    class_name = class_def.get('name')

                    if class_name is None:
                        raise RuntimeError("No name definition for class found!")

                    property_def = child.find('property')

                    if property_def is not None:

                        for property_item in property_def:

                            if not property_item.text:
                                property_item.text = str("")

                            class_properties[property_item.tag] = property_item.text

            if not found_task:
                raise RuntimeError(f"No task definition found for: '{task_name}'")

            return TaskXmlInfo(class_module, class_name, class_properties)

        except Exception as err:
            raise TaskXmlReaderError(f"{err}")
